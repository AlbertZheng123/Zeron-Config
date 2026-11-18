import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import supabase_client


def test_init_cache_collapses_legacy_user_key_entries(tmp_path, monkeypatch):
    cache_path = tmp_path / "run_stats_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "KEY1|story|Shibuya": {"total_runs": 2, "total_time": 120.0},
                "KEY2|story|Shibuya": {"total_runs": 1, "total_time": 30.0},
                "story|Namek": {"total_runs": 4, "total_time": 80.0},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(supabase_client, "_CACHE_PATH", str(cache_path))
    monkeypatch.setattr(supabase_client, "_stats_cache", {})

    supabase_client.init_cache()

    assert supabase_client.get_total_runs(None, "story", "Shibuya") == 3
    assert supabase_client.get_total_time(None, "story", "Shibuya") == 150.0
    assert supabase_client.get_total_runs(None, "story", "Namek") == 4


def test_record_run_updates_local_cache_without_remote_sync(tmp_path, monkeypatch):
    cache_path = tmp_path / "run_stats_cache.json"
    monkeypatch.setattr(supabase_client, "_CACHE_PATH", str(cache_path))
    monkeypatch.setattr(supabase_client, "_stats_cache", {})

    supabase_client.record_run(None, "Farm", "story", "Shibuya", 1, 42.4)
    supabase_client.record_run(None, "Farm", "story", "Shibuya", 2, 30.2)

    assert supabase_client.get_total_runs(None, "story", "Shibuya") == 2
    assert supabase_client.get_total_time(None, "story", "Shibuya") == 72.6

    saved = json.loads(cache_path.read_text(encoding="utf-8"))
    assert saved["story|Shibuya"]["total_runs"] == 2
