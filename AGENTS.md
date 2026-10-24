# AGENTS.md

## What this repo is

A [Copier](https://copier.readthedocs.io/) template that scaffolds standardized
Git repositories. Not an application or library — there is no build, test
suite, or runtime.

The template source lives under `template/` (`_subdirectory: template` in
`copier.yml`). Root-level files (`.gitignore`, `.editorconfig`, `.gitattributes`,
etc.) are for this template repo itself and are not rendered by Copier. The
`template/` tree has its own copies of the files that *are* rendered, so a
change meant for generated projects belongs there, not at the root.

## File naming conventions

Files use a **`.jinja` suffix** that Copier strips during generation
(`_templates_suffix: .jinja`). Edit the `.jinja` file, not the rendered name.

**The suffix must sit outside any Jinja block.** A name like
`{% if has_go %}go.yml.jinja{% endif %}` is not a template: Copier copies it
verbatim, so generated repos get a file literally named `go.yml.jinja`
containing unevaluated `{% raw %}` markers. The correct form is
`{% if has_go %}go.yml{% endif %}.jinja`.

**Directory and file names contain Jinja2 blocks** (`{% if %}`, `{% endif %}`).
These are literal filesystem names — treat them as opaque. Shell globbing,
`find`, and tab-completion will break on them. Always quote or escape
shell arguments that touch the `template/` tree. Example:

```
template/{% if has_go %}go.mod{% endif %}.jinja
template/{% if 'python' in languages %}src{% endif %}/
```

The `_partials/` directory holds reusable Jinja snippets (included via `{% include 'template/_partials/…' %}`,
note the path is relative to the template root, not to the including file).
It is excluded from output (`_exclude` in `copier.yml`). Never add content
to `_partials/` that should appear directly in generated repos.

## Writing jinja in template files

`copier.yml` sets `_envops` to `trim_blocks: true`, `lstrip_blocks: true`, and
`undefined: jinja2.StrictUndefined`. Practical consequences:

- `trim_blocks` eats the newline after a block tag. A file ending in a
  conditional needs symmetric trim markers on both branches (`{% if x -%}` …
  `{% endif -%}`), or it renders with a missing or doubled final newline.
- `StrictUndefined` means a typo in a variable name fails the render instead
  of rendering empty. Only names defined in `copier.yml` are available.
- Copier applies its own `keep_trailing_newline: true` default on top of the
  partial `_envops` override, so that setting does not need restating.
- Literal output that looks like Jinja (Go templates in `.terraform-docs.yml`,
  `${{ }}` in GitHub Actions) must be escaped with `{{ '{{' }}`, or wrapped in
  `{% raw %}` preceded by a whitespace-controlled comment (`{#- -#}`) so
  `trim_blocks` has already fired. A bare `{% raw %}` line on its own produces
  a blank-line offset.

## How to test a template change

`scripts/test_template.py` is the render matrix: it scaffolds 30 answer
combinations and checks each output for parseable JSON, parseable workflows,
unevaluated Jinja, `@tasks-md/lint` errors, audit grade below A, a missing
declared entrypoint, and double blank lines. Run it, do not eyeball a render:

```bash
python3 scripts/test_template.py            # all configs, skipping ones already passed
python3 scripts/test_template.py --full     # ignore the pass cache
python3 scripts/test_template.py --changed  # only configs a dirty path can reach
python3 scripts/test_template.py ts-bun     # named configs
```

`--changed` reads `git status` and narrows to the configs whose answers the
touched template files are conditioned on; a change to `copier.yml`, to
`_partials/`, or to an unconditional template file expands to every config.
The pass cache is keyed on a hash of the whole tree, so any edit invalidates it
and a cached result never stands in for a render of the change under test.
`--shard N/M` splits the list for CI; it is not a development flag.

A config that passes proves the shape, not the intent: add one whenever you
add an answer combination the matrix does not already cover. `node_lint` must be
set explicitly wherever the package manager is `bun` or `pnpm`, because `deno` is
the default and is refused for those installers. Never set `use_precommit=true`
in a config: the post-generation task runs `pre-commit install`, which aborts
when `core.hooksPath` is set.

To inspect one render by hand:

```bash
copier copy --trust --defaults --vcs-ref HEAD . /tmp/test-output \
  --data repo_name=test-project \
  --data 'languages=[python, go]' \
  --data use_precommit=false
```

Always pass `--vcs-ref HEAD`: without it Copier renders the last git tag, not
the working tree.

`languages` is a `yaml` multiselect, so it takes a YAML list, not a comma
string. Valid choices are `python`, `javascript`, `typescript`, `go`, `rust`,
`dotnet`, `tofu`. `ci_provider` accepts only `github`, and only when at least
one language is selected; otherwise it offers only `none`.

For `copier adopt` (applying to an existing project), run
`template/scripts/detect.py` against the target repo to produce the `--data`
flags, then `copier adopt` with them. The script is not rendered into
generated projects — it is a development tool here. Note that a boolean which
defaults to `true` in `copier.yml` is indistinguishable from an absent marker
in the target repo, so `detect.py` reports it as a change even when it is
already the effective value.

## Key files and their roles

| File                              | Role                                                                     |
| --------------------------------- | ------------------------------------------------------------------------ |
| `copier.yml`                      | Template questions, computed vars, post-generation tasks, version config |
| `template/`                       | All files that get rendered into new projects (the `_subdirectory`)      |
| `template/_partials/`             | Reusable Jinja snippets — never rendered directly                        |
| `template/AGENTS.md.jinja`        | Generated repo's agent instructions (table of contents, not a manual)    |
| `template/TASKS.md.jinja`         | Generated task queue, carrying its own agent contract                    |
| `template/scripts/detect.py`      | Detection script for `copier adopt` — development tool, not rendered     |
| `template/scripts/_registry.json` | Markers that `detect.py` uses to identify languages and tools            |
| `template/scripts/audit.py.jinja` | Compliance audit script — generated at scaffold time                     |
| `scripts/test_template.py`        | The render matrix; development tool, never rendered into a project       |
| `scripts/migrations/`             | Migration scripts referenced by `_migrations`; development tool as well  |
| `TASKS.md`                        | Development task queue for the template itself, in the `tasks.md` format |
| `TOOLING.md`                      | Source of truth for LSP and formatter choices                            |

## Copier.yml conventions

- `when: false` on a question marks a computed/internal variable (not shown to the user).
- `when: "{{ condition }}"` makes a question conditional on prior answers.
- `_skip_if_exists` lists files Copier will not overwrite in existing projects
  during `adopt`. It protects the documents a human is most likely to have
  rewritten (`README.md`, `AGENTS.md`, `TASKS.md`, `CHANGELOG.md`, the optional
  `SECURITY.md`/`CONTRIBUTING.md`, and `.env`), so treat anything added to it as
  permanently the adopter's to maintain. Derived files — `package.json`, the
  workflows, the tool configs — are deliberately absent so `update` keeps them
  in step with the answers. `.gitignore` is absent for a different reason: it is
  rewritten like a derived file, so it ends with an adopter-rules marker and the
  generated half above that marker is what the template owns. Skipping it instead
  would leave an adopting checkout with none of the generated rules.
- `_tasks` are shell commands that run after generation (git init, pre-commit
  install, upstream wiring).
- `_jinja_extensions` include `jinja2_time.TimeExtension`. The system copier
  does not ship it, so a copier without that extension cannot render this
  template at all; `test_template.py` probes for one that can.
- `_migrations` entries use a PEP 440 version string; see `TOOLING.md` for when
  a migration is warranted and what the command must do.
- A boolean toggle usually gates both a rendered file's name and an entry in
  `template/scripts/_registry.json`; adding one means editing both, plus the
  conditional list in `template/scripts/audit.py.jinja`.

## Template variable scope

Template variables are referenced via `{{ var_name }}` in `.jinja` files.
Variables defined in `copier.yml` (including computed ones with `when: false`)
are available in all template files. Language helpers: `has_python`, `has_node`,
`has_go`, `has_rust`, `has_dotnet`, `has_tofu`, `has_typescript`.

Beyond those, a handful of computed flags answer "which tool set does this
project need", and a template that branches on a tool should ask the flag rather
than re-test the answers that produced it: `is_node_library`, `is_node_plugin`,
`has_node_build`, `uses_deno`, `uses_bun`. Adding a choice to a Node question
usually means updating one of these in `copier.yml` and the `TOOLING.md` table,
not every file that branches.

Note that directory names use the raw `in languages` test rather than the
`has_*` helpers (e.g. `{% if 'python' in languages %}src{% endif %}`); both
forms work, but a new helper should follow whichever the surrounding file uses.

## Style and tooling

- Markdown linting: `rumdl`, reading `template/.rumdl.toml`. The config lives
  under `template/` but governs this repo's own Markdown too, since rumdl walks
  up from the file being checked.
- YAML formatting: `yamlfmt` with `template/.yamlfmt.yaml` config.
- Python in `scripts/`: `ruff check`, `ruff format --check`, `mypy`. These cover
  the development tools only; nothing outside `template/` is rendered, so a
  generated project never sees them.
- Indentation: 2-space default, language-specific overrides in `.editorconfig`
  (4 for Python, C#, Rust; tabs for Makefile, shell, Go, PKGBUILD).
  Generated projects get language-tool configs matching the matrix in `TOOLING.md`.
- Shell scripts use tabs (per `.editorconfig`).
- Commit messages follow Conventional Commits (see `_partials/conventional-commits.jinja`).

## Do not edit

- `.rumdl_cache/` — rumdl's cache, ignore it.
- Files under `template/` that are `.gitkeep` placeholders.
