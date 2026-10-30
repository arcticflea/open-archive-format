# Design rationale and input review (informative)

OAF separates the public interchange contract from an application's internal
catalogue. A commercial application can remain proprietary while implementing
an openly licensed format, as can competing commercial or open-source tools.
No implementation owns the format or requires an online account to use it.

## Lessons from an existing metadata catalogue

The design reviewed a private reference application's SQLite schema, JSONL
export implementation, scan/provenance behavior, operating documentation and
project coordination documentation. Review was of technical definitions and
behavior, not production inventory. No private data, files, account identifiers,
source roots, deployment paths, credentials or private repository history were
copied into this repository. The reference code was not copied or relicensed.
The public implementation is newly written and all examples are synthetic.

The input exports table/record envelopes, including operational state. That
export is an application migration foundation; it is not OAF. Merely renaming
it would expose internal and potentially private data, preserve database
assumptions, and overstate interoperability.

| Internal concept reviewed | OAF design / migration guidance |
| --- | --- |
| Accounts/provider account identifiers | No core account record. Keep access mappings private. |
| Sources with root/device/inode binding | Portable source UUID and safe label; roots and machine binding stay outside OAF. |
| Scan runs and statuses | Activity with action, time, explicit outcome and source references. Map completed-with-errors to partial, never completed. Running observations may use partial outcome in an export. |
| Mutable latest entry per source/path | Emit an immutable occurrence for the exported observation. A future observation gets a new ID. Do not claim unrecorded history. |
| Relative paths and file kinds | Optional path components and explicit opaque package kind. Root becomes empty components. Withhold unrepresentable/private names. |
| File size and modification nanoseconds | Present regular file size only. Convert modification time to UTC; round down nanoseconds to microseconds and document precision loss in metadata. Directory/package sizes omitted. |
| Device and inode | Private implementation hints, never portable content identity. |
| Unhashed metadata observations | Valid occurrences with no asset link. Do not fabricate digest/deduplication evidence. |
| Error rows and work queues | Do not publish raw messages or queues. Record safe activity limitations or inaccessible observations only when supported by evidence. |
| Database migration version | Separate application schema version from OAF version. |

An adapter must use a consistent database snapshot and safe explicit field
mapping, sanitize account/location/error data, preserve a private mapping of
stable source IDs, and maintain an export mapping for occurrence IDs. The input
stores latest entries rather than an immutable observation log: the adapter
must not invent prior observations. Export-time IDs may be minted once and
remembered for later re-exports. If reliable observation times are unavailable,
record an import observation at import time and explain the limitation.
An adapter must not guess a moved source or infer missing files from absence.
No such adapter is implemented or claimed compatible in this release.

## Deliberate boundaries

Core identity distinguishes a collection, a historical observation, and bytes.
A filename or inode does not establish byte equality. Catalogue readers do not
need content access. Hashing is optional and explicit; verified hash claims
need provenance, but the catalogue alone cannot authenticate the evidence.

Metadata objects allow descriptive experimentation without making every app's
fields mandatory. Namespaced extensions have explicit required-feature
negotiation. Unknown optional values can survive round-trip without being
interpreted. Storage configuration and credentials have no core fields.

The JSON Schema IDs are stable identifiers, not a promise of a hosted schema
service. The bundled schemas are authoritative and validation uses local copies;
GitHub Pages is not required or configured. No schema fetch occurs at runtime.

## Licence selection

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode) permits reuse
and adaptation of specification prose with attribution and modification notices.
This makes the specification reusable in documentation and independent projects.
[MIT](https://choosealicense.com/licenses/mit/) keeps schemas, examples and code
easy to integrate, including in proprietary products, subject to its notices.
Neither licence requires an implementing application to publish its source.
The licence is not a patent clearance, certification, trademark grant or licence
to users' original content. Contributors should submit only material they have
permission to license under the applicable terms.

## Next decisions

A future content-package profile needs independent requirements for byte
manifests, portability, safe extraction, filenames, symlinks and verification.
It must not silently turn catalogue import into a restore operation. Streaming,
extension registries, formal migration adapters, content derivation and
multi-writer conflict semantics also need independent proposals and tests.
