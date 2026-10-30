# Synthetic archives

These examples were authored for OAF; no real inventory was transformed into
example data. Their labels, relative filenames, IDs, timestamps and annotations
are artificial. There are no source roots, account identities or content files.

- `minimal/`: one source, one observation activity, one unhashed empty-file
  observation. Demonstrates that scanning metadata need not hash content.
- `provenance/`: two sources, two occurrences sharing an asset, completed hash
  evidence, a missing observation from a partial activity, an opaque package
  of unknown size, a plain-text annotation and an optional namespaced extension.
  Records deliberately appear before some referenced objects. The digest is the
  well-known SHA-256 of zero bytes, not of a private file.

The missing and present occurrences are distinct historical observations of
the same synthetic location. Neither supersedes or deletes the other.

From the repository root run:

```sh
python tools/validate.py examples/minimal
python tools/validate.py examples/provenance
```

Use the Python environment described in the main README. Expected output reports
`valid: true`, version `0.1.0`, and 3 or 11 records respectively. JSON Schemas alone
cannot check references; use the reference validator or an equivalent full reader.
