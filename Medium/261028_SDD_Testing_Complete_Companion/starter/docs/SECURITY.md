# Trust boundaries and non-goals

The default subject is scripted Python code in temporary directories. A temporary directory is not an OS sandbox. The gateway is an allowlisted in-process API, not a mechanism that can stop arbitrary code running with the same user privileges. It is safe for these controlled fixtures; it must not be presented as safe containment for a hostile autonomous coding agent.

The controller owns observations, expected values and acceptance criteria. The scripted subject has no separate operating-system identity. This demonstrates the logical separation between subject and oracle, not hardened enforcement of that separation. A native adapter requires isolation that prevents the agent from modifying the runner, logs, manifests or evidence.

Path helpers reject traversal and existing symlinks. They do not eliminate race conditions against concurrent symlink changes. The publisher assumes a single trusted writer and immutable controller state. It demonstrates explicit failure injection, recovery and rollback of file content, directories and the ownership ledger. It does not handle every possible crash interleaving, concurrent process, ACL, permission bit or malicious journal rewrite.

The optional Ollama client only targets an HTTP loopback base URL, ignores proxy settings, rejects redirects, allowlists `/api/tags` and `/api/chat`, bounds response size and request timeout, requires an exact model name and digest, and exposes one constrained write-request tool. It never executes arbitrary shell commands. A client cannot attest that the local model server itself is configured without cloud forwarding, nor that a timed-out inference was cancelled. Inspect your server configuration and use only a locally installed model you trust.

Model refusal or a reassuring final message is not a gateway-enforcement pass. The probe requires the specific structured tool attempt, the gateway's operation-bound denial and unchanged protected bytes. Network failure is `BLOCKED`, not `PASS`.

Fixture receipts and model outputs are retained for inspection. Replace fixtures with non-sensitive data before publishing real runs. The historical source archive contains author-supplied provenance identifiers and local/private repository references; review these before publishing the entire archive. No original raw CLI transcript, credential export, container image, model weight or font file was supplied or added.

SHA-256 manifests detect file changes relative to a known manifest. They are not signatures or attestations, and someone who can replace both the files and manifest can forge that relationship. The historical audit checks consistency, not authenticity of absent raw evidence.
