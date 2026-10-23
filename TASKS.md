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

- [ ] Create `scripts/test_template.py` — render matrix as a repo script
  - **ID**: test-harness
  - **Tags**: tooling, ci
  - **Details**: The 18-config render matrix currently lives in
    `/tmp/opencode/matrix.sh`, which is scratch and disappears. It is the only
    thing that verifies a template change; it belongs in the repo.
  - **Acceptance**: `scripts/test_template.py` renders every config, asserts
    audit Grade A, `@tasks-md/lint` zero errors and no double blank lines, and
    exits non-zero on any failure.
  - **Verification**: `python3 scripts/test_template.py`
  - **Files**: `scripts/test_template.py`
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
  - **Verification**: `python3 scripts/test_template.py`
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
  - **Verification**: `python3 scripts/test_template.py`
  - **Files**: `template/{% if ci_provider == 'github' %}.github{% endif %}/ISSUE_TEMPLATE/`
  - **Touches**: `template/{% if ci_provider == 'github' %}.github{% endif %}/`
  - **Estimate**: 2h

- [ ] Restore `bun` as a `node_runtime` choice (@opencode)
  - **ID**: node-bun-runtime
  - **Tags**: node, templates
  - **Hypothesis**: All six opencode-* plugin repos are bun-native — `bun test`
    with `bun:test` imports across 23 test files, `type: module`, and
    TypeScript shipped directly with no build step. Bun was trimmed from
    `node_runtime` on the belief that it was unreachable; if the template is
    ever applied to them it must emit `bun test`, not `node --test`, or every
    test file fails to resolve its imports.
  - **Success**: A render with `node_runtime=bun` emits `"test": "bun test"` in
    `package.json`, a bun setup step in `node.yml`, and no `node --test`
    anywhere in the output. `node_test_runner` returns `bun test`.
  - **Pivot**: If bun-as-runtime produces the same output as bun-as-package-
    manager in every file, collapse the two questions instead and record why.
  - **Measurement**: `python3 scripts/test_template.py`
  - **Anchor**: The six repos at `~/repos/pngdeity/active/opencode-*`; bun's
    test runner is the documented `bun test` entrypoint
    (https://bun.sh/docs/cli/test).
  - **Details**: `node_runtime` is `node | deno` (`copier.yml:215-222`);
    `node_test_runner` hardcodes `node --test` for the node branch. Bun exists
    only as a `node_package_manager` value, where it affects the install and
    invoke commands but not the script body. Adding the runtime means also
    adding a bun branch to `node-ci-setup.jinja` and to the `test` job.
  - **Acceptance**: `node_runtime` offers `bun`; `node_test_runner` returns
    `bun test`; `node.yml` installs bun and runs `bun test`; the
    `node_purpose`/`node_build` validators still exclude deno as before.
  - **Verification**: `python3 scripts/test_template.py`
  - **Files**: `copier.yml`, `template/_partials/node-ci-setup.jinja`,
    `template/{% if ci_provider == 'github' %}.github{% endif %}/workflows/{% if has_node %}node.yml{% endif %}.jinja`,
    `template/{% if has_node and node_runtime != 'deno' %}package.json{% endif %}.jinja`
  - **Touches**: `copier.yml`, `template/_partials/`, `template/{% if ci_provider == 'github' %}.github{% endif %}/workflows/`
  - **Estimate**: 2h

- [ ] Emit `peerDependencies`, `keywords` and `author` in `package.json` (@opencode)
  - **ID**: node-manifest-peer
  - **Tags**: node, templates
  - **Hypothesis**: The plugin repos declare `@opencode/plugin`,
    `@opentui/core`, `@opentui/solid` and `solid-js` as `peerDependencies`,
    because the host application provides them. If the template cannot express
    a peer dependency, an adopted project either omits the declaration — and
    npm bundles a second copy of the host runtime — or keeps a hand-written
    manifest the template never touches. `author` and `keywords` affect all
    six repos; peers affect the one that renders a TUI.
  - **Success**: A render with the peer set to `@opencode/plugin` contains a
    `peerDependencies` block naming it, plus `author` and `keywords` when those
    answers are non-empty.
  - **Pivot**: If a free-text peers answer makes the question surface
    unmanageable, emit an empty `peerDependencies: {}` with a comment and
    record that as the ceiling.
  - **Measurement**: `python3 scripts/test_template.py`
  - **Anchor**: The six repos' `package.json` files; npm documents
    `peerDependencies` as the mechanism for host-provided packages
    (https://docs.npmjs.com/cli/configuring-npm/package-json#peerdependencies).
  - **Details**: `package.json.jinja` emits `name`, `version`, `private`,
    `type`, `description`, `license`, `sideEffects`, `files`, `main`, `types`,
    `exports`, `engines`, `repository`, `homepage`, `bugs`, `publishConfig`,
    `scripts` and `devDependencies` — and nothing else. `author`, `keywords`
    and `peerDependencies` are absent entirely.
  - **Acceptance**: All three fields are emitted when their source answer is
    non-empty, and omitted cleanly when it is empty.
  - **Verification**: `python3 scripts/test_template.py`
  - **Files**: `copier.yml`, `template/{% if has_node and node_runtime != 'deno' %}package.json{% endif %}.jinja`
  - **Touches**: `copier.yml`, `template/{% if has_node and node_runtime != 'deno' %}package.json{% endif %}.jinja`
  - **Estimate**: 2h

- [ ] Support subpath `exports` and negated `files` for library packages (@opencode)
  - **ID**: node-subpath-exports
  - **Tags**: node, templates
  - **Hypothesis**: The plugin repos export `./server`, `./tui`, `./core`,
    `./descriptors` and `./occupancy-metric` as separate entrypoints, and use
    `files: ["index.ts", "src/", "!**/*.test.ts"]` so tests do not publish. The
    template emits a single `"."` export and a non-negatable `files: ["src"]`,
    so an adopted library either publishes its tests or hand-maintains the
    manifest.
  - **Success**: A render declaring two subpaths emits both in `exports` with
    their own `types`/`import` conditions, and a `!**/*.test.ts` exclude
    survives into `files`. `npm pack --dry-run` lists no `.test.ts` file.
  - **Pivot**: If arbitrary subpath answers are too free-form to validate,
    restrict to a declared list of common names and record the limit.
  - **Measurement**: `python3 scripts/test_template.py`
  - **Anchor**: The six repos' `exports` and `files` blocks; npm documents
    subpath exports (https://nodejs.org/api/packages.html#subpath-exports) and
    negation in `files` (https://docs.npmjs.com/cli/configuring-npm/package-json#files).
  - **Details**: `package.json.jinja` has one `exports` object keyed `"."`
    whose shape varies only by `node_build`, and a `files` array of either
    `["src"]` or `["dist"]`.
  - **Acceptance**: Both capabilities are answer-driven; the default render is
    unchanged.
  - **Verification**: `python3 scripts/test_template.py`
  - **Files**: `copier.yml`, `template/{% if has_node and node_runtime != 'deno' %}package.json{% endif %}.jinja`
  - **Touches**: `copier.yml`, `template/{% if has_node and node_runtime != 'deno' %}package.json{% endif %}.jinja`
  - **Estimate**: 3h

- [ ] Point no-build libraries at the `.ts` source they actually ship (@opencode)
  - **ID**: node-build-none-entrypoint
  - **Tags**: node, templates
  - **Hypothesis**: With `node_build: none` and `node_purpose: library` the
    template emits `main: ./src/index.js`, `types: ./src/index.d.ts` and
    `exports` conditions of the same shape, while shipping `.ts` sources and no
    compiler. The no-build branch hardcodes a `.js`/`.d.ts` contract that only
    a compiled package can honour, so the source-pointing shape — the one
    OpenCode documents — is inexpressible. This breaks a `node`-runtime library
    too, so it is distinct from the bun runtime gap.
  - **Success**: A render with `node_build=none` and `node_purpose=library`
    emits `main`, `types` and `exports` pointing at files that exist in the
    output tree, never at a build artefact no step produces.
  - **Pivot**: If the OpenCode-documented `.ts` export (see
    `node-plugin-entrypoints`) makes `main`/`types` meaningless for this case,
    drop them entirely and export only subpaths, recording why.
  - **Measurement**: `python3 scripts/test_template.py`
  - **Anchor**: Source-pointing is supported, not merely documented, on two
    independent counts. The OpenCode V2 plugin docs' own manifest example
    exports `./src/index.ts`, and OpenCode's
    `packages/util/src/runtime/import.node.ts` carries an explicit `.ts`-first
    extension retry (`[".ts", ".tsx", ".js", …]`) so such an export resolves
    under Node. Its `packages/util/package.json` likewise points `exports` at
    `./src/*.ts` while declaring `files: ["dist"]`. A render
    `--data node_build=none --data node_purpose=library` writes `src/.gitkeep`
    only while `package.json` names `./src/index.js`.
  - **Details**: `package.json.jinja`'s `node_build == 'none'` branch is shared
    between application and library. For an application the entrypoints are
    harmless; for a library they are the published contract.
  - **Acceptance**: `node_build=none` libraries reference only files the render
    creates, and the application branch is unchanged.
  - **Verification**: `python3 scripts/test_template.py`
  - **Files**: `copier.yml`, `template/{% if has_node and node_runtime != 'deno' %}package.json{% endif %}.jinja`
  - **Touches**: `copier.yml`, `template/{% if has_node and node_runtime != 'deno' %}package.json{% endif %}.jinja`
  - **Estimate**: 1h

- [ ] Add `node_purpose: plugin` with `server`/`tui` entrypoints (@opencode)
  - **ID**: node-plugin-entrypoints
  - **Tags**: node, templates
  - **Hypothesis**: An OpenCode plugin is not imported by a consumer; the host
    loads it by entrypoint name. `packages/plugin/src/host.ts` resolves
    `entry(["server", ""])`, `entry(["tui"])` and `entry(["rpc"])` — named
    subpath first, then the bare package name — and the V2 CLI docs state a
    path-loaded plugin resolves `<package>/server` and `<package>/tui` from the
    package root rather than through `exports`. Publishers therefore emit named
    entrypoints (Codestz exports `./server`, `./tui`, `./config`, `./segment`
    and no `"."`), and those with a build add one-line root shims re-exporting
    from `dist/`. The `application`/`library` split cannot express this, so
    every plugin project hand-maintains its manifest.
  - **Success**: A render with `node_purpose=plugin` emits `./server` and
    `./tui` exports with no `"."`, `engines.opencode`, and `keywords`
    containing `opencode-plugin`; entrypoints point at `.ts` sources the render
    creates when there is no build, and at `dist/*.js` behind root shims when
    there is. `library` and `application` renders are byte-identical to today's
    output.
  - **Pivot**: If a third purpose multiplies the manifest branches beyond
    readability, express the plugin shape as an `exports` override on
    `library` and record the lost guard.
  - **Measurement**: `python3 scripts/test_template.py`
  - **Anchor**: `Codestz/opencode-cockpit` `packages/status/package.json` and
    its `server.js`/`tui.js` shims, whose header comment records the
    path-vs-exports rule; `mynameistito/opencode-plugins`;
    `anomalyco/opencode` `packages/plugin/src/host.ts` and
    `packages/util/src/npm.ts`. That last file is decisive for the no-build
    case: npm install sets `ignoreScripts: true`, so `prepack`/`prepare` never
    run on a user's machine and nothing can be built at install time.
  - **Details**: `node_purpose` currently offers `application` and `library`,
    with `library` validator-gated on non-deno. `package.json.jinja` branches
    on `is_node_library` throughout (`private`, `sideEffects`, `files`, `main`,
    `types`, `exports`, `prepack`). The plugin shape needs all of those plus
    the entrypoint pair, so it is a genuine third branch rather than a flag.
    Whether a build exists decides *what* the entrypoints point at, not
    whether they exist.
  - **Acceptance**: The new value renders a manifest a plugin can be loaded
    from, `is_node_library` keeps its current meaning for the other two
    values, and `detect.py` has no new answer to infer (the question is not
    detectable from markers).
  - **Verification**: `python3 scripts/test_template.py`
  - **Files**: `copier.yml`, `template/{% if has_node and node_runtime != 'deno' %}package.json{% endif %}.jinja`,
    `template/{% if ci_provider == 'github' %}.github{% endif %}/workflows/{% if has_node %}node.yml{% endif %}.jinja`
  - **Touches**: `copier.yml`, `template/`
  - **Estimate**: 4h

- [ ] Prove the published artefact exists before `publish.yml` runs `npm publish` (@opencode)
  - **ID**: node-build-publish-guard
  - **Tags**: ci, node
  - **Hypothesis**: `publish.yml` calls `npm publish` directly, with a comment
    claiming "prepack runs the build and the tests". That holds only when
    publishing from a machine where scripts run; the guard is load-bearing
    because OpenCode's own installer sets `ignoreScripts: true`, so nothing a
    consumer does will ever build this package. A build that silently fails
    publishes a package whose declared entrypoints do not exist.
  - **Success**: A render with `node_build: tsc` and a library purpose
    publishes only after a step that fails when `dist/` is absent or a
    declared `main`/`exports` path does not exist on disk.
  - **Pivot**: If proving `dist/` is awkward across package managers, fall
    back to asserting every path declared in `main` and `exports` exists,
    which is the property that actually matters.
  - **Measurement**: `python3 scripts/test_template.py`
  - **Anchor**: `template/{% if ci_provider == 'github' %}.github{% endif %}/workflows/{% if is_node_library %}publish.yml{% endif %}.jinja`
    runs `node-ci-setup.jinja` then bare `npm publish`;
    `anomalyco/opencode` `packages/util/src/npm.ts` sets `ignoreScripts: true`.
  - **Details**: The workflow trusts `prepack` implicitly. Adding an explicit
    assertion makes the failure mode a red step rather than a broken release,
    and costs one job step.
  - **Acceptance**: The guard is skipped for `node_build: none` (where it
    would be wrong to demand `dist/`), present for every build value, and the
    default render is unchanged.
  - **Verification**: `python3 scripts/test_template.py`
  - **Files**: `template/{% if ci_provider == 'github' %}.github{% endif %}/workflows/{% if is_node_library %}publish.yml{% endif %}.jinja`
  - **Touches**: `template/{% if ci_provider == 'github' %}.github{% endif %}/workflows/`
  - **Estimate**: 1h

- [ ] Stop protecting `package.json` in `_skip_if_exists` on adoption (@opencode)
  - **ID**: skip-package-manifest
  - **Tags**: copier, templates
  - **Hypothesis**: `package.json` is in `_skip_if_exists` so that `copy` and
    `update` never clobber a hand-written manifest. On adoption that means the
    Node answers govern nothing: the template's `node_runtime`, `node_purpose`
    and `node_build` write other files while the manifest keeps whatever the
    adopter had, and the two can disagree silently.
  - **Success**: Adopting a repo with an existing `package.json` either
    preserves it *and* records that the Node answers were not applied, or
    regenerates it — not the current silent middle.
  - **Pivot**: If raising adoption the merge burden is too high, keep the
    protection but emit a `package.json.template` beside it and record the
    refusal to merge.
  - **Measurement**: `python3 scripts/test_template.py`
  - **Anchor**: `_skip_if_exists` is Copier's documented "do not overwrite in
    an existing project" list
    (https://copier.readthedocs.io/en/stable/configuring/#skip_if_exists).
  - **Details**: `copier.yml` `_skip_if_exists` lists `package.json` among the
    human-owned documents (`README.md`, `AGENTS.md`, `CHANGELOG.md`, …). For a
    manifest with machine-derived fields that grouping is wrong.
  - **Acceptance**: The adoption behaviour is explicit, documented in
    `TOOLING.md`, and exercised by a test config.
  - **Verification**: `python3 scripts/test_template.py`
  - **Files**: `copier.yml`, `TOOLING.md`, `scripts/test_template.py`
  - **Touches**: `copier.yml`, `TOOLING.md`, `scripts/`
  - **Estimate**: 2h

- [ ] Teach `detect.py` the non-root surfaces the plugin repos use (@opencode)
  - **ID**: detect-plugin-surface
  - **Tags**: tooling
  - **Hypothesis**: Detection maps only root-level markers, so a repo whose
    Python lives in `bin/*.py`, whose units live in `share/systemd/user/` and
    whose records live in `docs/records/` is detected as
    `languages=["javascript"]` and nothing else. Feeding that to `copier adopt`
    silently drops the Python language, its tooling and its CI.
  - **Success**: Running `detect.py` on `opencode-codeintel` reports `python`
    among the languages, with the reason recorded; every answer it emits is one
    `copier.yml` accepts.
  - **Pivot**: If nested detection produces false positives on unrelated repos,
    restrict it to explicitly configured subdirectories and record the limit.
  - **Measurement**: `python3 template/scripts/detect.py ../opencode-codeintel`
  - **Anchor**: The six repos at `~/repos/pngdeity/active/opencode-*`;
    `opencode-codeintel` tracks `bin/*.py` and `share/systemd/user/*.service`.
  - **Details**: `_registry.json` `language_markers` are root-relative
    filenames (`pyproject.toml`, `package.json`, `go.mod`, `*.csproj`, `*.tf`).
    `tool_markers` likewise. `detect.py` globs the repo root only.
  - **Acceptance**: A documented set of nested markers is recognised, the
    emitted `--data` string feeds a successful `copier copy`, and the
    limitation is recorded for any surface still undetectable.
  - **Verification**: `python3 template/scripts/detect.py ../opencode-codeintel`
  - **Files**: `template/scripts/_registry.json`, `template/scripts/detect.py`
  - **Touches**: `template/scripts/`
  - **Estimate**: 3h

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

- [ ] Replace the README `## Usage` placeholder with a real first-run path (@opencode)
  - **ID**: readme-usage-section
  - **Tags**: docs, templates
  - **Hypothesis**: `## Usage` renders as a fenced block containing only
    `# Replace with the smallest runnable example.` It is the one section a
    consumer needs most, and it ships empty — worse, it ships *as a command
    block*, which reads as runnable and is not. Every other placeholder in the
    template is prose inside a `[!NOTE]`, so the reader can tell it is
    unfinished; this one imitates the finished article.
  - **Success**: A fresh render's `## Usage` contains either a runnable command
    drawn from the answers already given (the install command, the test
    command, or the module's declared entrypoint) or prose that is visibly a
    placeholder, and never a fenced block whose only line is a comment.
  - **Pivot**: If no answer yields a truthful command for a given project
    shape, omit the section entirely rather than emit an empty one, and record
    which shapes have no defensible usage text.
  - **Measurement**: `python3 scripts/test_template.py`, asserting no rendered
    `README.md` matches a fence whose body is a single `#` comment.
  - **Anchor**: `template/README.md.jinja` lines 45-49 hold the placeholder;
    `copier.yml`'s `repo_description` and the language answers already supply
    the material for a truthful line, and `template/_partials/development.jinja`
    already renders exact commands per language — the Usage section is the only
    one that does not use them.
  - **Details**: The template cannot know what the code does, which is why the
    placeholder exists. But it can know the install command and the test
    command, both already computed (`node_install_cmd`, `node_test_cmd`,
    `uv sync`, `go build`, …). Whether to emit those under `## Usage`, point at
    `## Development`, or drop the heading is the decision worth recording.
  - **Acceptance**: No rendered README contains a one-line comment fence under
    `## Usage`; the default render is either truthful or honestly empty, and
    the choice is written down next to the template.
  - **Verification**: `python3 scripts/test_template.py`
  - **Files**: `template/README.md.jinja`
  - **Touches**: `template/README.md.jinja`
  - **Estimate**: 1h

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
