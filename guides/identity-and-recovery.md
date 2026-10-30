<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Identity and recovery — NON-NORMATIVE implementation guide

**Status: informative guidance only, not a conformance requirement.** This guide
does not extend or amend [OAF 0.1.0](../spec/0.1.0.md) or its schemas. The published
specification and schemas govern conformance. Section references below refer to
that specification. These recommendations describe possible exporter practices;
they prescribe no storage engine, backup service, ledger layout or application.
All examples are synthetic and illustrative, not complete OAF archives.

## Persistent mappings across exports

An exporter may need durable identity state to associate retained catalogue
evidence with OAF identifiers. This state can be part of the catalogue or kept
separately; OAF defines no private ledger format. Treat whatever is needed to
repeat those associations as essential application state rather than a disposable
cache. Record enough evidence to distinguish an exact re-export from a new event.

Apply the identity rules in sections 2 and 3:

- Keep `archive_id` for exports of the same catalogue lineage. `created_at`
  describes each export, not the beginning of that lineage.
- Preserve IDs for the same entities and never reuse an ID for a different entity.
  Use opaque UUID URNs, preferably random UUIDv4, with no embedded private hints.
- Preserve a source ID through an explicitly confirmed move or remount of the
  same collection. A path, device hint or provider identifier alone does not
  establish portable source identity.
- An occurrence is an immutable historical observation. Exact re-export retains
  its ID; every later observation gets a new ID, even at an unchanged location.
  A mutable catalogue row or source/path slot is not itself an OAF occurrence.
- Preserve the identities of the actual activities supporting retained evidence.
  A new export does not by itself turn old observations into new scans. A new
  activity represents a new event, with its actual scope and outcome.
- An asset identifies particular bytes. Names, sizes and timestamps alone do not
  establish byte identity. Omit unsupported asset associations; changed bytes
  cannot reuse an asset ID. Revised annotations receive new annotation IDs.

For example, re-exporting a retained observation of the synthetic collection
“Sample collection” preserves its occurrence and supporting activity IDs. A later
observation of the same logical location receives a new occurrence ID, even if
its recorded attributes match. Replacing the old record's timestamp or state
while retaining its ID would misrepresent that immutable observation.

When an application's catalogue retains only current mutable rows, an exporter
can map the retained evidence conservatively, but cannot reconstruct observations
that were overwritten between exports. A changed retained row is not permission
to rewrite an earlier OAF occurrence. Preserve earlier exports when history
matters. Export omission does not mean deletion, and a stale row does not prove
that an object is missing (section 3.2).

Do not invent original observation times. Where those times are unknown, section
2 calls for the import observation time and an explanation in metadata; an
import activity can record the import time. Do not label an import as a completed
source scan or assert current presence without evidence. Metadata cannot override
core semantics, and partial coverage remains partial (sections 3.4 and 4).

## Back up and recover a consistent set

Plan recovery for the catalogue and all identity state together. Backing up only
the catalogue can preserve descriptive data while losing cross-export continuity.
Backing up only mappings cannot recover the catalogue evidence they describe.

A useful recovery procedure is to:

1. Identify the catalogue, mapping state, schema/version information and any
   non-secret configuration needed to interpret them. Keep credentials and
   private access bindings protected separately from public interchange files.
2. Capture a mutually consistent recovery point. Coordinate catalogue changes,
   identity allocation and export publication so a crash or concurrent writer
   cannot publish an export whose identities are absent from recoverable state.
   Transactions, snapshots or coordinated checkpoints are possible techniques;
   this guide requires no particular mechanism.
3. Retain completed exports and enough recovery information to identify which
   catalogue and mapping generations belong together. Detect incomplete writes
   and mismatched recovery sets before resuming exports. Verify backup integrity
   and maintain access to any required recovery secrets independently.
4. Restore into an isolated location first. Check integrity, versions, reference
   consistency and the association between catalogue and mapping state. Re-export
   unchanged retained evidence and compare IDs and semantics with a known export;
   each new export can have a different `created_at`.
5. Before resuming production, account for exports made after the recovery point.
   An older backup may omit identities already published. Preserve those exports
   and reconcile from trustworthy evidence, or stop continuity-dependent output.
   Avoid two uncoordinated writers advancing the same recovered lineage.

Restoring a consistent older set does not prove that no later events occurred.
Describe recovery limits honestly. Recovery checks belong to the implementation;
the OAF validator checks an export, not the completeness of a backup or the truth
of identity claims.

## If identity state is lost

Preserve surviving catalogues, exports and backups before attempting recovery.
Prefer a verified consistent restore. A surviving OAF export may supply original
IDs and immutable records, but it need not contain the application's complete
mapping history or enough evidence to associate every current row with them.
Reconstruct only associations supported by trustworthy retained evidence, and
make uncertainty visible to the operator.

Do not guess earlier IDs from paths, names, row positions, sizes or timestamps,
silently mint replacement IDs while claiming they preserve prior identity, or
fabricate missing observations, activities or continuity. A digest comparison
alone does not establish source, occurrence or catalogue-lineage continuity.
Conflicting records with the same ID require surfacing the conflict and preserving
both inputs; 0.1.0 defines neither last-writer-wins nor automatic remapping
(section 3).

If continuity cannot be established, stop exports that claim it and explain what
was lost. The operator can recover more evidence or deliberately begin an
independent catalogue with a new `archive_id`. Document that break without claiming
that newly allocated identities recover the lost history. Loss of a private
mapping file does not, by itself, make surviving OAF files unreadable or alter
their existing IDs. If reliable evidence still establishes the same lineage,
loss of some record mappings is not automatically a reason to change its archive
ID; unresolved associations still cannot be invented.

## Relocation, copies and independent forks

Moving an export directory, restoring the same catalogue to replacement hardware,
or changing backup destinations does not by itself create an independent lineage.
For a confirmed continuation, retain the archive ID and the IDs of unchanged
entities. Review private access configuration separately; moving a catalogue is
not proof that a new mounted collection is the original source (section 3.1).

A deliberately independent catalogue fork receives a new archive ID (section 2),
even if it initially copies the same records. Merely changing a directory name
does not make that decision. Conversely, copying an export for reading or backup
does not require a new archive ID.

For a synthetic example, a catalogue continued after a confirmed machine move
keeps `urn:uuid:11111111-1111-4111-8111-111111111111`. A deliberately independent
working catalogue starts with
`urn:uuid:22222222-2222-4222-8222-222222222222`. These are fixed example archive
IDs, not values to reuse in production. Unchanged copied entities retain their
record IDs; new observations and other new entities receive new IDs. A new
archive ID is not an instruction to rewrite historical occurrence records or
claim a new observation took place.

OAF 0.1.0 has no core parent-archive field, fork relationship, merge protocol or
automatic synchronization. An implementation can document the operator's fork
decision separately, but cannot give metadata standardized lineage semantics or
add an unknown core field. Later merging still follows the conflict rules.

## Each export remains independently readable

For the core catalogue profile, `manifest.json` and `records.jsonl` carry the
portable meaning. All record references resolve within that export (section 5),
including when exporting a selected subset. A private identity store helps a
writer continue identities; it is not a prerequisite for interpreting those
already exported. Do not require a reader to consult it to resolve IDs, recover
core fields or understand provenance. Required extensions retain their explicit
negotiation rules; they are not an implicit dependency on a private ledger.

Test an export with an independent core reader or validator that has no access
to the application, mapping state, original content, accounts or network. Reading
does not automatically fetch links, traverse source paths or execute restoration
instructions. The catalogue profile does not contain original content and cannot
restore missing bytes; content backup is a separate concern (sections 1 and 8).

## Privacy and publication review

Identity state can expose cross-export links and private implementation hints.
Protect it and its backups according to the sensitivity of the catalogue. Do not
ship it merely to make an export readable. Labels, logical paths, timestamps,
hashes, annotations and stable UUID linkability can themselves be sensitive.
Preview exports and review redactions, provenance and references together
(section 6). Redaction cannot invent evidence or leave dangling references.

Use synthetic reproductions when reporting implementation problems publicly.
Exclude private catalogues, identifiers, operational paths, account mappings,
credentials, raw logs and private fixtures. This guide contains original prose
and synthetic examples only; it publishes no private implementation data or code.
It is documentation under the repository's [CC BY 4.0 licence](../LICENSE).
Repository licensing grants no rights to a user's catalogue or source content.
