<!-- SPDX-License-Identifier: MIT -->
# LG G8 notes

## 2026-11-02: shared initramfs M1

The shared script ran as PID 1, ACM capture and two fresh USB SSH connections
passed, and the phone automatically returned to its existing Android slot B.
Full USB observation and both boot-slot hashes passed. The compiled board
compatible is `lge,alphalm`; an earlier `lg,alphalm` typo was stopped by the
guard and is retained as a failed comparison. Image generation now checks
the actual compiled DTB. Arch, Hyprland, real UFS enumeration and actual
display/touch in this userspace remain open; see [BRINGUP-M1.md](BRINGUP-M1.md).

## 2026-11-02: target and refresh-rate baseline

The owner selected OmaMobile as the final userspace. Existing kernel
bring-up is being connected to the shared Arch Linux ARM rootfs and
Hyprland; neither has passed a phone boot yet.

The LG SW43410 driver currently exposes one 1440 x 3120 mode at 60 Hz.
Stock Android reports the same resolution and approximately 60 Hz, with
no alternative refresh rates. Mode switching, scanout-rate measurement
and lower-power refresh configurations remain untested. Retain 60 Hz for
the first shared-userspace boot.

Current kernel evidence is on `7.3.0-lgg8`; detailed acceptance and the
remaining stages are in [BRINGUP-M1.md](BRINGUP-M1.md). The descriptor is
deliberately RAM-only, with no writable partitions and no installer path.

## 2026-11-02: kernel WLAN registration

The kernel RAM experiment now registers a WLAN PHY and network interface.
An A/B/A comparison identified a QRTR service announcement dropped before
the local HELLO; the retry fix passed separately without temporary
QRTR/PD logging, including USB observation and Android recovery. See
[the kernel checkpoint](https://github.com/LIghtJUNction/linux-lgg8/commit/81b24bcbeb5a03aeb589bef7682d2efec5f72252).

The generic LG kernel tree still disables Wi-Fi by default; the experiment
uses an explicit supply override and verified private factory inputs.
Scanning, association and data have not been tested. Ath10k falls back
to a random MAC, so factory-address provisioning remains open. None of
these diagnostic-userspace results counts as an OmaMobile phone boot.
