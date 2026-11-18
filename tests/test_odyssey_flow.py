import math

import cv2
import numpy as np

from macro_app.services.odyssey_flow import (
    ODYSSEY_MEMORIA_REFS,
    TREASURE_ROOM_DETECTION_DELAY_SECONDS,
    OdysseyCandidateScore,
    OdysseyFlowService,
    OdysseyMatch,
)


def _draw_dashed_line(
    mask: np.ndarray,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    start_fraction: float = 0.0,
    end_fraction: float = 1.0,
    dash_length: int = 14,
    gap_length: int = 10,
    width: int = 4,
) -> None:
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    distance = math.hypot(dx, dy)
    if distance <= 0:
        return
    ux = dx / distance
    uy = dy / distance
    cursor = max(0.0, distance * start_fraction)
    limit = min(distance, distance * end_fraction)
    while cursor < limit:
        dash_end = min(cursor + dash_length, limit)
        p1 = (int(round(sx + ux * cursor)), int(round(sy + uy * cursor)))
        p2 = (int(round(sx + ux * dash_end)), int(round(sy + uy * dash_end)))
        cv2.line(mask, p1, p2, 255, width)
        cursor += dash_length + gap_length


def test_odyssey_corridor_accepts_dotted_path_from_current_node():
    mask = np.zeros((240, 280), dtype=np.uint8)
    current = (40, 190)
    target = (220, 40)
    _draw_dashed_line(mask, current, target)

    score = OdysseyFlowService._score_corridor(
        mask,
        current,
        OdysseyMatch("boss", target[0], target[1], 0, 0, 0.95),
        endpoint_skip=20,
        min_upward_px=1,
        min_corridor_score=0.005,
    )

    assert score.accepted is True


def test_odyssey_corridor_rejects_unrelated_dotted_line_not_leaving_current_node():
    mask = np.zeros((240, 280), dtype=np.uint8)
    current = (40, 190)
    target = (220, 40)
    _draw_dashed_line(mask, current, target, start_fraction=0.45, end_fraction=1.0)

    score = OdysseyFlowService._score_corridor(
        mask,
        current,
        OdysseyMatch("normal", target[0], target[1], 0, 0, 0.95),
        endpoint_skip=20,
        min_upward_px=1,
        min_corridor_score=0.005,
    )

    assert score.accepted is False
    assert "current" in score.reason or "coverage" in score.reason or "gap" in score.reason


def test_odyssey_corridor_rejects_candidate_not_in_source_branch_direction():
    mask = np.zeros((260, 360), dtype=np.uint8)
    current = (60, 210)
    connected_target = (60, 40)
    wrong_priority_target = (310, 70)
    _draw_dashed_line(mask, current, connected_target)
    _draw_dashed_line(mask, (130, 170), wrong_priority_target)

    wrong_score = OdysseyFlowService._score_corridor(
        mask,
        current,
        OdysseyMatch("normal", wrong_priority_target[0], wrong_priority_target[1], 0, 0, 0.95),
        endpoint_skip=20,
        min_upward_px=1,
        min_corridor_score=0.005,
    )
    connected_score = OdysseyFlowService._score_corridor(
        mask,
        current,
        OdysseyMatch("boss", connected_target[0], connected_target[1], 0, 0, 0.95),
        endpoint_skip=20,
        min_upward_px=1,
        min_corridor_score=0.005,
    )

    assert wrong_score.accepted is False
    assert "direct dotted branch" in wrong_score.reason
    assert connected_score.accepted is True


def test_odyssey_select_best_connected_prefers_elite_boss_override():
    normal_score = OdysseyCandidateScore(
        OdysseyMatch("normal", 20, 20, 20, 20, 0.95),
        corridor_score=0.2,
        dotted_pixels=100,
        distance=80.0,
        accepted=True,
        reason="connected",
    )
    elite_score = OdysseyCandidateScore(
        OdysseyMatch("elite_boss", 120, 20, 20, 20, 0.95),
        corridor_score=0.2,
        dotted_pixels=100,
        distance=80.0,
        accepted=True,
        reason="connected",
    )

    selected = OdysseyFlowService._select_best_connected(
        [normal_score, elite_score],
        ("Normal", "Shop", "Boss"),
    )

    assert selected is elite_score


def test_odyssey_memoria_refs_include_new_options_and_treasure_delay():
    assert ODYSSEY_MEMORIA_REFS["Damage"] == "damage_memoria_odyssey_ref.png"
    assert ODYSSEY_MEMORIA_REFS["All I got"] == "all_i_got_memoria_odyssey_ref.png"
    assert TREASURE_ROOM_DETECTION_DELAY_SECONDS == 3.0
