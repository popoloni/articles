# Distribution history

The [October 28 checksum manifest](SHA256SUMS-20261028.txt) and [package validation record](package-validation-20261028.json) are preserved unchanged. They do not describe this revised edition.

The October 29 clean-clone audit found 196 missing manifest entries, one article checksum mismatch, and 24 broken local links. Of the missing files, 194 were present inside the supplied matrix and mutation ZIPs and matched their manifest hashes. This edition restores those exact bytes and supplies new starter ignore files. The revised files receive new hashes in the current [SHA256SUMS](../../SHA256SUMS).

The article mismatch came from a shortened introductory paragraph in Markdown while the older text remained in HTML. Reading copies are now rebuilt from the revised Markdown. Current checks are recorded separately in [package-validation.json](../../package-validation.json).
