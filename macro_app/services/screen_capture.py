"""Shared screen capture with a DeskPad-safe Roblox window backend."""

from __future__ import annotations

import ctypes
import ctypes.util
import threading
import time
from typing import Any

import cv2
import numpy as np
from mss import mss

from macro_app.services.relative_positioning import (
    BASE_ROBLOX_BOTTOM,
    BASE_ROBLOX_LEFT,
    BASE_ROBLOX_RIGHT,
    BASE_ROBLOX_TOP,
    RelativePositioner,
    find_roblox_process_id,
)

try:
    import objc
    import ScreenCaptureKit
    from dispatch import dispatch_queue_create
    from Foundation import NSDate, NSObject, NSRunLoop
    from Quartz import CGDisplayBounds, CGMainDisplayID
except ImportError:  # pragma: no cover - unavailable on non-macOS test hosts.
    objc = None
    ScreenCaptureKit = None
    dispatch_queue_create = None
    NSDate = None
    NSObject = object
    NSRunLoop = None
    CGDisplayBounds = None
    CGMainDisplayID = None


class ScreenCaptureError(RuntimeError):
    """Raised when the requested capture source cannot provide a valid frame."""


def roblox_is_off_main_display(positioner: RelativePositioner) -> bool:
    """Return whether Roblox's center is outside the macOS main display."""
    if CGDisplayBounds is None or CGMainDisplayID is None:
        return False
    bounds = positioner.current_bounds()
    main_bounds = CGDisplayBounds(CGMainDisplayID())
    center_x = bounds.left + (bounds.width / 2)
    center_y = bounds.top + (bounds.height / 2)
    return not (
        main_bounds.origin.x <= center_x < main_bounds.origin.x + main_bounds.size.width
        and main_bounds.origin.y <= center_y < main_bounds.origin.y + main_bounds.size.height
    )


if objc is not None:
    _block_two_objects = {
        "callable": {
            "retval": {"type": b"v"},
            "arguments": {
                0: {"type": b"^v"},
                1: {"type": b"@"},
                2: {"type": b"@"},
            },
        }
    }
    _block_one_object = {
        "callable": {
            "retval": {"type": b"v"},
            "arguments": {0: {"type": b"^v"}, 1: {"type": b"@"}},
        }
    }
    objc.registerMetaDataForSelector(
        b"SCShareableContent",
        b"getShareableContentExcludingDesktopWindows:onScreenWindowsOnly:completionHandler:",
        {"arguments": {4: _block_two_objects}},
    )
    objc.registerMetaDataForSelector(
        b"SCStream",
        b"startCaptureWithCompletionHandler:",
        {"arguments": {2: _block_one_object}},
    )
    objc.registerMetaDataForSelector(
        b"SCStream",
        b"stopCaptureWithCompletionHandler:",
        {"arguments": {2: _block_one_object}},
    )
    objc.registerMetaDataForSelector(
        b"NSObject",
        b"stream:didOutputSampleBuffer:ofType:",
        {
            "retval": {"type": b"v"},
            "arguments": {
                2: {"type": b"@"},
                3: {"type": b"^{opaqueCMSampleBuffer=}"},
                4: {"type": b"q"},
            },
        },
    )


_core_media = None
_core_video = None
if ctypes.util.find_library("CoreMedia") and ctypes.util.find_library("CoreVideo"):
    _core_media = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreMedia"))
    _core_video = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreVideo"))
    _core_media.CMSampleBufferGetImageBuffer.restype = ctypes.c_void_p
    _core_media.CMSampleBufferGetImageBuffer.argtypes = [ctypes.c_void_p]
    _core_video.CVPixelBufferLockBaseAddress.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
    _core_video.CVPixelBufferUnlockBaseAddress.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
    _core_video.CVPixelBufferGetBaseAddress.restype = ctypes.c_void_p
    _core_video.CVPixelBufferGetBaseAddress.argtypes = [ctypes.c_void_p]
    _core_video.CVPixelBufferGetBytesPerRow.restype = ctypes.c_size_t
    _core_video.CVPixelBufferGetBytesPerRow.argtypes = [ctypes.c_void_p]
    _core_video.CVPixelBufferGetWidth.restype = ctypes.c_size_t
    _core_video.CVPixelBufferGetWidth.argtypes = [ctypes.c_void_p]
    _core_video.CVPixelBufferGetHeight.restype = ctypes.c_size_t
    _core_video.CVPixelBufferGetHeight.argtypes = [ctypes.c_void_p]


class _WindowStreamOutput(NSObject):
    if objc is not None:
        backend = objc.ivar()

    def initWithBackend_(self, backend):
        self = objc.super(_WindowStreamOutput, self).init()
        if self is not None:
            self.backend = backend
        return self

    def stream_didOutputSampleBuffer_ofType_(self, _stream, sample_buffer, output_type):
        if output_type != 0 or _core_media is None or _core_video is None:
            return
        try:
            pixel_buffer = _core_media.CMSampleBufferGetImageBuffer(sample_buffer.pointerAsInteger)
            if not pixel_buffer:
                return
            _core_video.CVPixelBufferLockBaseAddress(pixel_buffer, 1)
            try:
                base_address = _core_video.CVPixelBufferGetBaseAddress(pixel_buffer)
                bytes_per_row = _core_video.CVPixelBufferGetBytesPerRow(pixel_buffer)
                width = int(_core_video.CVPixelBufferGetWidth(pixel_buffer))
                height = int(_core_video.CVPixelBufferGetHeight(pixel_buffer))
                if not base_address or width <= 0 or height <= 0 or bytes_per_row < width * 4:
                    return
                byte_count = int(bytes_per_row) * height
                buffer_type = ctypes.c_uint8 * byte_count
                raw = np.ctypeslib.as_array(buffer_type.from_address(base_address))
                rows = raw.reshape(height, int(bytes_per_row))
                bgra = rows[:, : width * 4].reshape(height, width, 4)
                self.backend._store_frame(bgra[:, :, :3].copy())
            finally:
                _core_video.CVPixelBufferUnlockBaseAddress(pixel_buffer, 1)
        except Exception as exc:  # pragma: no cover - callback errors require live SCK.
            self.backend._store_error(exc)


class ScreenCaptureKitWindowStream:
    """Continuously capture the desktop-independent Roblox window."""

    def __init__(self, positioner: RelativePositioner) -> None:
        self._positioner = positioner
        self._condition = threading.Condition()
        self._latest_frame: np.ndarray | None = None
        self._latest_frame_at = 0.0
        self._frame_count = 0
        self._callback_error: Exception | None = None
        self._stream = None
        self._output = None
        self._queue = None
        self._filter = None
        self._configuration = None
        self._started = False

    @property
    def frame_count(self) -> int:
        with self._condition:
            return self._frame_count

    def diagnostics(self) -> dict[str, Any]:
        with self._condition:
            frame = self._latest_frame
            return {
                "frame_count": self._frame_count,
                "frame_age": (
                    max(0.0, time.monotonic() - self._latest_frame_at)
                    if frame is not None
                    else None
                ),
                "frame_shape": tuple(frame.shape) if frame is not None else None,
            }

    def start(self, timeout: float = 5.0) -> None:
        if self._started:
            return
        if ScreenCaptureKit is None or objc is None or _core_media is None or _core_video is None:
            raise ScreenCaptureError("ScreenCaptureKit capture is unavailable on this system")

        content_result: dict[str, Any] = {"content": None, "error": None}
        content_ready = threading.Event()

        def on_content(content, error):
            content_result["content"] = content
            content_result["error"] = error
            content_ready.set()

        ScreenCaptureKit.SCShareableContent.getShareableContentExcludingDesktopWindows_onScreenWindowsOnly_completionHandler_(
            True,
            False,
            on_content,
        )
        self._wait_for_event(content_ready, timeout)
        if not content_ready.is_set():
            raise ScreenCaptureError("Timed out while requesting ScreenCaptureKit windows")
        if content_result["error"] is not None:
            raise ScreenCaptureError(f"ScreenCaptureKit window query failed: {content_result['error']}")

        roblox_pid = find_roblox_process_id()
        window = self._find_roblox_window(content_result["content"], roblox_pid)
        if window is None:
            raise ScreenCaptureError("ScreenCaptureKit could not find the Roblox window")

        bounds = self._positioner.current_bounds()
        configuration = ScreenCaptureKit.SCStreamConfiguration.alloc().init()
        configuration.setWidth_(bounds.width)
        configuration.setHeight_(bounds.height)
        configuration.setShowsCursor_(False)
        configuration.setScalesToFit_(True)
        configuration.setQueueDepth_(3)
        configuration.setPixelFormat_(0x42475241)  # BGRA
        if hasattr(configuration, "setCapturesAudio_"):
            configuration.setCapturesAudio_(False)
        if hasattr(configuration, "setIgnoreShadows_"):
            configuration.setIgnoreShadows_(True)

        content_filter = ScreenCaptureKit.SCContentFilter.alloc().initWithDesktopIndependentWindow_(window)
        stream = ScreenCaptureKit.SCStream.alloc().initWithFilter_configuration_delegate_(
            content_filter,
            configuration,
            None,
        )
        output = _WindowStreamOutput.alloc().initWithBackend_(self)
        queue = dispatch_queue_create(b"zeron.roblox.window.capture", None)
        added, add_error = stream.addStreamOutput_type_sampleHandlerQueue_error_(
            output,
            0,
            queue,
            None,
        )
        if not added:
            raise ScreenCaptureError(f"Could not attach ScreenCaptureKit output: {add_error}")

        start_result = {"error": None}
        started = threading.Event()

        def on_started(error):
            start_result["error"] = error
            started.set()

        self._stream = stream
        self._output = output
        self._queue = queue
        self._filter = content_filter
        self._configuration = configuration
        stream.startCaptureWithCompletionHandler_(on_started)
        self._wait_for_event(started, timeout)
        if not started.is_set():
            self.stop()
            raise ScreenCaptureError("Timed out while starting Roblox window capture")
        if start_result["error"] is not None:
            self.stop()
            raise ScreenCaptureError(f"Could not start Roblox window capture: {start_result['error']}")

        deadline = time.monotonic() + timeout
        with self._condition:
            while self._latest_frame is None and self._callback_error is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._condition.wait(min(0.1, remaining))
        if self._callback_error is not None:
            error = self._callback_error
            self.stop()
            raise ScreenCaptureError(f"Roblox window capture callback failed: {error}")
        if self._latest_frame is None:
            self.stop()
            raise ScreenCaptureError("Roblox window capture started but produced no frames")
        self._started = True

    def stop(self) -> None:
        stream = self._stream
        self._started = False
        if stream is not None:
            stopped = threading.Event()
            try:
                stream.stopCaptureWithCompletionHandler_(lambda _error: stopped.set())
                stopped.wait(1.0)
            except Exception:
                pass
        self._stream = None
        self._output = None
        self._queue = None
        self._filter = None
        self._configuration = None

    def capture_region_bgr(self, region: tuple[int, int, int, int]) -> np.ndarray:
        bounds = self._positioner.current_bounds()
        left, top, right, bottom = region
        if left < bounds.left or top < bounds.top or right > bounds.right or bottom > bounds.bottom:
            raise ScreenCaptureError(
                f"Capture region {region} lies outside Roblox bounds "
                f"({bounds.left}, {bounds.top}, {bounds.right}, {bounds.bottom})"
            )

        return self._capture_local_region(
            left - bounds.left,
            top - bounds.top,
            right - bounds.left,
            bottom - bounds.top,
            right - left,
            bottom - top,
        )

    def capture_base_region_bgr(self, region: tuple[int, int, int, int]) -> np.ndarray:
        """Capture a calibrated base region without consulting global window position."""
        left, top, right, bottom = region
        if (
            left < BASE_ROBLOX_LEFT
            or top < BASE_ROBLOX_TOP
            or right > BASE_ROBLOX_RIGHT
            or bottom > BASE_ROBLOX_BOTTOM
        ):
            raise ScreenCaptureError(f"Base capture region {region} lies outside Roblox's base frame")
        return self._capture_local_region(
            left - BASE_ROBLOX_LEFT,
            top - BASE_ROBLOX_TOP,
            right - BASE_ROBLOX_LEFT,
            bottom - BASE_ROBLOX_TOP,
            right - left,
            bottom - top,
        )

    def _capture_local_region(
        self,
        local_left: int,
        local_top: int,
        local_right: int,
        local_bottom: int,
        expected_width: int,
        expected_height: int,
    ) -> np.ndarray:
        with self._condition:
            if self._callback_error is not None:
                raise ScreenCaptureError(f"Roblox window capture failed: {self._callback_error}")
            if self._latest_frame is None:
                raise ScreenCaptureError("Roblox window capture has no frame")
            frame = self._latest_frame.copy()

        frame_height, frame_width = frame.shape[:2]
        base_width = BASE_ROBLOX_RIGHT - BASE_ROBLOX_LEFT
        base_height = BASE_ROBLOX_BOTTOM - BASE_ROBLOX_TOP
        scale_x = frame_width / max(1, base_width)
        scale_y = frame_height / max(1, base_height)
        frame_left = round(local_left * scale_x)
        frame_top = round(local_top * scale_y)
        frame_right = round(local_right * scale_x)
        frame_bottom = round(local_bottom * scale_y)
        crop = frame[frame_top:frame_bottom, frame_left:frame_right]
        if crop.size == 0:
            raise ScreenCaptureError(
                "Roblox window capture produced an empty local crop "
                f"({local_left}, {local_top}, {local_right}, {local_bottom})"
            )

        if crop.shape[1] != expected_width or crop.shape[0] != expected_height:
            crop = cv2.resize(crop, (expected_width, expected_height), interpolation=cv2.INTER_AREA)
        return crop

    def _store_frame(self, frame: np.ndarray) -> None:
        with self._condition:
            self._latest_frame = frame
            self._latest_frame_at = time.monotonic()
            self._frame_count += 1
            self._condition.notify_all()

    def _store_error(self, error: Exception) -> None:
        with self._condition:
            self._callback_error = error
            self._condition.notify_all()

    @staticmethod
    def _find_roblox_window(content, expected_pid: int | None = None):
        if content is None:
            return None
        candidates = []
        for window in content.windows():
            owner = window.owningApplication()
            owner_name = str(owner.applicationName() or "") if owner is not None else ""
            owner_pid = int(owner.processID()) if owner is not None else 0
            if expected_pid is not None and owner_pid != expected_pid:
                continue
            if expected_pid is None and "Roblox" not in owner_name:
                continue
            frame = window.frame()
            width = int(frame.size.width)
            height = int(frame.size.height)
            if width <= 0 or height <= 0:
                continue
            candidates.append((width * height, window))
        if not candidates:
            return None
        return max(candidates, key=lambda item: item[0])[1]

    @staticmethod
    def _wait_for_event(event: threading.Event, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        if NSRunLoop is None or threading.current_thread() is not threading.main_thread():
            event.wait(timeout)
            return
        while not event.is_set() and time.monotonic() < deadline:
            NSRunLoop.currentRunLoop().runUntilDate_(
                NSDate.dateWithTimeIntervalSinceNow_(0.02)
            )


class RuntimeScreenCapture:
    """Use mss normally and ScreenCaptureKit for off-main Roblox windows."""

    def __init__(self, positioner: RelativePositioner | None = None) -> None:
        self._positioner = positioner
        self._mss = None
        self._window_stream = None
        self._uses_window_capture = bool(
            positioner is not None and roblox_is_off_main_display(positioner)
        )

    @property
    def uses_window_capture(self) -> bool:
        return self._uses_window_capture

    @property
    def backend_name(self) -> str:
        return "ScreenCaptureKit Roblox window" if self._uses_window_capture else "mss display"

    def start(self) -> None:
        if not self._uses_window_capture:
            return
        self._window_stream = ScreenCaptureKitWindowStream(self._positioner)
        self._window_stream.start()

    def stop(self) -> None:
        if self._window_stream is not None:
            self._window_stream.stop()
            self._window_stream = None
        self._mss = None

    def capture_region_bgr(self, region: tuple[int, int, int, int]) -> np.ndarray:
        if self._uses_window_capture:
            if self._window_stream is None:
                raise ScreenCaptureError("ScreenCaptureKit Roblox window capture is not started")
            return self._window_stream.capture_region_bgr(region)

        if self._mss is None:
            self._mss = mss()
        left, top, right, bottom = region
        shot = self._mss.grab(
            {
                "left": left,
                "top": top,
                "width": right - left,
                "height": bottom - top,
            }
        )
        return cv2.cvtColor(np.asarray(shot), cv2.COLOR_BGRA2BGR)

    def capture_base_region_bgr(self, region: tuple[int, int, int, int]) -> np.ndarray:
        if self._uses_window_capture:
            if self._window_stream is None:
                raise ScreenCaptureError("ScreenCaptureKit Roblox window capture is not started")
            return self._window_stream.capture_base_region_bgr(region)

        if self._positioner is not None:
            region = self._positioner.translate_region(region)
        return self.capture_region_bgr(region)

    def diagnostics(self) -> dict[str, Any]:
        if self._window_stream is not None:
            return self._window_stream.diagnostics()
        return {"frame_count": None, "frame_age": None, "frame_shape": None}
