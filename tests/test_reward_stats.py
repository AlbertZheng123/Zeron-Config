from macro_app.services.reward_stats import RewardStatsStore, normalize_reward_name


def test_reward_stats_store_defaults_to_zero(tmp_path):
    store = RewardStatsStore(tmp_path / "reward_stats.json")

    assert store.load() == {
        "Gems": 0,
        "Gold": 0,
        "Doggy Bones": 0,
        "Grenade Pins": 0,
        "Blood Swords": 0,
        "Green Essence Stones": 0,
        "Memoria Rerolls": 0,
        "Rainbow Essence Stones": 0,
        "Super Stat Chips": 0,
        "Trait Rerolls": 0,
    }


def test_reward_stats_store_adds_known_reward_aliases(tmp_path):
    store = RewardStatsStore(tmp_path / "reward_stats.json")

    totals = store.add_rewards(
        {
            "Doggy Bone": 3,
            "Grenade": 2,
            "Blood Sword": 1,
            "Green Essence": 4,
            "Gems": 30,
            "Memoria Reroll": 6,
            "Rainbow Essence Stone": 8,
            "Super Stat Chip": 10,
            "Trait Reroll": 12,
            "Shackled Memoria": 99,
        }
    )

    assert totals["Doggy Bones"] == 3
    assert totals["Grenade Pins"] == 2
    assert totals["Blood Swords"] == 1
    assert totals["Green Essence Stones"] == 4
    assert totals["Gems"] == 30
    assert totals["Memoria Rerolls"] == 6
    assert totals["Rainbow Essence Stones"] == 8
    assert totals["Super Stat Chips"] == 10
    assert totals["Trait Rerolls"] == 12
    assert totals["Shackled Memoria"] == 99

    totals = store.add_rewards({"doggy bones": 5, "Gold": 75})
    assert totals["Doggy Bones"] == 8
    assert totals["Gold"] == 75


def test_normalize_reward_name():
    assert normalize_reward_name("Doggy Bone") == "Doggy Bones"
    assert normalize_reward_name("grenade pins") == "Grenade Pins"
    assert normalize_reward_name("trait rr") == "Trait Rerolls"
    assert normalize_reward_name("unknown") == "unknown"
