# Open Archive Format (OAF)

**v0.1 / 0.1.0 — experimental, catalogue-only.** A vendor-neutral, versioned,
openly licensed format for local-first digital archive catalogues. Your data
remains yours; independent applications can read and write it without a service
or proprietary database. Commercial and open-source implementations are welcome.

Start with the [normative specification](spec/0.1.0.md),
[manifest schema](schemas/manifest.schema.json), [record schema](schemas/record.schema.json)
and [synthetic examples](examples/README.md).

Implementation advice: [Identity and recovery — NON-NORMATIVE guide](guides/identity-and-recovery.md)
covers persistent mappings, recovery, relocation and independent forks.

An archive is two ordinary UTF-8 files:

```text
my-catalogue/
  manifest.json
  records.jsonl
```

Sources represent origin collections. Occurrences preserve individual historical
observations. Assets identify byte content only when supported by evidence;
unhashed observations are valid. Activities carry provenance. Annotations and
namespaced extensions let applications add meaning without owning the format.

## Validate locally

Python 3.9 or later. Install the dependency once; subsequent validation is offline.
Run these commands from this repository:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/validate.py examples/minimal
.venv/bin/python tools/validate.py examples/provenance
.venv/bin/python -m unittest discover -s tests -v
```

On Windows use `.venv\Scripts\python.exe` for the environment's Python.
Exit 0 means core validation passed; exit 1 means rejected/unreadable/unsupported
input. CLI argument errors use exit 2. Diagnostics avoid echoing catalogue values.
The validator checks syntax, schemas, references and semantic rules. It never
reads original content, contacts sources, or changes an archive. Optional unknown
extensions are structurally accepted; every required extension is unsupported.
Reference tool resource limits are documented in the specification.

## Implemented and planned

Implemented: normative core model, JSON Schema Draft 2020-12, offline Python
validator, synthetic positive examples, negative conformance tests and CI.

Not implemented: database import/export adapters, application UI, scanning,
merging, migrations, content packaging/restoration, cryptographic authenticity
and synchronization. Optional self-contained content packages are future work;
0.1.0 is a catalogue, not a content backup. See [design notes](spec/design.md).

## Licences and ownership

Specification and prose documentation: **CC BY 4.0**. Schemas, reference code,
tests, workflow and synthetic examples: **MIT**. See [LICENSE](LICENSE) for exact
scope and texts. Both allow commercial use. A commercial app implementing OAF
does not have to publish its source code. These licences do not license any
user's archive contents or waive privacy obligations. No private catalogue,
account data, credentials or operational paths are included here.

Contributions and compatibility proposals are welcome; see
[CONTRIBUTING.md](CONTRIBUTING.md) and [CHANGELOG.md](CHANGELOG.md).
