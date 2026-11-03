# ArtisanROM contribution guidance

This is a Samsung firmware port using the UN1CA Bash build system and smali
patches. It is not a standalone Android app or a complete AOSP source tree.

- Read the target configuration and existing patch flow before editing it.
- Preserve existing device features and the fork's c1s audio and 60 Hz changes.
- Treat c1s (Galaxy Note20, SM-N980F / SM-N981B) separately from c2s (Ultra).
  The framework's spoofed SM-S926B identity is not the physical device identity.
- For the display-density investigation, read
  `docs/c1s-display-density-investigation.md` and
  `docs/copilot-c1s-display-task.md` before proposing a fix.
- Distinguish reported behavior, log observations, hypotheses, and verified
  code behavior. Do not claim a flashed-device fix from a source-only check.
- Keep raw bugreports, serial numbers, account information and Wi-Fi/network
  identifiers out of commits and issue bodies. Use the sanitized evidence.
- Do not add boot-time DPI-reset loops, overwrite a user's zoom setting,
  disable SELinux, replace unrelated graphics libraries, or remove AI services
  to mask these display symptoms.
- Run `bash -n target/c1s/config.sh` and
  `python3 -m unittest discover -s scripts/tests -p 'test_c1s_display_capabilities.py' -v`
  for the configuration change. These are host-side checks; a firmware build,
  APK/smali validation and physical-device verification are separate steps.
- The fork's `sixteen` branch and upstream's `sixteen-qpr2` branch are distinct
  source baselines. Check provenance before copying patches or changing a base.
