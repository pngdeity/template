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

- [ ] Research: decide what `docs/` should contain (@opencode)
  - **ID**: docs-corpus-shape
  - **Tags**: docs, research
  - **Hypothesis**: The template ships `docs/` as an empty `.gitkeep` while
    `AGENTS.md`, `README.md` and `CONTRIBUTING.md` all send long-form decisions
    there. A scaffolded project gets a directory every document points at and
    no statement of what goes in it, what to name a file, or how large a
    decision warrants one. The cost is not the missing content — it is that the
    convention stays unwritten, so each project invents a different one and the
    pointer becomes decoration.
  - **Success**: A decision recorded in `docs/` naming the document set a
    generated project should start with, the naming rule for a new file, and
    the threshold at which a decision deserves a file rather than a commit
    message — each justified by an example corpus rather than asserted, and
    restated as a concrete template change (seed files, an `AGENTS.md` line, or
    nothing, with the reason nothing is needed).
  - **Pivot**: If the evidence supports no seed files at all, the deliverable
    is a single-line convention in `AGENTS.md` saying so, and the `.gitkeep`
    stays; record that outcome rather than adding a directory README for its
    own sake.
  - **Measurement**: `ls docs` in a fresh render (currently `.gitkeep` only),
    plus the number of documents the render's own prose points at
    (`rg -n 'docs/'` across rendered AGENTS/README/CONTRIBUTING).
  - **Anchor**: Counter-examples are plentiful in the survey already done — the
    six `opencode-*` repos carry `docs/INSTALL.md`, `docs/architecture.md`,
    `docs/records/` (one file per settled incident, with a `README.md` index);
    `Codestz/opencode-cockpit` keeps `docs/` beside a `site/`;
    `anomalyco/opencode` keeps `docs/opencode/v2.md` referenced from source
    comments. Read `opencode-codeintel/docs/records/README.md` and this
    template repo's own `docs/` (`records/`, `projects/`, `reference/`,
    `graduation-rule.md`) for the closest precedent.
  - **Details**: Today `docs/` exists only because a `.gitkeep` was added;
    `template/README.md.jinja` links it as `[docs/](docs/)` in the Overview
    placeholder text, and `AGENTS.md.jinja` says "long-form decisions belong in
    `docs/`". Neither says what to write. Two candidate shapes to compare: a
    single `docs/README.md` index plus free-form files, versus the sibling
    repo's bucketed `records/` + `projects/` + `reference/` layout with a
    graduation rule. The second is heavier and may be wrong for a scaffold.
  - **Acceptance**: A written recommendation answers (a) which files, if any, a
    new project starts with, (b) how a new document is named, (c) when a
    decision gets a file, and (d) whether the template should seed them — each
    with the evidence behind it. Any resulting template edit is queued as its
    own task rather than bundled here.
  - **Verification**: `test -f docs/README.md || rg -q 'docs/' AGENTS.md` in a
    fresh render, plus the written recommendation existing in the repo's own
    `docs/`.
  - **Files**: `docs/` (the research note), then whichever of
    `template/docs/`, `template/AGENTS.md.jinja`, `template/README.md.jinja`
    the recommendation selects.
  - **Touches**: `docs/`, possibly `template/`
  - **Estimate**: 2h

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
