# Runtime and generated data
The default server creates `prepwise.sqlite3` here. Uploaded rows are stored in SQLite; the uploaded source file is not automatically archived.

Local generation may create `raw/`, `processed/`, `predictions/` and `synthetic/` folders. Preserve source files and generation manifests. Do not commit live databases, credentials, private data or the audit oracle as model input.

For this competition, use team-created labelled synthetic records only. See [Data and models](../docs/DATA_AND_MODELS.md). Durable cloud storage and backup/restore verification are still required before claiming production persistence.
