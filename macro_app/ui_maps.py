"""Authoritative widget registries for repeated UI groups."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OverlayModeWidgets:
    group: object
    image_frame: object
    mode_label: object
    active_label: object | None
    map_label: object
    macro_label: object
    map_combo: object
    macro_combo: object
    runs_label: object
    total_label: object
    time_label: object
    create_button: object
    import_button: object
    select_button: object


@dataclass(frozen=True)
class OverlayWidgets:
    page_title: object
    subtitle: object
    status_label: object
    webhook_toggle_button: object
    webhook_url_input: object
    webhook_test_button: object
    modes: dict[str, OverlayModeWidgets]


@dataclass(frozen=True)
class AdvancedWidgets:
    unit_inputs: dict[int, object]
    unit_saved_labels: dict[int, object]


def build_overlay_widgets(window) -> OverlayWidgets:
    modes = {
        "story": OverlayModeWidgets(
            group=window.storyModeGroup,
            image_frame=window.storyImageFrame,
            mode_label=window.storyModeLabel,
            active_label=getattr(window, "storyActiveLabel", None),
            map_label=window.storyMapLabel,
            macro_label=window.storyMacroLabel,
            map_combo=window.storyMapCombo,
            macro_combo=window.storyMacroCombo,
            runs_label=window.storyRunsLabel,
            total_label=window.storyTotalLabel,
            time_label=window.storyTimeLabel,
            create_button=window.storyCreateMacroButton,
            import_button=window.storyImportMacroButton,
            select_button=window.storySelectMacroButton,
        ),
        "raids": OverlayModeWidgets(
            group=window.raidsModeGroup,
            image_frame=window.raidsImageFrame,
            mode_label=window.raidsModeLabel,
            active_label=getattr(window, "raidsActiveLabel", None),
            map_label=window.raidsMapLabel,
            macro_label=window.raidsMacroLabel,
            map_combo=window.raidsMapCombo,
            macro_combo=window.raidsMacroCombo,
            runs_label=window.raidsRunsLabel,
            total_label=window.raidsTotalLabel,
            time_label=window.raidsTimeLabel,
            create_button=window.raidsCreateMacroButton,
            import_button=window.raidsImportMacroButton,
            select_button=window.raidsSelectMacroButton,
        ),
        "legend": OverlayModeWidgets(
            group=window.legendModeGroup,
            image_frame=window.legendImageFrame,
            mode_label=window.legendModeLabel,
            active_label=getattr(window, "legendActiveLabel", None),
            map_label=window.legendMapLabel,
            macro_label=window.legendMacroLabel,
            map_combo=window.legendMapCombo,
            macro_combo=window.legendMacroCombo,
            runs_label=window.legendRunsLabel,
            total_label=window.legendTotalLabel,
            time_label=window.legendTimeLabel,
            create_button=window.legendCreateMacroButton,
            import_button=window.legendImportMacroButton,
            select_button=window.legendSelectMacroButton,
        ),
        "bossRush": OverlayModeWidgets(
            group=window.bossRushModeGroup,
            image_frame=window.bossRushImageFrame,
            mode_label=window.bossRushModeLabel,
            active_label=getattr(window, "bossRushActiveLabel", None),
            map_label=window.bossRushMapLabel,
            macro_label=window.bossRushMacroLabel,
            map_combo=window.bossRushMapCombo,
            macro_combo=window.bossRushMacroCombo,
            runs_label=window.bossRushRunsLabel,
            total_label=window.bossRushTotalLabel,
            time_label=window.bossRushTimeLabel,
            create_button=window.bossRushCreateMacroButton,
            import_button=window.bossRushImportMacroButton,
            select_button=window.bossRushSelectMacroButton,
        ),
        "events": OverlayModeWidgets(
            group=window.eventsModeGroup,
            image_frame=window.eventsImageFrame,
            mode_label=window.eventsModeLabel,
            active_label=getattr(window, "eventsActiveLabel", None),
            map_label=window.eventsMapLabel,
            macro_label=window.eventsMacroLabel,
            map_combo=window.eventsMapCombo,
            macro_combo=window.eventsMacroCombo,
            runs_label=window.eventsRunsLabel,
            total_label=window.eventsTotalLabel,
            time_label=window.eventsTimeLabel,
            create_button=window.eventsCreateMacroButton,
            import_button=window.eventsImportMacroButton,
            select_button=window.eventsSelectMacroButton,
        ),
        "dungeon": OverlayModeWidgets(
            group=window.dungeonModeGroup,
            image_frame=window.dungeonImageFrame,
            mode_label=window.dungeonModeLabel,
            active_label=getattr(window, "dungeonActiveLabel", None),
            map_label=window.dungeonMapLabel,
            macro_label=window.dungeonMacroLabel,
            map_combo=window.dungeonMapCombo,
            macro_combo=window.dungeonMacroCombo,
            runs_label=window.dungeonRunsLabel,
            total_label=window.dungeonTotalLabel,
            time_label=window.dungeonTimeLabel,
            create_button=window.dungeonCreateMacroButton,
            import_button=window.dungeonImportMacroButton,
            select_button=window.dungeonSelectMacroButton,
        ),
    }
    return OverlayWidgets(
        page_title=window.overlayPageTitle,
        subtitle=window.overlaySubtitle,
        status_label=window.overlayStatusLabel,
        webhook_toggle_button=window.overlayWebhookToggleButton,
        webhook_url_input=window.overlayWebhookUrlInput,
        webhook_test_button=window.overlayWebhookTestButton,
        modes=modes,
    )


def build_advanced_widgets(window) -> AdvancedWidgets:
    return AdvancedWidgets(
        unit_inputs={
            1: window.unit1NameInput,
            2: window.unit2NameInput,
            3: window.unit3NameInput,
            4: window.unit4NameInput,
            5: window.unit5NameInput,
            6: window.unit6NameInput,
        },
        unit_saved_labels={
            1: window.unit1SavedLabel,
            2: window.unit2SavedLabel,
            3: window.unit3SavedLabel,
            4: window.unit4SavedLabel,
            5: window.unit5SavedLabel,
            6: window.unit6SavedLabel,
        },
    )
