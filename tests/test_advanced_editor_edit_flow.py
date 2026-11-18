import os
import sys
from types import SimpleNamespace


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from macro_app.controllers import advanced_editor as advanced_editor_module
from macro_app.controllers.advanced_editor import AdvancedEditorController


class _TextValue:
    def __init__(self, value):
        self._value = value

    def text(self):
        return self._value


class _BoolValue:
    def __init__(self, value):
        self._value = value

    def isChecked(self):
        return self._value


class _ComboValue:
    def __init__(self, *, current_index=0, current_data=None, current_text=""):
        self._current_index = current_index
        self._current_data = current_data
        self._current_text = current_text

    def currentIndex(self):
        return self._current_index

    def currentData(self):
        return self._current_data

    def currentText(self):
        return self._current_text


def test_active_order_key_maps_loop_and_setup_sections():
    fake_loop = SimpleNamespace(state=SimpleNamespace(editor=SimpleNamespace(step_section="loop")))
    fake_setup = SimpleNamespace(state=SimpleNamespace(editor=SimpleNamespace(step_section="setup")))

    assert AdvancedEditorController._active_order_key(fake_loop) == "order"
    assert AdvancedEditorController._active_order_key(fake_setup) == "setup_order"


def test_add_place_step_uses_macro_order_key_for_loop_edits(monkeypatch):
    captured = {}

    def fake_retarget_place_instruction(macro, **kwargs):
        captured.update(kwargs)
        return {"cmd": "place", "slot": kwargs["new_slot"], "placement_index": 0}

    monkeypatch.setattr(advanced_editor_module, "retarget_place_instruction", fake_retarget_place_instruction)

    finalized = {}
    fake = SimpleNamespace(
        window=SimpleNamespace(
            placeUnitCombo=_ComboValue(current_index=1),
            placeXInput=_TextValue("123"),
            placeYInput=_TextValue("456"),
            placeUntilEmptyCheckbox=_BoolValue(False),
            statusbar=SimpleNamespace(showMessage=lambda _msg: None),
        ),
        state=SimpleNamespace(
            editor=SimpleNamespace(
                editing=SimpleNamespace(active=True, step_type="place", row=object()),
                step_section="loop",
            )
        ),
        current_macro={"units": {1: {"placements": []}, 2: {"placements": []}, 3: {"placements": []}, 4: {"placements": []}, 5: {"placements": []}, 6: {"placements": []}}},
        _widget_to_order_index=lambda _row: 4,
        _active_order_key=lambda: "order",
        _finalize_advanced_edit=lambda instruction, rebuild_rows=False: finalized.update(
            {"instruction": instruction, "rebuild_rows": rebuild_rows}
        ),
        update_placement_counter_label=lambda: None,
        refresh_upgrade_placement_combo=lambda: None,
        _append_instruction=lambda _instruction: None,
    )

    AdvancedEditorController.add_place_step(fake)

    assert captured["order_key"] == "order"
    assert captured["order_index"] == 4
    assert finalized["instruction"] == {"cmd": "place", "slot": 2, "placement_index": 0}
    assert finalized["rebuild_rows"] is True


def test_add_place_step_uses_macro_order_key_for_setup_edits(monkeypatch):
    captured = {}

    def fake_retarget_place_instruction(macro, **kwargs):
        captured.update(kwargs)
        return {"cmd": "place", "slot": kwargs["new_slot"], "placement_index": 0}

    monkeypatch.setattr(advanced_editor_module, "retarget_place_instruction", fake_retarget_place_instruction)

    fake = SimpleNamespace(
        window=SimpleNamespace(
            placeUnitCombo=_ComboValue(current_index=0),
            placeXInput=_TextValue("10"),
            placeYInput=_TextValue("20"),
            placeUntilEmptyCheckbox=_BoolValue(True),
            statusbar=SimpleNamespace(showMessage=lambda _msg: None),
        ),
        state=SimpleNamespace(
            editor=SimpleNamespace(
                editing=SimpleNamespace(active=True, step_type="place", row=object()),
                step_section="setup",
            )
        ),
        current_macro={"units": {1: {"placements": []}, 2: {"placements": []}, 3: {"placements": []}, 4: {"placements": []}, 5: {"placements": []}, 6: {"placements": []}}},
        _widget_to_order_index=lambda _row: 1,
        _active_order_key=lambda: "setup_order",
        _finalize_advanced_edit=lambda *_args, **_kwargs: None,
        update_placement_counter_label=lambda: None,
        refresh_upgrade_placement_combo=lambda: None,
        _append_instruction=lambda _instruction: None,
    )

    AdvancedEditorController.add_place_step(fake)

    assert captured["order_key"] == "setup_order"


def test_add_upgrade_step_uses_current_selected_unit_when_editing():
    captured = {}
    fake = SimpleNamespace(
        window=SimpleNamespace(
            upgradeUnitCombo=_ComboValue(current_data=3),
            autoUpgradeCheckBox=_BoolValue(False),
            maxUpgradeCheckBox=_BoolValue(False),
            upgradePlacementCombo=_ComboValue(current_text="#2 (300, 400)"),
            upgradeCountInput=_TextValue("4"),
            upgradeNoPlacementsLabel=SimpleNamespace(setText=lambda _text: None),
            statusbar=SimpleNamespace(showMessage=lambda _msg: None),
        ),
        state=SimpleNamespace(
            editor=SimpleNamespace(
                editing=SimpleNamespace(active=True, step_type="upgrade"),
            )
        ),
        _append_instruction=lambda instruction: captured.update({"instruction": instruction}),
    )

    AdvancedEditorController.add_upgrade_step(fake)

    assert captured["instruction"] == {
        "cmd": "upgrade",
        "slot": 3,
        "placement_index": 2,
        "mode": "manual",
        "count": 4,
    }
