# Note20 c1s: resolution controls change density without changing display mode

Investigation date: 2026-11-03, Europe/Berlin.
Status: source configuration correction with host-side regression coverage.
A separate initial-density module passed the owner's reported device check.
The installed-ROM Settings correction still needs integration, signing and
physical-device validation; no complete rebuilt ROM is included.

## Device and source provenance

| Item | Observed value |
| --- | --- |
| Physical device, owner supplied | Galaxy Note20 SM-N980F/DS |
| Target codename / SoC | c1s / Exynos 990 |
| Reported installed ROM | ArtisanROM 4.0.2 |
| Framework identity | SM-S926B, Android 16 / SDK 36 |
| System build | BP4A.251205.006 / S926BXXSHDZI1 |
| Vendor platform version | Android 11 / SDK 30 |
| Kernel | 4.19.325-cip119-st3-ArtisanKRNL-v4.0.1 |
| Fork baseline for this change | Darklightgod/ArtisanROM, sixteen, 0b4f5debc24b9ea891aec20a23426238db355065 |
| Current upstream reference inspected | ArtisanROM/ArtisanROM, sixteen-qpr2, abeb2cac4ff80fdf6f0748b7422d6b4d4b307323 |

The fork baseline still identifies its source firmware as S22 Ultra in
`unica/configs/essi.sh`. It is not a verified source match for the owner's
installed S24+ based ROM. This is a narrow correction to the existing fork,
not proof that its tree can reproduce the supplied 4.0.2 image.

## Observed resolution-menu behavior

The owner supplied screenshots and three bugreports captured on
2026-11-02 at 22:56:19 and 2026-11-03 at 00:22:01 and 00:29:47.
The two newer reports contain overlapping history; do not count shared events
twice. Raw files and screenshots are deliberately excluded from this repository.

The Settings screen can become extremely small and switch to two columns while
the resolution summary continues to report FHD+ (2400 x 1080). The captured
physical mode and application bounds remain 1080 x 2400, approximately 60 Hz.

| Local event time, 2026-11-03 | Logical density | Global width reported in dp |
| --- | ---: | ---: |
| 00:17:40.382 | 298 | 580 |
| 00:17:49.847 | 198 | 873 |
| 00:18:07.049 | 132 | 1309 |
| 00:18:52.041 | 176 | 982 |
| 00:18:59.021 | 234 | 738 |
| 00:19:06.547 | 312 | 554 |
| 00:19:24.693 | 416 | 415 |
| 00:19:49.347 | 554 | 312 |
| 00:20:10.242 | 142 | 1217 |
| 00:20:16.201 | 189 | 914 |
| 00:20:22.012 | 252 | 686 |
| 00:20:48.351 | 336 | 514 |
| 00:21:05.256 | 448 | 386 |

Sanitized excerpts from the 00:22:01 report, near original lines 290595-290790:

```text
SecDisplayUtils: setUserPreferredDisplayMode: width=1080, height=2400, fps=60.000004
SecDisplayUtils: currentDensity = 198
SecDisplayUtils: defaultDensity = 213
SecDisplayUtils: currentWidth = 1080
SecDisplayUtils: basePx : 3   targetPx : 2
SecDisplayUtils: convertRatio : 0.6666667
SecDisplayUtils: applyForcedDisplayDensity: density=132
```

The caller of the density update is
`com.samsung.android.settings.display.ScreenResolutionFragment$2.onClick`,
through `SecDisplayUtils.setDisplayMode` and
`WindowManagerService.setForcedDisplaySizeDensityWithInfo`.
Other transitions log `basePx : 3 targetPx : 4` and `convertRatio : 1.3333334`.
Settings repeatedly reads `width = 1080 screenResolution = 1` and also logs
`SecDisplayUtils: No support`.

This establishes density changes initiated by the resolution screen without an
observed mode change. Repeated updates amplify the effect. The later direct APK
inspection below identifies the zero-width code path; the complete installed
ROM's source revision still requires matching.

## Boot observation: distinguish metadata from the visible UI

The owner reports that the first start after flashing also has an unusually
small UI. That first-start sequence is not captured in the supplied reports.
The older report captures a later boot with a saved density override:

```text
22:55:18.844  DisplayNode: density=213, bounds=811.2676 x 1802.8169 dp
22:55:19.240  DisplayNode: density=448, bounds=385.7143 x 857.1429 dp
WindowManager: init=1080x2400 213dpi base=1080x2400 448dpi
ro.sf.lcd_density=450
SettingsEntry: mForcedDensity=448
```

These are different stages and sources of density data. Initial 213 dpi
metadata alone does not prove a visible tablet UI, a faulty hardware density,
or an automatic resolution switch. A missing first-start override is a
hypothesis. The native mode stays 1080 x 2400 in the captured sequence.

## Follow-up inspection of the installed files

The owner subsequently supplied the actual Settings APK, floating features,
32/64-bit vendor display libraries, early boot logs and property outputs.
The raw inputs are not committed.

### Settings code path and candidate correction

Inspected package: `com.android.settings`, version name 16 / version code 36,
shared UID `android.uid.system`.
APK SHA-256:
`41a68fa18f360576a3e55100021dc7e2b6f22dfde9f3c39c3a06b71537458375`.

The affected Samsung classes are in `classes5.dex` in this APK:

1. `ScreenResolutionPreferenceController.getAvailabilityStatus()I` returns
   AVAILABLE (0) outside desktop windowing without testing physical resolution
   capabilities.
2. `SecDisplayUtils.initSupportedResolutionData(Display)` logs `No support`
   unless there are exactly three distinct physical sizes. In the unsupported
   case it leaves the initially zero HD/FHD/WQHD width fields unchanged.
3. `SecDisplayUtils.setDisplayMode(Context,String,Display)` maps the selection
   to a zero width, falls back to the current display mode, and then accepts
   zero through an `if-gez v0` guard. It can consequently reach the forced-size,
   preferred-mode and selection-dependent density updates.

A separate c1s-only candidate replaces the controller result with
UNSUPPORTED_ON_DEVICE (3) and changes this width guard from `if-gez v0` to
`if-gtz v0`. The installed APK's own BasePreferenceController confirms that
status 3 means unsupported. Normal zoom and shared density helpers are not
changed.

This candidate was applied to the two actual decoded classes, assembled with
smali 2.5.2 and parsed again. Both DEX checksums were valid. Exactly two methods
changed; the other 81 methods in these two classes retained identical
instructions. The width guard changes one instruction with unchanged operands
and branch target. Six host tests covered the installer, real-class patching,
idempotence and rejection of unknown donors/targets.

These checks are separate from this branch's older configuration tests.
The APK candidate is not integrated into this older S22 build, and has not
been installed or tested on the phone. A complete compatible ROM build and
platform signing remain required.

### XML and vendor-library applicability

The supplied floating-feature XML already lacks
`SEC_FLOATING_FEATURE_COMMON_CONFIG_DYN_RESOLUTION_CONTROL`, so deleting that
entry alone cannot fix the installed Settings availability. Its HFR entries
still include default 120, mode 3 and rates up to 120; treat that as a separate
c1s configuration issue rather than proof the panel runs at 120 Hz.

| Vendor input | SHA-256 |
| --- | --- |
| 32-bit libexynosdisplay.so | `5a3279b615291ec9690a4e286a7ac5699ad2893fd9f67b1cb3cf2c963f0c5f2a` |
| 64-bit libexynosdisplay.so | `6477a33da2aca40a902cb1e8b22f988791da991bfb7b96129fd23801e646d2be` |

Neither library contains the original or replacement signatures from the
inspected upstream DDIScaler module. That exact patch is not directly
applicable, and absence alone does not classify the binaries as unpatched.
No vendor binary was changed.

## Initial-density device check reported on 2026-11-03

Before the test, both boot logs contained:

```text
SurfaceFlinger: ro.sf.init.lcd_density must be defined as a build property
```

The owner read an empty `ro.sf.init.lcd_density` and
`ro.sf.lcd_density=450`, with the same result in local and root shells.

The separate KernelSU test module `c1s_init_density_test`, version 0.1.0,
adds only `ro.sf.init.lcd_density=450` during regular early module-property
processing. It does not install a Settings APK, change vendor libraries,
adjust the density override, or install SELinux rules. After the requested
module/reboot test procedure, the owner reported these command outputs:

```text
getprop ro.sf.init.lcd_density
450

wm size
Physical size: 1080x2400

wm density
Physical density: 450
Override density: 448
```

This is positive device evidence that WindowManager now reports an initial
density of 450 rather than the previously captured 213, while the existing
448 user override and native dimensions are retained. It does not establish
that the separate resolution-menu bug is fixed or reproduce the very first
post-flash setup. A new boot log, repeated restarts and broader UI checks
have not yet been supplied.

Rollback for this property test is to disable/remove that module and reboot.
For a permanent c1s build fix, initialize the compositor property before
SurfaceFlinger using the verified base density, without forcing 448 or
repeatedly resetting the user's zoom. Preserve that distinction when reporting
hardware validation.

## Source correction in this branch

In the fork baseline, `target/c1s/config.sh` enables
`TARGET_COMMON_SUPPORT_DYN_RESOLUTION_CONTROL=true`. The existing
`unica/patches/product_feature/customize.sh` consequently advertises
`WQHD,FHD,HD` and selects donor multi-resolution graphics/media files.

The change sets the c1s capability to `false`, matching the current upstream
c1s capability. In this older fork, the existing disabled-capability branch
deletes the dynamic-resolution floating feature and selects its existing
framework, game-manager and edge-lighting compatibility patches instead of
installing the donor multi-resolution files. No new binary/smali offsets are
invented. Screen zoom and font scaling remain available through their ordinary
controls. Existing c1s audio and 60 Hz changes are retained.

Host tests execute that actual resolution feature section with the real c1s
and c2s configurations and record its build-helper calls. Additional checks run
the actual `apply_modules.sh` scheduler over that section and the complete
`stock_blobs/customize.sh`, using controlled firmware helpers and mutable
floating-feature state. They check the value after both modules in the real
sorted order. They do not assemble the patched APKs or build a complete ROM.

## Codex review follow-up: later stock-blobs override

The review of commit `2abbb46d93c25eeaefee75f7edc3fe00dc702999` identified
an incomplete build gate in this older fork. Its `stock_blobs` module wrote
`WQHD,FHD,HD` for every Exynos 990 target after `product_feature` had deleted
the capability for c1s. The original section-only tests missed that later write.

The new test reproduced the finding before the fix: the c1s final-state check
failed with `WQHD,FHD,HD`, while the other three checks passed. The later
assignment is now gated on `TARGET_COMMON_SUPPORT_DYN_RESOLUTION_CONTROL`
as well as the platform. All four checks then passed: c1s stays disabled after
`stock_blobs`, while c2s retains its supported resolution list and donor path.

This corrects the reviewed fork build path. The supplied installed 4.0.2 XML
already lacked this entry, so this older-source override must not be claimed
as the proven cause of that installed ROM's separate Settings bug.

## Existing upstream work and remaining investigation

The inspected upstream `CHANGELOG.md` already lists incompatible-model
resolution UI handling in 4.0.0 and a DDIScaler boot-shrinking fix in 4.0.2.
Do not submit this c1s configuration value upstream as a new discovery: it is
already `false` there.

Upstream contains
`unica/patches/display_ddiscaler_boot_fix/customize.sh`. It patches exact
instruction byte patterns in the 32-bit and 64-bit vendor
`libexynosdisplay.so` libraries. This module is absent from the fork baseline.
Its presence in a changelog does not prove the installed libraries contain it,
and screen-area shrinking and density scaling must not be assumed identical.
Before any backport, check the precise source version, module order, target
selection, library hashes and exact original/already-patched patterns.

The separate `SemanticSearchCore` (`com.samsung.android.ssco`) native crashes
are outside this display change. Six distinct SIGSEGV events are visible;
an NPU-model initialization timeout precedes one captured crash. The first
events predate the resolution-menu experiment. Do not disable that service as
part of this display fix.

## Remaining integration and physical-device acceptance checks

1. Build against the chosen and documented firmware source and validate all
   smali patch applications and rebuilt APKs. Record build/commit identifiers.
2. On c1s, verify native 1080 x 2400 / 60 Hz and absence of unsupported HD/WQHD
   controls. A deep link must not alter density through an unsupported path.
3. Check ordinary screen zoom, font size and accessibility settings still work.
4. Extend the initial-density device check above with a fresh boot log,
   repeated normal restarts, and zoom/accessibility checks. The single reported
   size/density check passed; the remaining checks are pending. Do not wipe a
   daily-use device for this test.
5. Test a genuinely fresh setup only on an authorized test installation; do not
   infer first-boot behavior from initial DisplayDeviceInfo metadata.
6. Confirm c2s and other supported targets retain their resolution controls.

The configuration change does not repair a running installation automatically
and does not migrate an existing bad density override. The captured normal
448 dpi is an owner-specific observed setting, not a universal factory value.

## References

- [Upstream c1s configuration](https://github.com/ArtisanROM/ArtisanROM/blob/abeb2cac4ff80fdf6f0748b7422d6b4d4b307323/target/c1s/config.sh)
- [Upstream DDIScaler module](https://github.com/ArtisanROM/ArtisanROM/blob/abeb2cac4ff80fdf6f0748b7422d6b4d4b307323/unica/patches/display_ddiscaler_boot_fix/customize.sh)
- [Upstream changelog](https://github.com/ArtisanROM/ArtisanROM/blob/abeb2cac4ff80fdf6f0748b7422d6b4d4b307323/CHANGELOG.md)
- [Android adaptive layout documentation](https://developer.android.com/develop/ui/views/layout/responsive-adaptive-design-with-views)
