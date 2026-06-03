# Tasks

<!-- policy: Run tests before every commit. Never skip CI checks.
     policy: Prefer fixing root causes over symptoms. -->

## P0

- [ ] Generate `.github/dependabot.yml.jinja` — automated dependency updates per ecosystem
- [ ] Generate issue templates — `.github/ISSUE_TEMPLATE/bug_report.yml` + `feature_request.yml`
- [ ] Generate `.github/PULL_REQUEST_TEMPLATE.md`

## P1

- [ ] Create `scripts/test-template.sh` — copier copy into tmpdir, validate output syntax
- [ ] Document `_skip_if_exists` entries in `copier.yml` with inline comments
- [ ] Add `_migrations` example — v1.0.0 → v1.1.0 pattern as a worked migration
- [ ] Wire `_external_data` stub — parent template answer loading

## P2

- [ ] Non-Go task runner partials (Taskfile for Python/Node/Rust — matching Go's `_partials/taskfile-go.jinja`)
- [ ] `go.mod` optional `toolchain` directive question
- [ ] Audit: verify `detect.py` marks all boolean toggles (check missing: `use_apm`, `fork_upstream`, `include_code_of_conduct`, `node_package_manager`)

## P3

- [ ] SHA-pin all GitHub Actions in CI workflows (currently `@v4`/`@v5` — pin commit SHAs)
- [ ] `.nvmrc` generation alongside `.go-version`/`.python-version` pattern
- [ ] `docs/opencode-formatter-handoff.md` — rewrite or delete from repo root (stale, already removed from `template/docs/`)
