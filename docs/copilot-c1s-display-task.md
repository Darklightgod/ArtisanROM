# Copilot task: finish the c1s display-density investigation

Work on a new branch in this fork. First read
`docs/c1s-display-density-investigation.md` and the repository instructions.

The existing change disables unsupported dynamic resolution for c1s in this
older fork and tests its build-feature routing. Do not describe it as a tested
binary fix for the owner's ArtisanROM 4.0.2 installation.

## Latest evidence to preserve

The actual Settings APK's zero-width path is now identified in the investigation.
A separate initial-density module produced owner-reported output:
`ro.sf.init.lcd_density=450`, physical size 1080x2400, physical density 450,
and existing override density 448. This is a positive device check for initial
density only. The Settings candidate has host assembly validation, but still
requires matching-source integration, platform signing and a device test.
The exact DDIScaler byte patterns do not match either supplied vendor library.

## Required work

1. Establish the correct source baseline for Android 16 / S926BXXSHDZI1 and the
   owner's reported 4.0.2 ROM. Compare this fork's older `sixteen` with upstream
   `sixteen-qpr2`. Preserve the fork's c1s audio and 60 Hz changes. Do not
   overwrite/rebase shared branches automatically or drop those modifications.
2. Confirm c1s dynamic resolution remains disabled in generated floating
   features and Settings availability. The captured compositor advertises a
   single 1080 x 2400 / 60 Hz mode. Do not expose HD or WQHD through a donor
   SM-S926B identity. Keep normal screen zoom and accessibility scaling.
3. Integrate the independently tested initial-density property into the matching
   c1s build before SurfaceFlinger starts. Confirm its base density remains 450;
   do not force the user's 448 override. Preserve the positive single-device
   size/density check, and obtain a new boot log and repeated restart checks.
   The very first post-flash setup has not been reproduced.
4. Audit upstream's `display_ddiscaler_boot_fix` module before considering a
   backport. Confirm exact vendor library fingerprints and byte-pattern matches,
   scope it to supported targets, retain credits, and handle already-patched
   and unknown binaries deliberately. Do not patch unrelated instruction matches
   or invent universal offsets. The supplied library hashes and absence of
   both original/replacement patterns are documented; the inspected patch
   cannot be directly applied to these binaries.
5. Integrate the inspected c1s Settings correction: mark the resolution
   preference unsupported and reject a zero mapped width in
   `SecDisplayUtils.setDisplayMode(Context,String,Display)` before writes.
   The candidate changes `if-gez v0` to `if-gtz v0`; the actual classes already
   passed a host assembly/reparse check. Match the chosen donor and keep the
   device-specific controller correction off supported multi-resolution targets.
   Preserve normal zoom and accessibility. Use the actual source/smali flow.
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
