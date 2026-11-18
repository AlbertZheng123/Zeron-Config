import os
from datetime import datetime

from macro_app.services.run_logs import MacroRunLogger


def test_macro_run_logger_writes_iteration_and_archives(tmp_path):
    logger = MacroRunLogger(str(tmp_path))
    logger.start_session("Legend", "Burning Spirit Tree", "Auto Farm", started_at=datetime(2026, 4, 7, 13, 42))
    logger.start_iteration(started_at=datetime(2026, 4, 7, 13, 43))
    logger.log("Placed unit")
    logger.finish_iteration(65, rewards={})
    path = logger.finalize()

    assert path == os.path.join(str(tmp_path), "Legend_Burning_Spirit_Tree_04_07_13_42.log")
    contents = open(path, encoding="utf-8").read()
    assert contents.startswith("----MACRO START-----\n04/07 13:43:00")
    assert "Macro: Auto Farm" in contents
    assert "Placed unit" in contents
    assert "---- MACRO SUMMARY ---" in contents
    assert "Rewards: {}" in contents
    assert "Total time: 1m 5s" in contents


def test_macro_run_logger_interrupts_and_uses_collision_suffix(tmp_path):
    existing = tmp_path / "Boss_Rush_Arin_04_07_13_42.log"
    existing.write_text("existing", encoding="utf-8")

    logger = MacroRunLogger(str(tmp_path))
    logger.start_session("Boss Rush", "Arin", started_at=datetime(2026, 4, 7, 13, 42))
    logger.start_iteration(started_at=datetime(2026, 4, 7, 13, 43))
    logger.log("Waiting for wave")
    logger.interrupt(3)
    path = logger.finalize()

    assert path == os.path.join(str(tmp_path), "Boss_Rush_Arin_04_07_13_42_2.log")
    contents = open(path, encoding="utf-8").read()
    assert "----MACRO INTERRUPTED----" in contents
    assert "---- MACRO SUMMARY ---" in contents
    assert "----MACRO ENDED-----" in contents


def test_macro_run_logger_lists_saved_logs_without_current_file(tmp_path):
    (tmp_path / "current_macro.log").write_text("running", encoding="utf-8")
    saved = tmp_path / "Boss_Rush_Arin_04_07_13_42.log"
    saved.write_text("Macro: Solo Raid\nTotal time: 2m 5s\n", encoding="utf-8")

    logs = MacroRunLogger(str(tmp_path)).list_saved_logs()

    assert len(logs) == 1
    assert logs[0].filename == "Boss_Rush_Arin_04_07_13_42.log"
    assert logs[0].gamemode == "Boss Rush"
    assert logs[0].map_name == "Arin"
    assert logs[0].macro_name == "Solo Raid"
    assert logs[0].status == "SUCCESS"
    assert logs[0].duration_label == "2m 5s"


def test_macro_run_logger_marks_interrupted_logs_distinctly(tmp_path):
    saved = tmp_path / "Boss_Rush_Arin_04_07_13_42.log"
    saved.write_text(
        "Macro: Solo Raid\n----MACRO INTERRUPTED----\nTotal time: 2m 5s\n",
        encoding="utf-8",
    )

    logs = MacroRunLogger(str(tmp_path)).list_saved_logs()

    assert logs[0].status == "INTERRUPTED"


def test_macro_run_logger_reuses_cached_saved_logs_when_directory_is_unchanged(tmp_path, monkeypatch):
    saved = tmp_path / "Boss_Rush_Arin_04_07_13_42.log"
    saved.write_text("done", encoding="utf-8")
    logger = MacroRunLogger(str(tmp_path))

    first = logger.list_saved_logs()
    assert len(first) == 1

    original_stat = os.stat

    def _guarded_stat(path, *args, **kwargs):
        if str(path) == str(saved):
            raise AssertionError("file stat should not run again while saved-log cache is valid")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(os, "stat", _guarded_stat)
    second = logger.list_saved_logs()

    assert len(second) == 1
    assert second[0].filename == first[0].filename
