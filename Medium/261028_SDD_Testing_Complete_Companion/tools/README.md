# Companion maintenance tools

The tools in this directory are separate from the starter's standard-library runtime.

## Audit the original summary

```sh
python3 tools/audit_original_record.py
python3 -m unittest discover -s tools/tests -v
```

The audit checks supplied historical metadata. It does not authenticate unavailable raw reports or rerun the original framework.

## Check the delivered package

```sh
python3 tools/verify_package.py
```

This verifies the file hashes in `SHA256SUMS` and reader-facing local Markdown/HTML links. It does not fetch external URLs. Exact archived originals retain source-only historical references and are excluded from navigation checking; the portable reading copies are checked. Newly generated user-run outputs are not part of the distribution hash manifest.

## Rebuild reading copies after editing

The default starter requires no third-party packages. Only this optional publishing task requires the Markdown renderer recorded in [requirements-preview.txt](requirements-preview.txt):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/requirements-preview.txt
.venv/bin/python tools/build_previews.py
python3 tools/verify_package.py --links-only
```

Editing or rebuilding distributed files will invalidate their original distribution hashes. Preserve the delivered archive as the original, create a new version, and generate a new manifest rather than claiming the changed files match the old one. The renderer writes corresponding `.html` reading copies, `index.html`, and an article preview with embedded PNGs. It does not publish to Medium or any external site.

On Windows use `py -3 -m venv .venv` and `.venv\Scripts\python.exe` for the two environment commands. Rendering is optional; the distributed HTML already works offline.

## Build a portable release

From the companion root, after editing and rebuilding the previews:

```sh
python3 -m unittest discover -s tools/tests -v
python3 tools/package_release.py --refresh-manifest --output ../sdd-testing-companion-reader.zip
```

The explicit `--refresh-manifest` updates the current [SHA256SUMS](../SHA256SUMS); the [October 28 manifest](../evidence/distribution-history/SHA256SUMS-20261028.txt) remains an archived input. Omit the flag to require the existing manifest to match. The output must be outside the companion and both the ZIP and its `.sha256` sidecar must be new paths. The builder refuses to overwrite a retained release.

The builder checks local links, hashes and complete manifest coverage against the exact files it packages. It rejects symlinks and verifies archive names and file bytes. Sorted entries, fixed timestamps and normalized file modes give repeatable archives with the same inputs and compression environment. A changed compressor version may change the ZIP digest; individual file hashes remain the comparison point.

The archive includes the article, offline reading copies, figures, starter, tests, dotfiles and retained evidence. It excludes virtual environments, Git metadata, bytecode and generated `runs`, `test-results`, `validation-runs` and `validation-container` directories. It does not include model weights, private native-agent harnesses or containers. Hashes detect changes; they are not publisher signatures.

Before distributing a ZIP, extract it into a **new directory**, open `SDD_Testing_Companion/index.html`, and run from that extracted root:

```sh
python3 tools/verify_package.py
python3 starter/validate.py --output ../reader-runs
```

Keep the fresh results alongside the archive. The [reproduction guide](../starter/docs/REPRODUCE.md) explains expected results and the optional container and live-model paths. Releasing the archive does not publish the article or upload anything.
