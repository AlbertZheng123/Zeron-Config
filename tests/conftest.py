"""Keep tests independent of the developer's saved macros and display."""

import os
import tempfile


_test_home = tempfile.TemporaryDirectory(prefix="zeron-config-tests-")
os.environ["ZERON_CONFIG_HOME"] = _test_home.name
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
