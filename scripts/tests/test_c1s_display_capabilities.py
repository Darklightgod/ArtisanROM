#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the actual resolution build gate without firmware or device writes."""

from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
FEATURE_SCRIPT = ROOT / "unica/patches/product_feature/customize.sh"
START = "# SEC_PRODUCT_FEATURE_COMMON_CONFIG_DYN_RESOLUTION_CONTROL\n"
END = "# SEC_PRODUCT_FEATURE_COMMON_SUPPORT_EMBEDDED_SIM\n"


def resolution_build_calls(target):
    source = FEATURE_SCRIPT.read_text()
    start = source.index(START)
    section = source[start:source.index(END, start)]
    harness = r'''
set -e
source "$1"
TARGET_OS_SINGLE_SYSTEM_IMAGE=essi
MODPATH=/product-feature
record_call() { printf '%s' "$1"; shift; printf '\t%s' "$@"; printf '\n'; }
GET_FINGERPRINT_SENSOR_TYPE() { printf '%s\n' ultrasonic; }
SET_FLOATING_FEATURE_CONFIG() { record_call FLOAT "$@"; }
ADD_TO_WORK_DIR() { record_call ADD "$@"; }
APPLY_PATCH() { record_call PATCH "$@"; }
ABORT() { printf '%s\n' "$*" >&2; exit 1; }
source "$2"
'''
    with tempfile.TemporaryDirectory(prefix="c1s-resolution-test-") as temporary:
        section_path = Path(temporary) / "resolution-section.sh"
        section_path.write_text(section)
        result = subprocess.run(
            ["bash", "-c", harness, "resolution-build-test",
             str(ROOT / "target" / target / "config.sh"), str(section_path)],
            check=True, capture_output=True, text=True,
        )
    return [line.split("\t") for line in result.stdout.splitlines()]


class ResolutionCapabilityTests(unittest.TestCase):
    def test_c1s_removes_multi_resolution_feature_and_avoids_donor_stack(self):
        calls = resolution_build_calls("c1s")
        self.assertIn(
            ["FLOAT", "SEC_FLOATING_FEATURE_COMMON_CONFIG_DYN_RESOLUTION_CONTROL",
             "--delete"], calls,
        )
        self.assertFalse(any(call[0] == "ADD" for call in calls), calls)
        patches = {call[2] for call in calls if call[0] == "PATCH"}
        self.assertEqual(patches, {
            "system/framework/framework.jar",
            "system/framework/gamemanager.jar",
            "priv-app/SystemUI/SystemUI.apk",
        })

    def test_c2s_retains_existing_supported_resolution_path(self):
        calls = resolution_build_calls("c2s")
        self.assertIn(
            ["FLOAT", "SEC_FLOATING_FEATURE_COMMON_CONFIG_DYN_RESOLUTION_CONTROL",
             "WQHD,FHD,HD"], calls,
        )
        added_paths = {call[3] for call in calls if call[0] == "ADD"}
        self.assertIn("system/bin/surfaceflinger", added_paths)
        self.assertIn("system/bin/bootanimation", added_paths)
        self.assertFalse(any(call[0] == "PATCH" for call in calls), calls)


if __name__ == "__main__":
    unittest.main()
