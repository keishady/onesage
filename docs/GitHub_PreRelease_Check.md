# GitHub Pre-release Check

Target release: OneSage v0.1.0-alpha

Current internal capability state: v0.8.1

This checklist is for preparing a public GitHub alpha release. It is a manual review checklist. Do not publish private workspace data.

## 1. Do Not Include Personal Paths

Check for local absolute paths such as:

- Windows drive paths
- user home directories
- machine-specific absolute paths
- local workspace names
- private temp directories

Recommended action:

- remove personal paths from documentation before release
- replace local paths with relative paths
- keep examples generic

## 2. Do Not Include Personal Case Data

OneSage may contain local strategic examples created during development.

Check for:

- private user questions
- private project names
- personal business ideas
- real outcomes from private experiments
- local SQLite contents

Recommended action:

- keep only synthetic examples in public docs
- remove or ignore local runtime data

## 3. Do Not Include SQLite Runtime Data

Check for SQLite database files:

- `OneSage.db`
- `*.sqlite`
- `*.sqlite3`
- any database under local workspace folders

Recommended action:

- do not publish local runtime databases
- add database files to `.gitignore`
- include schema documentation instead of local data

## 4. Check for Secrets

Search for:

- API keys
- tokens
- passwords
- cookies
- private URLs
- local credentials
- `.env`
- `.env.local`
- `OPENAI_API_KEY`
- `sk-`

Recommended action:

- remove secrets
- rotate any leaked credentials
- commit only `.env.example` if needed

## 5. Remove Temporary Files

Check for:

- `__pycache__/`
- `.pytest_cache/`
- `.mypy_cache/`
- `.ruff_cache/`
- `.DS_Store`
- `Thumbs.db`
- temporary export files
- local zip archives
- local output folders

Project-specific folders to review:

- `.tmp_onesage_v02`
- `.tmp_onesage_v02b`
- `.tmp_onesage_v03`
- `.tmp_onesage_v04`
- `output`
- `onesage-v0.4.zip`

Recommended action:

- exclude temporary development artifacts from the public release
- keep source code and documentation only

## 6. Check Package Metadata

Current package metadata may still show older internal version numbers.

Check:

- `pyproject.toml`
- package name
- package description
- CLI entry points
- Python version requirement

Recommended action:

- decide whether public alpha should use `v0.1.0-alpha` or current internal state labels
- avoid claiming production readiness

## 7. Check Documentation Consistency

Required public docs:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `CONTRIBUTING.md`
- `docs/GitHub_PreRelease_Check.md`

Check that documentation states:

- OneSage is not an autonomous agent
- OneSage is not a tool executor
- OneSage is not a workflow engine
- OneSage does not currently use LLM reasoning
- OneSage does not currently use embedding retrieval
- OneSage does not call external APIs

## 8. Check Strategic Boundary

The public release should communicate:

```text
OneSage = Decision Layer before Action
```

Do not market OneSage as:

- fully autonomous
- production-ready
- universal AI agent
- automation platform

## 9. Suggested .gitignore Items

Before publishing, consider adding:

```gitignore
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
.env
.env.*
*.sqlite
*.sqlite3
OneSage.db
output/
.tmp_onesage_*/
*.zip
```

Do not add `.gitignore` automatically unless preparing the actual repository package.

## 10. Final Manual Checklist

- [ ] No personal absolute paths in public files.
- [ ] No private case data.
- [ ] No local SQLite database.
- [ ] No secrets or API keys.
- [ ] No cache directories.
- [ ] No temporary output files.
- [ ] README describes OneSage in 5 minutes.
- [ ] Architecture docs match current v0.8.1 capabilities.
- [ ] Roadmap separates current features from future plans.
- [ ] Contributing guide explains acceptable contributions.
- [ ] Release name clearly says alpha.
