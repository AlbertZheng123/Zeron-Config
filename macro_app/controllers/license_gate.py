"""License page controller."""

from __future__ import annotations

import os

from macro_app.constants import KEY_SAVE_PATH, PAGE_OVERLAY


class LicenseGateController:
    """Handle saved-key startup and the license page actions."""

    def __init__(self, window, state, navigation, valid_keys) -> None:
        self.window = window
        self.state = state
        self.navigation = navigation
        self.valid_keys = valid_keys

    def bind(self) -> None:
        self.window.licenseValidateButton.clicked.connect(self.validate_and_proceed)
        self.window.licenseKeyInput.returnPressed.connect(self.validate_and_proceed)

    def validate_and_proceed(self) -> None:
        entered_key = self.window.licenseKeyInput.text().strip()
        if entered_key in self.valid_keys:
            self.state.current_user_key = entered_key
            try:
                with open(KEY_SAVE_PATH, "w") as file:
                    file.write(entered_key)
            except Exception as exc:
                print(f"Could not save key: {exc}")
            self.window.licenseErrorLabel.setText("")
            self.navigation.go_to_page(PAGE_OVERLAY)
        else:
            self.window.licenseErrorLabel.setText("Invalid key. Please try again.")

    def check_saved_key(self) -> bool:
        try:
            if os.path.exists(KEY_SAVE_PATH):
                with open(KEY_SAVE_PATH, "r") as file:
                    saved_key = file.read().strip()
                if saved_key in self.valid_keys:
                    self.state.current_user_key = saved_key
                    print(f"[key] Loaded saved key: {saved_key[:8]}...")
                    return True
        except Exception as exc:
            print(f"[key] Error reading saved key: {exc}")
        return False
