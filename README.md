# Zeron Config

A macOS desktop app for creating, editing, and running macros for **Anime Vanguards** on Roblox. Build sequences of placements, upgrades, abilities, and waits in a visual editor, then save them by game mode and map.

Zeron Config combines recorded click positions with image detection and OCR so macros can wait for game events such as a wave starting, a wave completing, or reaching a yen target.

## Features

- **Visual macro editor** — configure up to six unit slots, record placement positions, and edit your sequence as step cards.
- **Setup and loop steps** — run preparation once when starting a macro, then repeat your main sequence.
- **Unit actions** — place, upgrade by count or with auto/max modes, sell, and change targeting priority.
- **Abilities** — unit-specific main abilities, auto ability, Ainz Arcane and Caloric Stone, and Skele King's Strings flow.
- **Flexible waits** — wait for seconds, game start, waves, wave completion, or a yen amount.
- **Mouse and keyboard steps** — add clicks, key presses, and timed key holds.
- **Replay controls** — loop endlessly or stop after completion, with an optional restart at a chosen wave.
- **Card selection** — configure Legend cards and Dungeon priorities, starter cards, and buff/debuff limits.
- **Odyssey options** — configure card and room priorities, character cards, shop handling, and Memoria selection.
- **Relative positioning** — translate clicks and detection regions relative to the Roblox window, including support for off-main-display capture on macOS.
- **Run history** — view logs, run counts, elapsed time, and detected reward totals.
- **Optional Discord notifications** — send selected run events, results, rewards, and screenshots to your own webhook.

Available actions depend on the selected unit, game mode, and current game UI. Game updates can require changes to detection templates or saved macros.

## Requirements

- **macOS** — the current runtime uses macOS window, input, and screen-capture APIs. The pinned Apple Silicon OCR wheel requires macOS 14 or later. Windows and Linux are not supported by these instructions.
- Roblox with Anime Vanguards running in a window.
- **Python 3.11** for the source setup below, matching the project's current packaging environment.
- Screen capture and input permissions for the app or process running it.

## Install and launch

Download or clone this repository, then open Terminal in its root folder—the folder containing `macro_app_main.py`.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python macro_app_main.py
```

For later launches:

```bash
source .venv/bin/activate
python macro_app_main.py
```

Keep `references/`, `ui_references/`, `map_images/`, and `macros/` alongside the source files. They contain detection templates, interface assets, and bundled macro content used by the app.

### macOS permissions

In **System Settings → Privacy & Security**, grant access when prompted:

| Permission | Used for |
| --- | --- |
| Screen Recording / Screen & System Audio Recording | Reading waves, yen, cards, results, and other game UI |
| Accessibility | Sending input and positioning the Roblox window |
| Input Monitoring | Global start/stop shortcuts and recording clicks |
| Automation | Window-resize fallback through System Events, if requested |

When running from source, the permission entry may be your terminal, IDE, or Python process. For a packaged build, grant access to Zeron Config. Restart the relevant process after changing permissions if capture or input still fails.

## Create your first macro

1. **Open Roblox and enter Anime Vanguards.** Use a windowed game. Entering Advanced Create attempts to resize Roblox to the layout used by the editor and detection templates.
2. **Choose a mode and map** on the Config page, then select **Create Macro**.
3. **Configure your units.** Match the editor's unit slots to your in-game hotbar so placement and ability steps use the intended units.
4. **Add loop steps.** For a placement, choose a unit, select **Record Click**, then left-click its intended position in Roblox. Select **Add Place Step** to add the action to the sequence. Add upgrades, abilities, and waits as needed.
5. **Add setup steps if needed.** Use the Setup section for actions that should run once when you start the macro. Put actions needed every replay in the Loop section.
6. **Configure Settings.** Choose **Stop After Completion** for an initial test. Adjust timing and enable the detection or card-selection options your macro needs.
7. **Select Save Macro**, then start using the button or **Ctrl+S**. Watch the first run and stop it if positions or timing need adjustment.

**The runner uses the saved JSON file. Save your edits before starting or restarting a macro.**

Recording a click captures a position; it does not record an entire gameplay session. Add each action you want the macro to perform.

### Example sequence

A simple Loop sequence could look like this:

1. Wait for game start.
2. Wait until you have enough yen for your first unit.
3. Place the unit at a recorded position.
4. Wait for the desired wave or yen target.
5. Upgrade the placement.
6. Use an ability or add further placements and upgrades.

Tune the sequence for your units, costs, map, and camera view. A macro created with a different layout or loadout may need new coordinates and waits.

## Start and stop

| Action | Shortcut |
| --- | --- |
| Start the saved macro from the editor | **Ctrl+S** |
| Stop the macro | **Ctrl+P** |
| Alternate stop shortcut | **'** (apostrophe) |

These are global shortcuts intended to work while Roblox has focus. Use **Control**, not Command. Start and Stop buttons are also available in the editor.

## Macro settings

Open **Settings inside Advanced Create** to configure each macro.

| Setting | What it does |
| --- | --- |
| Loop Endlessly / Stop After Completion | Choose whether to replay or finish after one run |
| Wait between clicks, key presses, and steps | Adjust action timing for your game and connection |
| Check Placed | Verify placements and retry failed attempts; repeated failures stop the macro |
| Disable Chat | Perform the chat-disable clicks at macro startup |
| Anti-AFK | Enable the runtime's anti-idle behavior |
| Relative Positioning | Adjust action and detection coordinates to the live Roblox window |
| Reposition Camera on Start | Apply the startup camera-positioning routine |
| Force Restart Wave | Restart when the configured wave is detected |
| Legend / Dungeon card selection | Configure mode-specific card choices and priorities |
| Odyssey options | Configure automatic room, card, shop, and Memoria handling |

Force Restart Wave skips the usual end-of-run reward and webhook flow. With **Loop Endlessly**, the macro starts its next iteration. With **Stop After Completion**, it performs the restart clicks and stops.

The main shell's **Settings** tab has a separate **Debug Console Mode** toggle. Enable it when diagnosing detection issues, especially yen OCR polling.

## Saved macros and folders

On macOS, writable app data normally lives in:

```text
~/Library/Application Support/Zeron Config/
├── macros/
│   ├── story/
│   ├── raids/
│   ├── legend/
│   ├── bossRush/
│   ├── events/
│   └── dungeon/
└── runtime_output/
    ├── logs/
    ├── data/
    └── debug/
```

Macros are JSON files organized into map folders under each mode. Use **Open Folder** on the Config page to open the live macros directory.

To use a macro JSON someone has shared with you:

1. Open that directory and find the correct mode/map folder.
2. Copy the JSON file into it.
3. Return to the app and open the macro dropdown to refresh the list.
4. Select the macro and check its units, settings, and positions before running it.

Back up this directory to preserve your macros and stats. Bundled seed macros are merged into user data at startup without overwriting existing user files. You can override the data location with the `ZERON_CONFIG_HOME` environment variable.

The initial public version includes map folders but no ready-made gameplay macros. Create your own or import a local JSON file from someone you trust.

**Cloud/share-code importing is currently disabled.** Use local JSON files to exchange macros.

## Logs, stats, and Discord

Use **Logs** to inspect saved run output and **Stats** to view recorded runs, time, and detected rewards. Reward totals depend on successful end-of-run detection.

For Discord, open the webhook controls in **Integrations**, enter your own Discord webhook URL, and choose the events and content you want to send. Use the test control to check the connection, then enable notifications.

Treat your webhook URL as a password: do not put it in shared macros, screenshots, bug reports, or source files. When screenshot notifications are enabled, captured game images are sent to the configured Discord channel. Review the capture area before enabling them.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Start/stop hotkeys do not work | Check Input Monitoring permission, restart the app, and try the editor buttons |
| Clicks do not reach Roblox | Check Accessibility permission and that the intended Roblox window is open |
| Clicks land in the wrong place | Check window size, camera view, display scaling, and Relative Positioning; record the positions again if needed |
| Wave, yen, or image detection does not work | Check screen-capture permission and that the expected game UI is visible; enable Debug Console Mode for more detail |
| A wait appears stuck | Check its target and game state; game-start waits continue until detected or stopped |
| A pasted macro is missing | Check the live mode/map folder and reopen the macro dropdown |
| Changes do not appear during a run | Save the macro, stop it, and start again |
| Off-main-display or DeskPad capture fails | Enable Relative Positioning and check screen-capture permission; this path uses ScreenCaptureKit window capture |

When reporting a problem, include your macOS version, how you launched the app, display setup, mode/map, and relevant log lines. Remove webhook URLs, private identifiers, and personal information first.

## Project notes

Zeron Config is built with Python, PySide6, OpenCV, MSS, and RapidOCR. Detection templates and supported game flows may need updates when Anime Vanguards changes its interface.

This is an independent project and is not affiliated with Roblox or the developers of Anime Vanguards.

Original code and documentation are available under the [MIT license](LICENSE). See [third-party notices](THIRD_PARTY_NOTICES.md) for fonts and other assets, [CONTRIBUTING.md](CONTRIBUTING.md) for development instructions, and [SECURITY.md](SECURITY.md) for private vulnerability reporting.
