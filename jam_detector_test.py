"""Standalone test for Skele King Jam (rhythm game) orb detection.

Press P to start detection, O to stop.
Detects orbs at the hit zone and presses/holds the corresponding key (A/S/D/F/B).

Uses macOS ScreenCaptureKit for ~60fps streaming capture with zero-copy pixel access.
"""

import ctypes
import ctypes.util
import queue
import threading
import time
import warnings

import objc

warnings.filterwarnings("ignore", message="PyObjCPointer created")

objc.loadBundle(
    "ScreenCaptureKit",
    globals(),
    bundle_path="/System/Library/Frameworks/ScreenCaptureKit.framework",
)

from dispatch import dispatch_queue_create  # noqa: E402
from Foundation import NSDate, NSObject, NSRunLoop  # noqa: E402
from pynput import keyboard  # noqa: E402
from pynput.keyboard import Controller as KeyController  # noqa: E402
from Quartz import CGRectMake  # noqa: E402

# ---------------------------------------------------------------------------
# CoreMedia / CoreVideo C functions
# ---------------------------------------------------------------------------

_cm = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreMedia"))
_cv = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreVideo"))

_cm.CMSampleBufferGetImageBuffer.restype = ctypes.c_void_p
_cm.CMSampleBufferGetImageBuffer.argtypes = [ctypes.c_void_p]
_cv.CVPixelBufferLockBaseAddress.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
_cv.CVPixelBufferUnlockBaseAddress.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
_cv.CVPixelBufferGetBaseAddress.restype = ctypes.c_void_p
_cv.CVPixelBufferGetBaseAddress.argtypes = [ctypes.c_void_p]
_cv.CVPixelBufferGetBytesPerRow.restype = ctypes.c_size_t
_cv.CVPixelBufferGetBytesPerRow.argtypes = [ctypes.c_void_p]
_cv.CVPixelBufferGetWidth.restype = ctypes.c_size_t
_cv.CVPixelBufferGetWidth.argtypes = [ctypes.c_void_p]

# ---------------------------------------------------------------------------
# Register ObjC signatures
# ---------------------------------------------------------------------------

_blk2 = {"callable": {"retval": {"type": b"v"}, "arguments": {0: {"type": b"^v"}, 1: {"type": b"@"}, 2: {"type": b"@"}}}}
_blk1 = {"callable": {"retval": {"type": b"v"}, "arguments": {0: {"type": b"^v"}, 1: {"type": b"@"}}}}

objc.registerMetaDataForSelector(b"SCShareableContent",
    b"getShareableContentExcludingDesktopWindows:onScreenWindowsOnly:completionHandler:",
    {"arguments": {4: _blk2}})
objc.registerMetaDataForSelector(b"SCStream",
    b"startCaptureWithCompletionHandler:", {"arguments": {2: _blk1}})
objc.registerMetaDataForSelector(b"SCStream",
    b"stopCaptureWithCompletionHandler:", {"arguments": {2: _blk1}})
objc.registerMetaDataForSelector(b"NSObject",
    b"stream:didOutputSampleBuffer:ofType:",
    {"retval": {"type": b"v"}, "arguments": {
        2: {"type": b"@"}, 3: {"type": b"^{opaqueCMSampleBuffer=}"}, 4: {"type": b"q"}}})

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Use two separate trigger lines:
# - start line for note/tap timing
# - hold line higher up for sustain tracking, away from receptor effects
SOURCE_X = 490
SOURCE_Y = 546
SOURCE_WIDTH = 220
START_TRIGGER_OFFSET = 26
HOLD_TRIGGER_OFFSET = 52
F_START_TRIGGER_OFFSET = 40
CAPTURE_TOP_Y = SOURCE_Y - HOLD_TRIGGER_OFFSET
CAPTURE_HEIGHT = (HOLD_TRIGGER_OFFSET - START_TRIGGER_OFFSET) + 1
START_ROW_INDEX = HOLD_TRIGGER_OFFSET - START_TRIGGER_OFFSET
HOLD_ROW_INDEX = 0
F_START_ROW_INDEX = HOLD_TRIGGER_OFFSET - F_START_TRIGGER_OFFSET
F_START_ROW_WINDOW = (-1, 0, 1)
SOURCE_RECT = CGRectMake(SOURCE_X, CAPTURE_TOP_Y, SOURCE_WIDTH, CAPTURE_HEIGHT)
LANE_KEYS = ("a", "s", "d", "f", "b")
LANE_OFFSETS = (10, 60, 110, 160, 210)
LANE_CENTER_ADJUST = (0, 0, 0, -4, 0)
LANE_USE_HOLD_FALLBACK_FOR_START = (False, False, False, True, False)

SAT_THRESHOLD = 150
VAL_THRESHOLD = 180
HOLD_SAT_THRESHOLD = 130
HOLD_VAL_THRESHOLD = 90
MIN_MATCHING_PIXELS = 4
MIN_HOLD_MATCHING_PIXELS = 1
MIN_PRESS_GAP = 0.04
MIN_KEY_HOLD = 0.03
RELEASE_EMPTY_FRAMES = 6
REARM_CLEAR_FRAMES = 1
SAMPLE_RADIUS = 4
HOLD_SAMPLE_RADIUS = 7
LANE_START_MIN_PIXELS = (4, 4, 4, 8, 4)
LANE_HOLD_MIN_PIXELS = (1, 1, 1, 1, 1)
LANE_REARM_CLEAR_FRAMES = (1, 1, 1, 3, 1)
LANE_HOLD_SAT_THRESHOLDS = (130, 130, 130, 95, 130)
LANE_HOLD_VAL_THRESHOLDS = (90, 90, 90, 70, 90)
LANE_RELEASE_EMPTY_FRAMES = (6, 6, 6, 10, 6)
DEBUG_PIXEL_LOG_EVERY = 0
DEBUG_OCC_LOG_EVERY = 0
DEBUG_HIT_LOG = True
DEBUG_STATE_LOG = True
DEBUG_LANE_INDEX = 3  # F lane
DEBUG_LANE_LOG_EVERY = 12

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

_active = False  # True when detection is actively processing frames
_key_ctrl = KeyController()
_last_press = [0.0, 0.0, 0.0, 0.0, 0.0]
_lane_occupied = [False, False, False, False, False]
_lane_is_down = [False, False, False, False, False]
_lane_ready = [True, True, True, True, True]
_lane_down_since = [0.0, 0.0, 0.0, 0.0, 0.0]
_lane_empty_frames = [0, 0, 0, 0, 0]
_lane_clear_frames = [0, 0, 0, 0, 0]
_frame_data = {"count": 0, "hits": 0, "start": 0.0, "err": 0}
_lane_byte_offsets = None  # computed on first frame
_hold_lane_byte_offsets = None  # computed on first frame
_keep_alive = []  # prevent GC of ObjC objects
_input_queue = queue.Queue()
_tap_worker_started = False
_tap_stop = threading.Event()
_stream_initialized = False


def _compute_byte_offsets(actual_width, sample_radius):
    """Compute lane byte offsets accounting for Retina scaling."""
    scale = actual_width / 220.0
    offsets = []
    for idx, center in enumerate(LANE_OFFSETS):
        adjusted_center = center + LANE_CENTER_ADJUST[idx]
        scaled_center = int(adjusted_center * scale)
        radius = int(sample_radius * scale)
        lane = []
        for dx in range(-radius, radius + 1):
            px = scaled_center + dx
            if 0 <= px < actual_width:
                lane.append(px * 4)
        offsets.append(tuple(lane))
    return offsets


def _lane_match_count(row, offsets, sat_threshold, val_threshold, bpr):
    """Return how many pixels in this lane look like a note body."""
    hits = 0
    for off in offsets:
        if off + 2 >= bpr:
            continue
        b, g, r = row[off], row[off + 1], row[off + 2]
        mx = max(r, g, b)
        if mx < val_threshold:
            continue
        mn = min(r, g, b)
        sat = ((mx - mn) * 255) // mx if mx > 0 else 0
        if sat >= sat_threshold:
            hits += 1
    return hits


def _release_all_keys():
    """Release any keys that the detector currently believes are held down."""
    for i, key_name in enumerate(LANE_KEYS):
        if _lane_is_down[i]:
            _input_queue.put(("up", key_name))
            _lane_is_down[i] = False
            _lane_empty_frames[i] = 0
            _lane_clear_frames[i] = 0
            _lane_ready[i] = False


def _tap_worker():
    """Send key events off the capture callback thread."""
    while not _tap_stop.is_set():
        try:
            action, key_name = _input_queue.get(timeout=0.1)
        except queue.Empty:
            continue
        try:
            if action == "down":
                _key_ctrl.press(key_name)
            elif action == "up":
                _key_ctrl.release(key_name)
            if key_name == "f":
                print(f"  [worker] {action.upper()} F")
        except Exception as exc:
            print(f"  [tap error] {exc}")
        finally:
            _input_queue.task_done()


def _ensure_tap_worker():
    global _tap_worker_started, _tap_stop
    if _tap_worker_started and not _tap_stop.is_set():
        return
    if _tap_stop.is_set():
        _tap_stop = threading.Event()
    worker = threading.Thread(target=_tap_worker, daemon=True, name="jam.tap.worker")
    worker.start()
    _tap_worker_started = True


# ---------------------------------------------------------------------------
# Stream output delegate (called on dispatch queue at ~60fps)
# ---------------------------------------------------------------------------

class _StreamOutput(NSObject):
    def stream_didOutputSampleBuffer_ofType_(self, _stream, sample_buffer, typ):
        global _lane_byte_offsets, _hold_lane_byte_offsets

        if typ != 0 or not _active:
            return

        try:
            ptr = sample_buffer.pointerAsInteger
            pb = _cm.CMSampleBufferGetImageBuffer(ptr)
            if not pb:
                return

            _cv.CVPixelBufferLockBaseAddress(pb, 1)
            base = _cv.CVPixelBufferGetBaseAddress(pb)
            bpr = _cv.CVPixelBufferGetBytesPerRow(pb)

            if not base or bpr <= 0:
                _cv.CVPixelBufferUnlockBaseAddress(pb, 1)
                return

            # Auto-detect scale on first frame
            if _lane_byte_offsets is None:
                actual_w = _cv.CVPixelBufferGetWidth(pb)
                _lane_byte_offsets = _compute_byte_offsets(actual_w, SAMPLE_RADIUS)
                _hold_lane_byte_offsets = _compute_byte_offsets(actual_w, HOLD_SAMPLE_RADIUS)
                scale = actual_w / 220.0
                print(f"  [info] Pixel buffer: {actual_w}px wide, scale={scale:.1f}x")

            start_row_addr = base + (START_ROW_INDEX * bpr)
            f_start_row_addr = base + (F_START_ROW_INDEX * bpr)
            hold_row_addr = base + (HOLD_ROW_INDEX * bpr)
            start_row = (ctypes.c_uint8 * bpr).from_address(start_row_addr)
            hold_row = (ctypes.c_uint8 * bpr).from_address(hold_row_addr)
            now = time.time()
            sat_t = SAT_THRESHOLD
            val_t = VAL_THRESHOLD

            lane_counts = []
            count = _frame_data["count"]
            if DEBUG_PIXEL_LOG_EVERY and count % DEBUG_PIXEL_LOG_EVERY == 0:
                parts = []
                for i in range(5):
                    mid = len(_lane_byte_offsets[i]) // 2
                    off = _lane_byte_offsets[i][mid]
                    if off + 2 < bpr:
                        b, g, r = start_row[off], start_row[off + 1], start_row[off + 2]
                        mx = max(r, g, b)
                        mn = min(r, g, b)
                        sat = ((mx - mn) * 255) // mx if mx > 0 else 0
                        parts.append(f"{LANE_KEYS[i].upper()}:({r},{g},{b}) s={sat}")
                print(f"  [px] {' | '.join(parts)}")

            for i in range(5):
                if i == 3:
                    start_match_count = 0
                    for row_delta in F_START_ROW_WINDOW:
                        row_index = F_START_ROW_INDEX + row_delta
                        if not (0 <= row_index < CAPTURE_HEIGHT):
                            continue
                        row_addr = base + (row_index * bpr)
                        row_buf = (ctypes.c_uint8 * bpr).from_address(row_addr)
                        row_count = _lane_match_count(row_buf, _lane_byte_offsets[i], sat_t, val_t, bpr)
                        if row_count > start_match_count:
                            start_match_count = row_count
                else:
                    start_match_count = _lane_match_count(start_row, _lane_byte_offsets[i], sat_t, val_t, bpr)
                hold_match_count = _lane_match_count(
                    hold_row,
                    _hold_lane_byte_offsets[i],
                    LANE_HOLD_SAT_THRESHOLDS[i],
                    LANE_HOLD_VAL_THRESHOLDS[i],
                    bpr,
                )
                lane_counts.append(hold_match_count)
                if LANE_USE_HOLD_FALLBACK_FOR_START[i]:
                    effective_start_count = max(start_match_count, hold_match_count)
                else:
                    effective_start_count = start_match_count
                start_occupied = effective_start_count >= LANE_START_MIN_PIXELS[i]
                sustain_occupied = hold_match_count >= LANE_HOLD_MIN_PIXELS[i]
                combined_occupied = start_occupied or sustain_occupied

                if _lane_is_down[i]:
                    if combined_occupied:
                        _lane_empty_frames[i] = 0
                    else:
                        _lane_empty_frames[i] += 1
                        held_long_enough = now - _lane_down_since[i] >= MIN_KEY_HOLD
                        if _lane_empty_frames[i] >= LANE_RELEASE_EMPTY_FRAMES[i] and held_long_enough:
                            _input_queue.put(("up", LANE_KEYS[i]))
                            _lane_is_down[i] = False
                            _lane_ready[i] = False
                            _lane_clear_frames[i] = 0
                            _lane_empty_frames[i] = 0
                            if DEBUG_HIT_LOG:
                                print(
                                    f"  [{LANE_KEYS[i].upper()}] up "
                                    f"(start={start_match_count}, hold={hold_match_count})"
                                )

                if not _lane_is_down[i] and not _lane_ready[i]:
                    if combined_occupied:
                        _lane_clear_frames[i] = 0
                    else:
                        _lane_clear_frames[i] += 1
                        if _lane_clear_frames[i] >= LANE_REARM_CLEAR_FRAMES[i]:
                            _lane_ready[i] = True
                            _lane_clear_frames[i] = 0
                            if DEBUG_STATE_LOG:
                                print(
                                    f"  [{LANE_KEYS[i].upper()}] rearmed "
                                    f"(start={start_match_count}, hold={hold_match_count})"
                                )

                if (
                    _lane_ready[i]
                    and not _lane_is_down[i]
                    and start_occupied
                    and now - _last_press[i] >= MIN_PRESS_GAP
                ):
                    _input_queue.put(("down", LANE_KEYS[i]))
                    _lane_is_down[i] = True
                    _lane_ready[i] = False
                    _lane_down_since[i] = now
                    _lane_empty_frames[i] = 0
                    _lane_clear_frames[i] = 0
                    _last_press[i] = now
                    _frame_data["hits"] += 1
                    if DEBUG_HIT_LOG:
                        print(
                            f"  [{LANE_KEYS[i].upper()}] down "
                            f"(start={start_match_count}, hold={hold_match_count}, effective={effective_start_count})"
                        )

                _lane_occupied[i] = combined_occupied

                if DEBUG_LANE_LOG_EVERY and i == DEBUG_LANE_INDEX and count % DEBUG_LANE_LOG_EVERY == 0:
                    print(
                        "  [F lane] "
                        f"start={start_match_count} hold={hold_match_count} effective={effective_start_count} "
                        f"ready={int(_lane_ready[i])} down={int(_lane_is_down[i])} "
                        f"empty={_lane_empty_frames[i]} clear={_lane_clear_frames[i]}"
                    )

            if DEBUG_OCC_LOG_EVERY and count % DEBUG_OCC_LOG_EVERY == 0:
                occ = " | ".join(
                    f"{LANE_KEYS[i].upper()}:{lane_counts[i]}{'*' if _lane_occupied[i] else ''}"
                    for i in range(5)
                )
                print(f"  [occ] {occ}")

            _frame_data["count"] += 1
            _cv.CVPixelBufferUnlockBaseAddress(pb, 1)

        except Exception as exc:
            _frame_data["err"] += 1
            if _frame_data["err"] <= 3:
                print(f"  [error] {exc}")


# ---------------------------------------------------------------------------
# Setup (must run on main thread)
# ---------------------------------------------------------------------------

def _init_stream():
    """Create and start the SCStream on the main thread. Returns True on success."""
    global _lane_byte_offsets, _hold_lane_byte_offsets, _stream_initialized
    if _stream_initialized:
        return True
    _lane_byte_offsets = None
    _hold_lane_byte_offsets = None
    _ensure_tap_worker()

    print("[JAM] Initializing ScreenCaptureKit...")

    # Get display
    result = {"content": None, "done": threading.Event()}
    def on_content(content, _err):
        result["content"] = content
        result["done"].set()

    SCShareableContent.getShareableContentExcludingDesktopWindows_onScreenWindowsOnly_completionHandler_(  # noqa: F821
        True, True, on_content
    )
    for _ in range(200):
        NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.05))
        if result["done"].is_set():
            break

    if result["content"] is None:
        print("[JAM] ERROR: No screen content. Grant Screen Recording permission and restart.")
        return False

    display = result["content"].displays()[0]
    print(f"[JAM] Display: {display.width()}x{display.height()}")

    config = SCStreamConfiguration.alloc().init()  # noqa: F821
    config.setWidth_(SOURCE_WIDTH)
    config.setHeight_(CAPTURE_HEIGHT)
    config.setShowsCursor_(False)
    config.setSourceRect_(SOURCE_RECT)
    config.setScalesToFit_(True)
    config.setQueueDepth_(3)
    config.setPixelFormat_(0x42475241)

    content_filter = SCContentFilter.alloc().initWithDisplay_excludingWindows_(display, [])  # noqa: F821
    stream = SCStream.alloc().initWithFilter_configuration_delegate_(content_filter, config, None)  # noqa: F821

    output = _StreamOutput.alloc().init()
    q = dispatch_queue_create(b"jam.frames", None)
    stream.addStreamOutput_type_sampleHandlerQueue_error_(output, 0, q, None)

    started = threading.Event()
    stream.startCaptureWithCompletionHandler_(lambda _e: started.set())
    for _ in range(100):
        NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.05))
        if started.is_set():
            break

    # Prevent garbage collection
    _keep_alive.extend([stream, output, q, content_filter, config])
    _stream_initialized = True

    print("[JAM] Stream ready. Press P to start, O to stop.")
    return True


# ---------------------------------------------------------------------------
# Start / Stop toggle
# ---------------------------------------------------------------------------

def _start():
    global _active
    if _active:
        return
    _active = True
    _last_press[:] = [0.0, 0.0, 0.0, 0.0, 0.0]
    _lane_occupied[:] = [False, False, False, False, False]
    _lane_is_down[:] = [False, False, False, False, False]
    _lane_ready[:] = [True, True, True, True, True]
    _lane_down_since[:] = [0.0, 0.0, 0.0, 0.0, 0.0]
    _lane_empty_frames[:] = [0, 0, 0, 0, 0]
    _lane_clear_frames[:] = [0, 0, 0, 0, 0]
    _frame_data.update(count=0, hits=0, err=0, start=time.time())
    print("[JAM] Detection ACTIVE — watching for orbs...")


def _stop():
    global _active
    if not _active:
        return
    _active = False
    _release_all_keys()
    elapsed = time.time() - _frame_data["start"]
    count = _frame_data["count"]
    fps = count / elapsed if elapsed > 0 else 0
    print(
        f"[JAM] Detection PAUSED. {count} frames in {elapsed:.1f}s "
        f"({fps:.1f} fps), {_frame_data['hits']} keys pressed"
    )


def _on_press(key):
    try:
        if key.char == "p":
            _start()
        elif key.char == "o":
            _stop()
        elif key.char == "6":
            print("  [manual] queueing F tap through worker")
            _input_queue.put(("down", "f"))
            _input_queue.put(("up", "f"))
    except AttributeError:
        pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 50)
    print("  Skele King Jam Detector — Test Script")
    print("=" * 50)
    print()
    print(f"  Capture: {SOURCE_WIDTH}x{CAPTURE_HEIGHT}px at ({SOURCE_X}, {CAPTURE_TOP_Y})")
    print(f"  Start line: y={SOURCE_Y - START_TRIGGER_OFFSET} ({START_TRIGGER_OFFSET}px early)")
    print(f"  F start line: y={SOURCE_Y - F_START_TRIGGER_OFFSET} ({F_START_TRIGGER_OFFSET}px early)")
    print(f"  Hold line: y={SOURCE_Y - HOLD_TRIGGER_OFFSET} ({HOLD_TRIGGER_OFFSET}px early)")
    print(f"  Start thresholds: sat>{SAT_THRESHOLD}, val>{VAL_THRESHOLD}")
    print(f"  Hold thresholds: sat>{HOLD_SAT_THRESHOLD}, val>{HOLD_VAL_THRESHOLD}")
    print(f"  Start occupancy base: {MIN_MATCHING_PIXELS}+ matching pixels")
    print(f"  Hold occupancy base: {MIN_HOLD_MATCHING_PIXELS}+ matching pixels")
    print(f"  Min press gap: {MIN_PRESS_GAP * 1000:.0f}ms")
    print(f"  Min key hold: {MIN_KEY_HOLD * 1000:.0f}ms")
    print(f"  Release after: {RELEASE_EMPTY_FRAMES} empty frame(s)")
    print(f"  Rearm after base: {REARM_CLEAR_FRAMES} clear frame(s)")
    print(f"  Hold sample radius: {HOLD_SAMPLE_RADIUS}px")
    print(f"  Lane start mins: {LANE_START_MIN_PIXELS}")
    print(f"  Lane center adjust: {LANE_CENTER_ADJUST}")
    print(f"  Lane hold sat thresholds: {LANE_HOLD_SAT_THRESHOLDS}")
    print(f"  Lane hold val thresholds: {LANE_HOLD_VAL_THRESHOLDS}")
    print(f"  Lane release empty frames: {LANE_RELEASE_EMPTY_FRAMES}")
    print(f"  Lane rearm frames: {LANE_REARM_CLEAR_FRAMES}")
    print(f"  Hold fallback for start: {LANE_USE_HOLD_FALLBACK_FOR_START}")
    print(f"  F start row window: {F_START_ROW_WINDOW}")
    print(f"  State debug: {'on' if DEBUG_STATE_LOG else 'off'}")
    print("  Backend: ScreenCaptureKit (~60fps)")
    print()
    print("  Lanes:")
    for i, key in enumerate(LANE_KEYS):
        print(f"    {key.upper()}: x={LANE_OFFSETS[i] + 490}")
    print()

    # Initialize stream on main thread BEFORE starting pynput
    if not _init_stream():
        return

    print()
    print("  [P] Start detection")
    print("  [O] Stop / pause detection")
    print("  [6] Manual F tap through worker")
    print("  [Ctrl+C] Quit")
    print()

    with keyboard.Listener(on_press=_on_press) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            _stop()
            _tap_stop.set()
            print("\n[JAM] Exited.")


if __name__ == "__main__":
    main()
