#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise resolution capability routing and the later module override."""

from pathlib import Path
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
FEATURE_SCRIPT = ROOT / "unica/patches/product_feature/customize.sh"
STOCK_SCRIPT = ROOT / "unica/patches/stock_blobs/customize.sh"
MODULE_RUNNER = ROOT / "scripts/internal/apply_modules.sh"
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


def final_resolution_state(target):
    """Run the real module scheduler, feature section and full stock module.

    Firmware-copy and APK helpers only record calls. The floating-feature
    helper keeps mutable state so a later override is visible to the test.
    """
    source = FEATURE_SCRIPT.read_text()
    start = source.index(START)
    section = source[start:source.index(END, start)]
    helpers = r'''
record_call() { printf '%s' "$1" >> "$CALL_LOG"; shift; printf '\t%s' "$@" >> "$CALL_LOG"; printf '\n' >> "$CALL_LOG"; }
LOG_STEP_IN() { record_call MODULE "$*"; }
LOG_STEP_OUT() { :; }
LOGE() { printf '%s\n' "$*" >&2; }
ABORT() { LOGE "$*"; exit 1; }
GET_FINGERPRINT_SENSOR_TYPE() { printf '%s\n' ultrasonic; }
IS_VALID_PARTITION_NAME() {
    case "$1" in system|system_ext|vendor|product|odm) return 0;; *) return 1;; esac
}
SET_FLOATING_FEATURE_CONFIG() {
    record_call FLOAT "$@"
    if [ "$1" = SEC_FLOATING_FEATURE_COMMON_CONFIG_DYN_RESOLUTION_CONTROL ]; then
        if [ "$2" = --delete ]; then
            : > "$FLOAT_STATE"
        else
            printf '%s' "$2" > "$FLOAT_STATE"
        fi
    fi
}
GET_FLOATING_FEATURE_CONFIG() { cat "$FLOAT_STATE"; }
ADD_TO_WORK_DIR() { record_call ADD "$@"; }
DELETE_FROM_WORK_DIR() { record_call DELETE "$@"; }
APPLY_PATCH() { record_call PATCH "$@"; }
SET_PROP() { record_call PROP "$@"; }
'''
    harness = r'''
set -e
source "$1"
TARGET_OS_SINGLE_SYSTEM_IMAGE=essi
model="${TARGET_FIRMWARE%%/*}"
region="${TARGET_FIRMWARE#*/}"
region="${region%%/*}"
mkdir -p "$WORK_DIR/system/system/etc/permissions"
mkdir -p "$FW_DIR/${model}_${region}/system/system/etc/permissions"
source "$2" "$3"
'''
    with tempfile.TemporaryDirectory(prefix="c1s-final-feature-test-") as temporary:
        directory = Path(temporary)
        src = directory / "src"
        utils = src / "scripts/utils/module_utils.sh"
        utils.parent.mkdir(parents=True)
        utils.write_text(helpers)
        modules = directory / "modules"
        # Create in reverse order; apply_modules.sh must impose its real order.
        for name, code in (("stock_blobs", STOCK_SCRIPT.read_text()),
                           ("product_feature", section)):
            module = modules / name
            module.mkdir(parents=True)
            (module / "module.prop").write_text(f"name={name}\nauthor=regression-test\n")
            (module / "customize.sh").write_text(code)
        calls = directory / "calls.txt"
        calls.write_text("")
        state = directory / "floating-feature.txt"
        state.write_text("WQHD,FHD,HD")
        environment = dict(os.environ, SRC_DIR=str(src),
                           WORK_DIR=str(directory / "work"),
                           FW_DIR=str(directory / "firmware"),
                           FLOAT_STATE=str(state), CALL_LOG=str(calls))
        subprocess.run(
            ["bash", "-c", harness, "final-feature-test",
             str(ROOT / "target" / target / "config.sh"),
             str(MODULE_RUNNER), str(modules)],
            env=environment, check=True, capture_output=True, text=True,
        )
        return state.read_text(), [line.split("\t") for line in calls.read_text().splitlines()]


class ResolutionCapabilityTests(unittest.TestCase):
    def assert_real_module_order(self, calls):
        order = [call[1] for call in calls if call[0] == "MODULE"]
        self.assertEqual(len(order), 2, order)
        self.assertIn('"product_feature"', order[0])
        self.assertIn('"stock_blobs"', order[1])

    def test_c1s_final_feature_stays_absent_after_stock_blobs(self):
        value, calls = final_resolution_state("c1s")
        self.assert_real_module_order(calls)
        self.assertEqual(value, "", "A later module restored unsupported resolutions")

    def test_c2s_final_feature_retains_supported_resolutions(self):
        value, calls = final_resolution_state("c2s")
        self.assert_real_module_order(calls)
        self.assertEqual(value, "WQHD,FHD,HD")

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
