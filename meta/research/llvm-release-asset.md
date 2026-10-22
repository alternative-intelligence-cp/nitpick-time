# The LLVM 20.1.8 release asset CI installs — research digest

**As of 2026-10-22.** Question: what are the sha256 and the size of
`LLVM-20.1.8-Linux-X64.tar.xz` at the LLVM project's `llvmorg-20.1.8` release —
the asset `.github/workflows/ci.yml` installs — and can it be replaced under its
name? Filed by cycle 0.4.0a (TM-265), whose CI step pins the digest.

## Answer

The asset is
`https://github.com/llvm/llvm-project/releases/download/llvmorg-20.1.8/LLVM-20.1.8-Linux-X64.tar.xz`,
**2 021 269 412 bytes, sha256
`1ead36b3dfcb774b57be530df42bec70ab2d239fbce9889447c7a29a4ddc1ae6`**. Three
readings agree: the asset itself, downloaded once and hashed whole; GitHub's
record of the asset; and the provenance the LLVM project's release workflow
signed for it. **The release is not immutable** — GitHub's record of it reads
`"immutable": false` — so an asset can be deleted and uploaded again under the
same name, and the pin is the digest, not the name.

## Evidence

- `https://github.com/llvm/llvm-project/releases/download/llvmorg-20.1.8/LLVM-20.1.8-Linux-X64.tar.xz`
  — retrieved 2026-10-22 05:47:29–05:48:25 EDT, streamed through `sha256sum`
  and `wc -c`: `1ead36b3dfcb774b57be530df42bec70ab2d239fbce9889447c7a29a4ddc1ae6`,
  `2021269412` bytes.
- `https://api.github.com/repos/llvm/llvm-project/releases/tags/llvmorg-20.1.8`
  — retrieved 2026-10-22: the asset's record, `"id": 271269785`, `"size":
  2021269412`, `"digest":
  "sha256:1ead36b3dfcb774b57be530df42bec70ab2d239fbce9889447c7a29a4ddc1ae6"`,
  `"created_at": "2025-07-09T05:32:33Z"`, `"updated_at":
  "2025-07-09T05:33:23Z"`, uploaded by `github-actions[bot]`; and the
  release's own, `"immutable": false`, published `2025-07-09T03:20:57Z`.
- `https://github.com/llvm/llvm-project/releases/download/llvmorg-20.1.8/LLVM-20.1.8-Linux-X64.tar.xz.jsonl`
  — retrieved 2026-10-22, 10 422 bytes: a Sigstore bundle whose in-toto
  statement, `"predicateType": "https://slsa.dev/provenance/v1"`, names the
  subject `LLVM-20.1.8-Linux-X64.tar.xz` with `{"sha256":
  "1ead36b3dfcb774b57be530df42bec70ab2d239fbce9889447c7a29a4ddc1ae6"}`, built by
  `.github/workflows/release-tasks.yml` at `refs/tags/llvmorg-20.1.8` (the
  project's run 16159480195), and logged at Rekor index 268489885.

## What would change this

A digest that differed between the readings, or an asset record updated after
2025-07-09: either would mean the asset changed under its name, and CI's check
would refuse the changed asset, which is the check's purpose. Neither did.

## Confidence and gaps

High for the digest and the size: the asset was hashed whole, and two records
kept by others agree with it. **Not checked: the attestation's signature** —
its certificate chain and its inclusion in the transparency log were read as
the project's statement, not verified as a signature; CI holds the asset to its
digest and reads no provenance. The second reading of the asset itself is CI's
own fetch, at the push that first runs the check. Security-sensitive: stale
ninety days after its date, on 2027-01-20, and re-checked whenever the pinned
LLVM release moves.
