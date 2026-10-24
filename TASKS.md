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

## P2

- [ ] Give a generated project one command that decides it is still sane (@opencode)
  - **ID**: check-command
  - **Tags**: tooling, ai-workflow
  - **Details**: A generated project ships `scripts/audit.py`, which checks only
    that expected files exist, and an `AGENTS.md` that lists each language's
    commands separately. An agent must therefore infer three commands per
    language and interpret three exit codes. The single signal an agent cannot
    misread is one exit status, and the repository it works in should provide
    it. Add a `--verify` mode (or a sibling `scripts/check.py`) that runs the
    declared commands for the selected languages in order and exits non-zero on
    the first failure, then have `AGENTS.md` say one line: run it before
    claiming work is done.
  - **Hypothesis**: An agent's dominant failure mode is not writing wrong code
    but declaring work finished when a formatter, a type checker or a test
    fails behind it; a single command whose exit status aggregates those
    replaces that judgement with a measurement. If a project's commands are
    already uniform enough that an agent reliably runs them, the win is smaller
    than assumed and the task should shrink to a change to `AGENTS.md` alone.
  - **Success**: A render contains one command that runs the same checks
    `AGENTS.md` documents, exits non-zero on any failure, and writes it in
    `AGENTS.md`; removing a required file makes it fail.
  - **Pivot**: If aggregating several tools' exit codes makes failures hard to
    attribute, stop at the first failure and print the command that failed
    rather than collecting all results.
  - **Measurement**: `python3 scripts/test_template.py`, plus running the new
    command in a render and deleting one source file to watch it fail.
  - **Anchor**: `scripts/audit.py` already exists and already enumerates the
    languages; `AGENTS.md` already lists the per-language commands it would
    aggregate.
  - **Acceptance**: One documented command decides the question, its exit status
    is the answer, and every generated language's checks are included.
  - **Verification**: `python3 scripts/test_template.py`
  - **Files**: `template/scripts/audit.py.jinja`, `template/AGENTS.md.jinja`
  - **Touches**: `template/scripts/`, `template/AGENTS.md.jinja`
  - **Estimate**: 2h

- [ ] Seed a generated repository map from the answers (@opencode)
  - **ID**: architecture-map
  - **Tags**: docs, ai-workflow
  - **Details**: `AGENTS.md` tells an agent to read `README.md`, which is
    written for a user, so an agent's first real failure is orientation: which
    file is the plugin, which is a manifest shim, which directory is generated.
    The render already knows every path it wrote and what each is for, so a
    one-page map listing real paths with a one-line role can be derived rather
    than written. Seed it at `docs/architecture.md`.
  - **Hypothesis**: Orientation errors — editing the wrong file confidently —
    cost more agent turns than any single wrong edit, and a derived map cannot
    drift the way prose would. If agents in practice find the entrypoint from
    `package.json` or `Cargo.toml` without it, the map is ceremony and the
    answer is not to emit one.
  - **Success**: Every path the map names exists in the same render, and the
    map is generated from the answers rather than restated by hand.
  - **Pivot**: If the map cannot be derived for a language without hand-written
    prose, restrict it to the languages that can and record the gap rather than
    inventing descriptions.
  - **Measurement**: `python3 scripts/test_template.py`, plus checking that each
    path named in a render's map exists in that render.
  - **Anchor**: `AGENTS.md` already describes the layout in prose and points at
    `docs/`; the render's own file list is the authoritative source for what
    exists.
  - **Acceptance**: A render's map names only existing paths, and a missing
    map path fails the matrix.
  - **Verification**: `python3 scripts/test_template.py`
  - **Files**: `template/docs/architecture.md.jinja`, `template/AGENTS.md.jinja`
  - **Touches**: `template/docs/`, `template/AGENTS.md.jinja`
  - **Estimate**: 1h

- [ ] Run the queue's own Verification commands (@opencode)
  - **ID**: tasks-status
  - **Tags**: tooling, ai-workflow
  - **Details**: The task contract says a task is removed only when its
    `**Verification**` command succeeds, but nothing executes them, so the queue
    is honour-system. A script that parses `TASKS.md`, runs each Verification
    with a timeout, and reports `open`/`passing`/`broken` lets an agent read the
    queue's truth instead of trusting a checkbox. A task whose Verification
    already passes is either done or mis-stated; both are actionable.
  - **Hypothesis**: A queue whose stated verification is never run accumulates
    tasks that are already done and tasks whose verification no longer means
    what it says, and an agent reading it cannot tell which. If most
    Verifications turn out to be non-runnable or trivially green, the field is
    being written as prose and the fix belongs in the task format, not a script.
  - **Success**: Running it against this repository reports a status per task
    and exits non-zero when any Verification fails, with per-command timeouts so
    one hang does not stall the run.
  - **Pivot**: If arbitrary shell in a task field is too dangerous to execute
    automatically, restrict the script to reporting the commands and their last
    known status, and record that execution is manual.
  - **Measurement**: `python3 scripts/tasks_status.py` against this repository's
    own `TASKS.md`, whose commands (the render matrix) are known to run.
  - **Anchor**: Every task in this file carries a runnable Verification; the
    template's own `TASKS.md` contract states the removal rule the script would
    enforce.
  - **Acceptance**: The script reports one status per task, honours a timeout,
    and its own Verification is that it runs clean on this repository.
  - **Verification**: `python3 scripts/tasks_status.py --check`
  - **Files**: `scripts/tasks_status.py`
  - **Touches**: `scripts/`
  - **Estimate**: 1.5h

- [ ] Investigate GitHub Codespaces as a second container target (@opencode)
  - **ID**: codespaces-config
  - **Tags**: ci, devcontainer
  - **Details**: The `use_devcontainer` answer emits a generic
    `mcr.microsoft.com/devcontainers/base:ubuntu` image with one
    `ghcr.io/devcontainers/features/*` entry per selected language. Codespaces
    reads the same file, so a project may already open there — but nothing has
    tested whether it actually works, and nothing records what Codespaces adds
    that the local devcontainer path does not need, or needs that the render
    does not provide.
  - **Acceptance**: A written recommendation answers whether the template should
    emit a Codespaces-specific configuration at all, and if so which file
    (`.devcontainer/devcontainer.json` kept as-is, a
    `.devcontainer/codespaces.json`, or `.devcontainer/<name>/devcontainer.json`)
    — each option justified by what Codespaces reads rather than asserted. Any
    template change lands as its own queued task; this one only decides.
  - **Hypothesis**: Codespaces reads the same `.devcontainer/devcontainer.json`
    the local path already emits, so the template needs no second file; what it
    may need is a feature or setting the generic render omits, such as a
    non-root user, a forwarded port, or a host requirement Codespaces cannot
    satisfy. If instead the file renders identically in both contexts and both
    open, the correct outcome is to record that and change nothing.
  - **Success**: The recommendation cites at least one measured fact per option
    — a Codespaces build log, a `devcontainer` CLI build, or the Codespaces
    documentation for what overrides what — and names the file the template
    should or should not emit, with the reason it cannot be inferred from the
    current answers.
  - **Pivot**: If Codespaces cannot be exercised without a paid account or a
    push to a GitHub repository, the deliverable becomes a documentation record
    of what is unknowable locally and what a maintainer must test by hand, and
    the answer is to emit nothing until that happens.
  - **Measurement**: `devcontainer build --workspace-folder .` against a
    `use_devcontainer` render, plus the Codespaces documentation for config
    precedence; neither exists in the repo today.
  - **Anchor**: The devcontainer answer already renders
    `devcontainer.json` with per-language `ghcr.io/devcontainers/features/*`
    entries; GitHub documents Codespaces as reading the same dev container
    configuration.
  - **Verification**: `test -f docs/records/codespaces.md && rg -q 'devcontainer.json' docs/records/codespaces.md`
  - **Files**: `docs/records/codespaces.md`
  - **Touches**: `docs/`
  - **Estimate**: 2h

## P3
