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

## P2

- [ ] Non-Go task runner partials (Taskfile for Python, Node, Rust)
  - **ID**: taskfile-others
  - **Tags**: templates, tooling
  - **Details**: `_partials/taskfile-go.jinja` exists but has no counterpart,
    so only Go projects get a task runner.
  - **Acceptance**: A rendered Python, Node and Rust project each contains a
    `Taskfile.yml` whose targets match that language's commands.
  - **Verification**: `python3 scripts/test_template.py`
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
  - **Verification**: `python3 scripts/test_template.py`
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
  - **Verification**: `python3 scripts/test_template.py`
  - **Files**: `template/{% if ci_provider == 'github' %}.github{% endif %}/workflows/`
  - **Touches**: `template/{% if ci_provider == 'github' %}.github{% endif %}/workflows/`
  - **Estimate**: 2h
