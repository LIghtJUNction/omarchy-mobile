<!-- SPDX-License-Identifier: MIT -->
# LG G8 (alphalm): first light and OmaMobile integration

Status, 2026-11-02: shared-initramfs M1 passed on `lgg8/ram-bringup`.
The board has prior mainline RAM-boot evidence; OmaMobile's Arch root and
Hyprland session have **not** run on this handset. No persistent install
or generic installer support is claimed.

## Goal

Run the shared OmaMobile userspace with LG G8 device support, then submit
the device files and the required kernel changes to their respective
repositories after device acceptance. The first gate is a recoverable
RAM session with USB networking, SSH, display and touch.

## Verified facts and sources

`K/` is the LG G8 kernel source, currently maintained in
[linux-lgg8](https://github.com/LIghtJUNction/linux-lgg8), branch
`lgg8/modem-20261102`. `R/` means the owner's private stock captures;
captures, firmware and NV are outside this repository.

- [V] SM8150; root compatible `lge,alphalm`.
  Source: `K/arch/arm64/boot/dts/qcom/sm8150-lg-alphalm.dts`.
- [V] SW43410 display, 1440 x 3120. The current driver offers one fixed
  mode: 320280 kHz / (1700 x 3140) = 60 Hz.
  Source: `K/drivers/gpu/drm/panel/panel-lg-sw43410.c`,
  `sw43410_mode` and `sw43410_get_modes`.
- [V] Stock Android also reports only 1440 x 3120 at approximately 60 Hz,
  with no alternative refresh rates. Source: filtered `dumpsys display`
  query on 2026-11-02. This is a declared mode, not a measured scanout rate.
- [V] Prior RAM tests reached a visible desktop and confirmed touch.
  USB ACM and eight-core execution passed separate controlled runs.
  Source: `K/lgg8/docs/STATUS.md` and `CONNECTIVITY.md`.
- [V] WCN3998 Bluetooth firmware loading and controller power/version/off
  passed. Pairing, data, the factory address source and wake remain open.
  Source: kernel commit `29f212e0ee80` and `K/lgg8/docs/CONNECTIVITY.md`.
- [V] MPSS DMS and UIM status queries passed using private EFS shadows.
  Physical SIM, registration, data and calls are untested; the owner
  deferred SIM testing. Source: `K/lgg8/docs/MODEM.md`.
- [V] Experimental Wi-Fi now passes firmware loading, WLFW, PHY and
  network-interface registration. A/B/A isolated an early-HELLO QRTR
  announcement loss; a separate build without temporary QRTR/PD logging
  passed the complete RAM test, USB observation and Android recovery.
  Scanning, association and data are untested, and ath10k currently falls
  back to a random MAC. This is not OmaMobile radio acceptance.
  Source: kernel commits `6ac9126d1d89`, `81b24bcbeb5a` and `K/lgg8/docs/TFTP.md`.
- [V] The owner's current recovery boots Android from slot B. The generic
  project convention that stock occupies A must not be assumed here.
  All previous acceptance used `fastboot boot`, retained both boot-slot
  hashes, and returned to Android.

## Design

Use the shared rootfs, shell and initramfs. Add only the LG device policy,
firmware mappings and services it needs. Samsung AoC, Trusty and SIT
profiles do not describe this Qualcomm board.

The current LG boot path uses an Android header-v0 envelope and a verified
MMU-off shim. It is neither the Tensor android-v4 layout nor the Pixel 4
U-Boot probe. Start with a `ram-only` descriptor and an empty storage
allowlist; generic images, flash, push and installation must refuse it.
The descriptor is a candidate record, not a supported release target.

For M1, add an explicit `initramfs --ram-probe --ssh-key PUBLIC_KEY`
build mode. It may read a `ram-only` descriptor only when its writable
partition list and boot-image list are empty and its init is the shared
`/initramfs/init`. Image generation and every phone write command keep
rejecting this boot method. Pack a board-compatible marker, one explicit
public key and a static BusyBox for the independently verified LG boot
envelope. No developer's other keys or board-specific reboot helpers
belong in this probe.

The shared init must force every exposed storage disk and partition
read-only in probe mode, arm a 90-second recovery timer before loading
optional board modules, and stay in RAM after USB/SSH setup. It must not
reach root growth, filesystem repair, mounting userdata or switching root.
Exercise these branches offline with simulated storage and reboot
commands before using the exact verified kernel in a RAM-only phone run.

Keep the panel at its verified 60 Hz mode. Dynamic rate switching, lower
power modes and measured scanout cadence are separate future gates; do
not infer additional modes from another device's settings.

## Gates and runbook

| Gate | Action and pass condition | Stop condition | Recovery / risk |
| --- | --- | --- | --- |
| M0, offline | Validate descriptor syntax and ensure generic write paths refuse it. Inventory the kernel config, modules and boot-envelope hashes. | Any generic path accepts a writable LG target, or module identities differ. | No phone access; correct the candidate. |
| M1, RAM | Build the shared initramfs with LG USB configuration; use the verified temporary boot envelope. Pass: a fresh USB SSH connection and recoverable serial console. | Wrong compatible, missing guardian/log stream, no reconnect, or changed slot state. | RAM timeout returns to the existing Android recovery; no slot switch or partition write. |
| M2, storage read-only | Before enabling UFS, verify LG LUNs/partition names and install the shared guard with no write exceptions. Pass: all exposed disks/partitions read-only, no Android mount. | Any unexpected writable block device or layout mismatch. | Reboot to Android; do not add allowlist entries. |
| M3, userspace | Supply a read-only Arch root with a RAM overlay or an explicitly designed alternative; run shared OmaMobile and verify actual display/touch and a fresh SSH session. | No usable display/input, unsafe storage state, or loss of recovery. | Return through the RAM guardian; retain the known-good image. |
| M4, integration | Test GPU, Wi-Fi, Bluetooth and device policy one at a time; record kernel/artifact identities and results. | A hang, thermal fault, missing firmware provenance or failed recovery. | Disable the experimental feature and return to the last accepted RAM image. |
| M5, persistent install | Prepare a separate layout/recovery proposal and concrete image only after RAM acceptance. | Stock recovery placement, data preservation or slot flags remain unknown. | No install until those requirements and the owner's intended data handling are resolved. |

M1 passed with the shared initramfs: PID 1 and file hashes, ACM frames,
two fresh SSH connections, automatic Android return, both boot-slot hashes
and the complete USB observation all passed. The second SSH connection
strictly checked the first connection's host key. The host used a temporary
namespace containing only the phone's USB interface, then removed it.
The touch input device was listed, but actual display and touch were not
observed. An early DRM query was empty. SCSI is disabled in this kernel,
so this run did not exercise protection after real UFS enumeration.

The first candidate used `lg,alphalm` instead of the compiled DTB's
`lge,alphalm`; the compatible guard stopped initialization and the phone
returned to Android. The corrected candidate passed. LG's archive adapter
now requires the actual compiled DTB before producing an envelope.
It converts only in-root leading-parent links to equivalent absolute
links and checks static PIE, without imposing LG envelope rules on the
shared OmaMobile initramfs. The 90-second RAM timer uses a finite 120-second
kernel watchdog opening deadline as a fallback.

M2-M5 remain open. A desktop in a different diagnostic userspace is not
acceptance of the shared rootfs or Hyprland. Kernel-side evidence is in
[OMAMOBILE.md](https://github.com/LIghtJUNction/linux-lgg8/blob/lgg8/modem-20261102/lgg8/docs/OMAMOBILE.md).
No commands that format `userdata`, change slots or write GPT/devinfo are
part of this initial port.

## Submission

Offline results, 2026-11-02: `tests/device-overlays` compiled all 53
existing overlays and parsed every descriptor, including alphalm. With
all phone transports replaced by refusing test stubs, `images`, `flash`
and `push` each rejected `BOOT_METHOD=ram-only` before using a transport.
The Mesa package candidate adds Gallium Freedreno; compilation and GPU
execution are still open gates.

The shared probe and storage-guard checks and the full local suite passed.
Rootfs smoke was skipped because a root image has not been built.

Device descriptor, notes, firmware extraction mappings, device package
and shared-tool changes belong here. Drivers, bindings and the board DTS
belong in the kernel repository. Run the project's local checks and a
real-device smoke test before submitting the port; publish no firmware,
NV, complete captures or identifiers. Update the device matrix only from
the acceptance evidence and link the corresponding notes.

## Resume after the 2026-11-02 checkpoint

The owner requested stopping after committing and pushing this work.
Kernel M1 is cd217a95a on lgg8/modem-20261102; shared-initramfs support
is c489eca on this branch. The phone has returned to Android, the
successful result is retained, and no test network namespace remains.

Continue with a device package named omamobile-device-alphalm and add its
PACKAGE field to the descriptor; no such package has been created yet.
Use a read-only root supplied over the existing USB link and a RAM overlay
for the next Arch/Hyprland gate. The verified kernel has NBD and overlayfs
as modules, ext4 built in, and SCSI disabled. Pack matching modules and the
reviewed private GPU firmware; keep the accepted Image and DTB unchanged.
Do not turn the M1 RAM loop into the normal userdata/install path.

Mesa 1.5 adds Gallium Freedreno in source only; package compilation and
GPU execution remain unverified. No rootfs image exists yet. Published
packages fetched into out/alphalm/published verified their signatures,
but download stopped twice on TLS EOF errors, most recently while fetching
omamobile-modem-sit-0.3.4-1-aarch64.pkg.tar.zst. Re-running
tools/fetch-published --channel development out/alphalm/published reuses
already verified files. A port-local signing key is in gitignored
keys/alphalm; retain it privately and use the project's --local alphalm
builds. Do not publish the key, phone firmware, NV or private boot images.

After Arch/Hyprland, complete actual GPU/display/touch, Wi-Fi scan and
association/address provisioning, Bluetooth pairing/data/wake, audio,
sensors/cameras and the other peripherals, power/charging/long-term
stability, real UFS protection and finally the separately designed
persistent boot path. Physical SIM testing remains deferred by the owner.
These gates remain open; no upstream submission or complete-device claim
has been made.
