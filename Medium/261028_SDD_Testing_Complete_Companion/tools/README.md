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
python3 -m pip install -r tools/requirements-preview.txt
python3 tools/build_previews.py
python3 tools/verify_package.py --links-only
```

Editing or rebuilding distributed files will invalidate their original distribution hashes. Preserve the delivered archive as the original, create a new version, and generate a new manifest rather than claiming the changed files match the old one. The renderer writes corresponding `.html` reading copies, `index.html`, and an article preview with embedded PNGs. It does not publish to Medium or any external site.
