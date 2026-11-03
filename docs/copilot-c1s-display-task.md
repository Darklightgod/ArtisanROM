# Copilot task: finish the c1s display-density investigation

Work on a new branch in this fork. First read
`docs/c1s-display-density-investigation.md` and the repository instructions.

The existing change disables unsupported dynamic resolution for c1s in this
older fork and tests its build-feature routing. Do not describe it as a tested
binary fix for the owner's ArtisanROM 4.0.2 installation.

## Required work

1. Establish the correct source baseline for Android 16 / S926BXXSHDZI1 and the
   owner's reported 4.0.2 ROM. Compare this fork's older `sixteen` with upstream
   `sixteen-qpr2`. Preserve the fork's c1s audio and 60 Hz changes. Do not
   overwrite/rebase shared branches automatically or drop those modifications.
2. Confirm c1s dynamic resolution remains disabled in generated floating
   features and Settings availability. The captured compositor advertises a
   single 1080 x 2400 / 60 Hz mode. Do not expose HD or WQHD through a donor
   SM-S926B identity. Keep normal screen zoom and accessibility scaling.
3. Trace the source and call path of the initial 213 dpi report versus
   `ro.sf.lcd_density=450` and the owner's saved 448 dpi. Distinguish initial
   device metadata from the UI's effective logical density. The first start
   after flashing has not been logged; do not claim its cause is proven.
4. Audit upstream's `display_ddiscaler_boot_fix` module before considering a
   backport. Confirm exact vendor library fingerprints and byte-pattern matches,
   scope it to supported targets, retain credits, and handle already-patched
   and unknown binaries deliberately. Do not patch unrelated instruction matches
   or invent universal offsets. If the exact binaries are unavailable, state
   what is missing and leave the binary fix unimplemented.
5. Where resolution selection is supported, ensure requesting an unavailable
   mode or selecting the active mode cannot repeatedly multiply density.
   Preserve density when no mode change succeeds. Use the actual source/smali
   implementation, not a stand-alone pseudocode model presented as integration.
6. Add/run tests for the code actually changed. Execute the host checks below,
   validate firmware/APK generation when dependencies are available, and report
   physical-device tests as pending unless they were actually performed.

## Host checks already available

```sh
bash -n target/c1s/config.sh
python3 -m unittest discover -s scripts/tests -p 'test_c1s_display_capabilities.py' -v
```

## Completion requirements

- Open a reviewable pull request with a narrow diff, source provenance, exact
  validation results, outstanding hardware checks, and rollback information.
- Do not publish raw bugreports or personal identifiers.
- Do not change SELinux, root behavior, authentication, unrelated audio, camera,
  encryption or SemanticSearchCore as part of this display task.
- Do not add boot loops that force 448 dpi or overwrite the user's chosen zoom.
- If upstream already contains a fix, document the installed-build mismatch
  instead of submitting a duplicate fix or claiming the user's device is fixed.
