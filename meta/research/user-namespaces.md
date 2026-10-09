# Unprivileged user namespaces on Ubuntu 24.04 — research digest

**As of 2026-10-08.** Question: may an unprivileged process on CI's runner
image, Ubuntu 24.04 LTS (`.github/workflows/ci.yml`'s `ubuntu-24.04`), create a
user namespace and use the capabilities inside it — enough to mount a `tmpfs`
over `/etc` in a mount namespace of its own — and if not, what lifts the
restriction?

## Answer

Not by default. Ubuntu 24.04 LTS restricts unprivileged user namespaces when
AppArmor is in use: an unprivileged, unconfined program may create one, under
a default profile that denies it the use of any capability inside — so the
`mount` a unit makes there is refused (`probe22`'s exit 24). The release notes
name the sysctl that lifts the restriction, for one boot or for good:
`kernel.apparmor_restrict_unprivileged_userns`, set to 0. They warn that
lifting it gives up the defence against kernel exploits that use unprivileged
user namespaces. A GitHub-hosted runner is a fresh VM for one job with
passwordless `sudo`, so CI lifts it in a step before the harness and prints
the value before and after. The workbench machine reads 0, measured.

## Evidence

- https://discourse.ubuntu.com/t/ubuntu-24-04-lts-noble-numbat-release-notes/39890
  — retrieved 2026-10-08 — the release notes' section on unprivileged user
  namespace restrictions: in 24.04 the Ubuntu kernel restricts unprivileged
  user namespaces when the `apparmor` package is in use; a default AppArmor
  profile lets an unprivileged, unconfined program create one and denies "the
  subsequent use of any capabilities within the user namespace"; to disable,
  for one boot, `echo 0 | sudo tee /proc/sys/kernel/apparmor_restrict_unprivileged_userns`,
  or for good a `/etc/sysctl.d/60-apparmor-namespace.conf` holding
  `kernel.apparmor_restrict_unprivileged_userns=0`; and that neither protects
  against kernel exploits that abuse unprivileged user namespaces.
- Measured on the workbench, 2026-10-08: `sysctl kernel.apparmor_restrict_unprivileged_userns`
  reads 0, and `unshare -rm` with a `tmpfs` mount inside succeeds, as
  `tests/probe/probe22_private_etc.npk` does on both legs.

## What would change this

A runner image whose restriction is already lifted, which would make CI's step
a no-op; or one where lifting it is refused, which would turn `probe22` RED at
exit 24 in CI and stop cycle 0.3.2 at its second step, before the system zone
— the plan's order exists for that. Neither is known before CI runs it: the
digest found no statement from GitHub of what its `ubuntu-24.04` image sets,
and the step prints it.

## Confidence and gaps

High for Ubuntu's default and the sysctl, from its own release notes. Unknown
for GitHub's image until its first run prints the value; the step asserts
nothing about the value before, sets it, and makes a namespace with a mount
once, so a refusal is the step's and never a unit's verdict.
