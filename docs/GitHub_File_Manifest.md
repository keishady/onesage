# GitHub File Manifest

Target release: OneSage v0.1.0-alpha

Internal capability state: v0.8.1

This manifest defines what should and should not be included in the first public GitHub alpha release.

## Recommended Public Repository Layout

Recommended clean release layout:

```text
README.md
CONTRIBUTING.md
.gitignore
pyproject.toml
onesage/
docs/
```

Current workspace note:

```text
The runnable package currently lives under onesage-v0.4/.
For a clean public repository, publish onesage-v0.4/onesage as onesage/
and onesage-v0.4/pyproject.toml as pyproject.toml.
```

Do not upload the entire local workspace as-is.

## Should Upload

Root files:

- `README.md`
- `CONTRIBUTING.md`
- `.gitignore`

Package metadata:

- `onesage-v0.4/pyproject.toml`

Source package:

- `onesage-v0.4/onesage/`

Recommended public docs:

- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/GitHub_PreRelease_Check.md`
- `docs/GitHub_File_Manifest.md`
- `docs/Security_Audit.md`

Optional internal design docs:

- legacy v0.7.1 Strategic Pattern Architecture
- legacy v0.7.2 Strategic Pattern Governance

Only include older internal design docs if local absolute paths and private notes are removed.

## Do Not Upload

Runtime databases:

- `*.db`
- `*.sqlite`
- `*.sqlite3`
- local OneSage SQLite memory files

Development outputs:

- `output/`
- `.tmp_onesage_*`
- `*.zip`

Old experimental package copies:

- `onesage-v0.1/`
- `onesage-v0.2/`
- `onesage-v0.3/`

Personal or local-only tooling:

- `tools/` unless reviewed and cleaned
- scripts containing local absolute paths

Private or machine-specific files:

- `.env`
- `.env.*`
- IDE settings
- cache folders
- local test artifacts

## Do Not Upload Private Data

Do not include:

- SQLite judgment memory
- private strategic questions
- private outcome reviews
- personal project names
- API keys
- tokens
- passwords
- browser/session data

## Release Packaging Recommendation

Create a clean release directory before GitHub publication:

```text
release/
  README.md
  CONTRIBUTING.md
  .gitignore
  pyproject.toml
  onesage/
  docs/
```

Then copy only reviewed files into that directory.

Do not publish directly from a local development workspace.
