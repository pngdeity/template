# Tasks

<!-- Agent contract
     Read this file before asking what to work on.
     Claim a task by appending (@agent-id) to its line, before starting.
     Remove a task only when its Verification command succeeds. Your belief that
     it works is not evidence.
     Add work you discover under the tier it belongs to, with an ID and a
     Verification command. Default to P2 when unsure.
     Do not reprioritize someone else's task. Record the concern in its Details
     and leave the priority alone.
-->

<!-- A task is a checkbox plus nested metadata fields, as in the P1 example.
     Completed tasks are removed, never checked off: put `closes <id>` in the
     commit and git log becomes the archive.
     Priority: P0 broken or users blocked. P1 planned work. P2 valuable, not
     blocking. P3 someday, kept for reference.
     Full field reference: README.md, Task tracking section.
-->

<!-- policy: Every template change is verified by a render, not by reading.
     policy: Prefer fixing root causes over symptoms. -->

## P0

- [ ] Create `scripts/test-template.sh` — render matrix as a repo script
  - **ID**: test-harness
  - **Tags**: tooling, ci
  - **Details**: The 18-config render matrix currently lives in
    `/tmp/opencode/matrix.sh`, which is scratch and disappears. It is the only
    thing that verifies a template change; it belongs in the repo.
  - **Acceptance**: `scripts/test-template.sh` renders every config, asserts
    audit Grade A, `@tasks-md/lint` zero errors and no double blank lines, and
    exits non-zero on any failure.
  - **Verification**: `bash scripts/test-template.sh`
  - **Files**: `scripts/test-template.sh`
  - **Touches**: `scripts/`
  - **Estimate**: 3h

- [ ] Generate `.github/dependabot.yml.jinja` — automated dependency updates per ecosystem
  - **ID**: ci-dependabot
  - **Tags**: ci, templates
  - **Details**: Generated projects get every other CI workflow but no
    Dependabot config, so dependency updates are manual. The ecosystems are the
    selected languages plus `github-actions`.
  - **Acceptance**: A rendered project with `ci_provider: github` contains
    `.github/dependabot.yml` with one `updates` entry per selected ecosystem,
    and the file is valid YAML.
  - **Verification**: `bash scripts/test-template.sh`
  - **Files**: `template/{% if ci_provider == 'github' %}.github{% endif %}/dependabot.yml.jinja`, `template/scripts/audit.py.jinja`
  - **Touches**: `template/{% if ci_provider == 'github' %}.github{% endif %}/`
  - **Estimate**: 2h

- [ ] Generate issue and pull-request templates
  - **ID**: ci-templates
  - **Tags**: ci, templates
  - **Details**: `.github/ISSUE_TEMPLATE/bug_report.yml`,
    `feature_request.yml` and `PULL_REQUEST_TEMPLATE.md` are the last pieces of
    the GitHub surface the template does not scaffold.
  - **Acceptance**: Rendered under `ci_provider: github`, all three files
    exist and parse as YAML or Markdown respectively.
  - **Verification**: `bash scripts/test-template.sh`
  - **Files**: `template/{% if ci_provider == 'github' %}.github{% endif %}/ISSUE_TEMPLATE/`
  - **Touches**: `template/{% if ci_provider == 'github' %}.github{% endif %}/`
  - **Estimate**: 2h

## P1

- [ ] Document `_skip_if_exists` entries in `copier.yml` with inline comments
  - **ID**: docs-skip-if-exists
  - **Tags**: docs
  - **Details**: Each entry protects a file an adopter is likely to have
    rewritten. That reason is not written down, so a future edit cannot tell
    which entries are load-bearing.
  - **Acceptance**: Every `_skip_if_exists` entry has an inline comment stating
    why it is protected.
  - **Verification**: `python3 -c "import yaml;yaml.safe_load(open('copier.yml'))"`
  - **Files**: `copier.yml`
  - **Touches**: `copier.yml`
  - **Estimate**: 30m

- [ ] Add a `_migrations` worked example (v1.0.0 → v1.1.0)
  - **ID**: docs-migrations
  - **Tags**: docs, copier
  - **Details**: Migrations are the one Copier feature the template documents
    but never demonstrates. A migration was attempted once and dropped after it
    turned out to be unnecessary, so there is no working reference.
  - **Acceptance**: `copier.yml` contains one migration whose command is a repo
    script, and `docs/` explains when a migration is warranted.
  - **Verification**: `python3 -c "import yaml;yaml.safe_load(open('copier.yml'))"`
  - **Files**: `copier.yml`, `scripts/`
  - **Touches**: `copier.yml`, `scripts/`
  - **Estimate**: 4h

## P2

- [ ] Audit: verify `detect.py` marks every answerable boolean toggle
  - **ID**: detect-coverage
  - **Tags**: tooling
  - **Details**: `use_commitizen` and `use_devcontainer` have no marker in
    `_registry.json` and cannot be detected. That is acceptable, but it is
    undocumented, and computed questions must never be listed (doing so
    overrides their derivation).
  - **Acceptance**: Every question in `copier.yml` is either present in
    `tool_markers` or explicitly listed as undetectable with a reason.
  - **Verification**: `python3 template/scripts/detect.py .`
  - **Files**: `template/scripts/_registry.json`, `template/scripts/detect.py`
  - **Touches**: `template/scripts/`
  - **Estimate**: 1h

- [ ] Non-Go task runner partials (Taskfile for Python, Node, Rust)
  - **ID**: taskfile-others
  - **Tags**: templates, tooling
  - **Details**: `_partials/taskfile-go.jinja` exists but has no counterpart,
    so only Go projects get a task runner.
  - **Acceptance**: A rendered Python, Node and Rust project each contains a
    `Taskfile.yml` whose targets match that language's commands.
  - **Verification**: `bash scripts/test-template.sh`
  - **Files**: `template/_partials/`
  - **Touches**: `template/_partials/`
  - **Estimate**: 3h

## P3

- [ ] Add a `toolchain` directive question to `go.mod`
  - **ID**: go-toolchain
  - **Tags**: go
  - **Details**: Go 1.21+ supports `toolchain`, which pins the compiler
    independently of the language version. The template neither emits it nor
    offers it.
  - **Acceptance**: With the new question set, `go.mod` contains a `toolchain`
    line; with it unset, `go.mod` is byte-identical to today's output.
  - **Verification**: `bash scripts/test-template.sh`
  - **Files**: `template/{% if has_go %}go.mod{% endif %}.jinja`, `copier.yml`
  - **Touches**: `template/{% if has_go %}go.mod{% endif %}.jinja`, `copier.yml`
  - **Estimate**: 1h

- [ ] SHA-pin all GitHub Actions in the generated workflows
  - **ID**: ci-pin-actions
  - **Tags**: ci, security
  - **Details**: Workflows reference `@v4`/`@v5` tags, which are mutable. Pinning
    commit SHAs is the supply-chain-hardened form; the trade-off is that updates
    must be mechanical.
  - **Acceptance**: Every `uses:` line in every rendered workflow references a
    40-character commit SHA with the version in a trailing comment.
  - **Verification**: `bash scripts/test-template.sh`
  - **Files**: `template/{% if ci_provider == 'github' %}.github{% endif %}/workflows/`
  - **Touches**: `template/{% if ci_provider == 'github' %}.github{% endif %}/workflows/`
  - **Estimate**: 2h
