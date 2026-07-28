# Security Audit

Target release: OneSage v0.1.0-alpha

Audit date: 2026-07-28

Scope: current local workspace before public GitHub release.

## Summary

The public release should not upload the current workspace as-is.

The clean public release should include only reviewed source and documentation:

- `README.md`
- `CONTRIBUTING.md`
- `.gitignore`
- package metadata
- `onesage/`
- reviewed public docs

The current workspace also contains old versions, output files, temporary folders, and internal research artifacts that should be excluded.

## Scan Targets

Checked for:

- local absolute paths
- usernames
- API keys
- tokens
- passwords
- secrets
- personal project data
- local databases
- temporary output files

## Findings

### 0. Targeted public-file scan result

Targeted scan covered:

- `README.md`
- `CONTRIBUTING.md`
- `.gitignore`
- public docs under `docs/`
- `onesage-v0.4/pyproject.toml`

Result:

- no real API key found
- no real token found
- no real password found
- no release-blocking local absolute path found in the intended public files

The words `token`, `password`, `secret`, and `OPENAI_API_KEY` appear only as checklist terms in security documentation.

### 1. Local absolute paths found

The scan found local absolute paths in non-release or internal files.

Examples:

- internal design docs mention the local project path
- older version README files mention local workspace paths
- `tools/build_zhouyi_rules.py` contains a local path

Release action:

- Do not upload old version folders as public release content.
- Do not upload `tools/` unless reviewed and cleaned.
- Prefer publishing only reviewed docs and `onesage-v0.4/onesage/`.

### 2. Output directory contains research artifacts

The `output/` directory contains research and competitor-analysis artifacts.

It includes words such as:

- secrets
- tokens
- security

These appear to be research text, not actual credentials, but the directory is not needed for public alpha.

Release action:

- Exclude `output/`.
- `.gitignore` now excludes `output/`.

### 3. No direct API key pattern confirmed in release files

No actual API key was confirmed in the intended release files.

Still check before publishing:

- `.env`
- copied shell history
- SQLite database files
- local config files

### 4. SQLite data must not be uploaded

OneSage uses SQLite for local memory.

Release action:

- Do not upload `*.db`, `*.sqlite`, or `*.sqlite3`.
- `.gitignore` excludes these files.
- Publish schema and docs, not local memory data.

### 5. Temporary and archive files present

The workspace contains development artifacts:

- `.tmp_onesage_*`
- `output/`
- `onesage-v0.4.zip`

Release action:

- Do not upload these files or folders.
- `.gitignore` excludes them.

### 6. Old version folders are not release-ready

The workspace contains:

- `onesage-v0.1/`
- `onesage-v0.2/`
- `onesage-v0.3/`
- `onesage-v0.4/`

Only `onesage-v0.4/onesage/` should be used as the current source package for this alpha.

Release action:

- Do not publish old version folders in the public repo.
- Build a clean release tree.

## README Final Check

README includes:

- what OneSage is
- what OneSage is not
- quick start command
- current status
- current limitations
- roadmap links
- architecture overview

README passes the public alpha readability check.

## pyproject Version Check

Original version:

```toml
version = "0.4.0"
```

Updated release-compatible Python version:

```toml
version = "0.1.0a1"
```

Reason:

- GitHub release name can be `v0.1.0-alpha`.
- Python package version should use PEP 440 form `0.1.0a1`.

## Security Recommendation

Before publishing:

1. Create a clean release directory.
2. Copy only files listed in `docs/GitHub_File_Manifest.md`.
3. Run a final secret scan inside that clean directory.
4. Confirm no database files exist.
5. Confirm no local absolute paths exist.
6. Confirm no private case data exists.

## Current Risk Level

If publishing the entire current workspace:

```text
High risk
```

If publishing only the clean manifest files:

```text
Low to medium risk
```

Remaining risk:

- Documentation may still need a final path scan after files are copied into the clean release directory.
- Package layout should be normalized so `onesage/` is at repository root.
