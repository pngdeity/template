# Tooling

Source of truth for LSP servers and formatters in use. Derive editor configs, CI checks, and pre-commit hooks from this document.

## LSP and formatter matrix

| Language             | File extension                               | LSP binary                   | Formatter binary | Config File(s)                    | Format                     |
| -------------------- | -------------------------------------------- | ---------------------------- | ---------------- | --------------------------------- | -------------------------- | --- |
| Bash / Shell         | `.sh`, `.bash`, `.zsh`, `.ksh`, `PKGBUILD`   | `bash-language-server`       | `shfmt`          | `.editorconfig`                   | EditorConfig               |
| C#                   | `.cs`, `.csx`                                | `roslyn-language-server`     | `csharpier`      | `.csharpierrc`* / `.editorconfig` | JSON / YAML / EditorConfig |
| C# (Razor)           | `.razor`                                     | `roslyn-language-server`     | `csharpier`      | `.csharpierrc`* / `.editorconfig` | JSON / YAML / EditorConfig |
| CSS                  | `.css`, `.scss`, `.sass`, `.less`            | —                            | `deno`           | `deno.json`                       | JSON/JSONC                 |
| Docker               | `Dockerfile`, `Containerfile`, `.dockerfile` | `docker-langserver`          | —                | —                                 | —                          |
| F#                   | `.fs`, `.fsi`, `.fsx`                        | `fsautocomplete`             | `fantomas`       | `.editorconfig`                   | EditorConfig               |
| Go                   | `.go`                                        | `gopls`                      | `goimports`      | —                                 | —                          |
| HTML                 | `.html`                                      | `html`                       | `deno`           | `deno.json`                       | JSON/JSONC                 |
| JavaScript / JSX     | `.js`, `.jsx`, `.mjs`, `.cjs`                | `typescript-language-server` | `deno`           | `tsconfig.json` / `deno.json`     | JSON/JSONC                 |
| JSON / JSONC         | `.json`, `.jsonc`                            | —                            | `deno`           | `deno.json`                       | JSON/JSONC                 |
| Jupyter              | `.ipynb`                                     | —                            | `deno`           | `deno.json`                       | JSON/JSONC                 |
| Just                 | `Justfile`, `justfile`                       | `just-lsp`                   | —                | —                                 | —                          |
| Lua                  | `.lua`                                       | `lua-language-server`        | `stylua`         | `.luarc.json` / `stylua.toml`     | JSON / TOML                |
| Markdown             | `.md`                                        | `rumdl`                      | `rumdl`          | `.rumdl.toml`                     | TOML                       |
| Pkl                  | `.pkl`, `.pcf`                               | `pkl-lsp`                    | `pkl`            | `PklProject`                      | Pkl                        |
| Python               | `.py`, `.pyi`                                | `pyright-langserver`         | `ruff`           | `pyproject.toml`                  | TOML                       |
| Rego                 | `.rego`                                      | `regal`                      | `regal`          | `.regal.yaml`                     | YAML                       |
| SQL                  | `.sql`                                       | —                            | `deno`           | `deno.json`                       | JSON/JSONC                 |
| TOML                 | `.toml`                                      | `taplo`                      | `taplo`          | `.taplo.toml`                     | TOML                       |
| Terraform / OpenTofu | `.tf`, `.tfvars`                             | `terraform-ls`               | `tofu`           | —                                 | —                          |
| TypeScript / TSX     | `.ts`, `.tsx`, `.mts`, `.cts`                | `typescript-language-server` | `deno`           | `tsconfig.json` / `deno.json`     | JSON/JSONC                 |
| XML / .NET project   | `.xml`, `.csproj`, `.slnx`                   | —                            | `xmllint`        | —                                 | —                          |
| YAML                 | `.yaml`, `.yml`                              | `yaml-language-server`       | `yamlfmt`        | `.yamlfmt.yaml`                   | YAML                       |

## Node tool assumptions

A Node or TypeScript project answers four independent questions at scaffold
time. They are deliberately separate: a project may install with one tool, test
with another, and never build at all.

| Question               | Choices                            | Governance                                                          |
| ---------------------- | ---------------------------------- | ------------------------------------------------------------------- |
| `node_package_manager` | `npm`, `pnpm`, `yarn`, `bun`       | Install commands, lockfile handling, `setup-node.jinja`             |
| `node_runtime`         | `node`, `bun`, `deno`              | Test runner in `package.json`; whether `package.json` exists at all |
| `node_purpose`         | `application`, `library`, `plugin` | `private`, `exports`, `files`, publish workflow presence            |
| `node_build`           | `none`, `tsc`, `tsup`              | `tsconfig.json` presence and emit settings                          |
| `node_lint`            | `deno`, `biome`                    | Formatter and linter: pre-commit hooks, CI lint step                |

`node_purpose` and `node_build` are unavailable when the runtime is `deno`: a
Deno project has no compiler config to choose, and cannot be an npm library or
an OpenCode plugin, whose manifest is a `package.json` entrypoint. Those choices
are refused with a validator message rather than hidden, so an answer that
cannot be honoured explains itself instead of vanishing from the list.

`node_lint: deno` is refused when the package manager is `bun` or `pnpm`: those
installers lay out `node_modules` differently from npm, so deno cannot resolve
the tree it is asked to lint.

Setting the runtime to `bun` and leaving the linter at `deno` would install both
tools and give the project a runner it cannot rely on, so the refused choice is
the one the default resolves to: a bun project must say `biome`.

Consequences worth knowing:

- `node_runtime: deno` emits no `package.json`. `deno.json` is the only Node-side
  config, and `deno test` is the runner.
- `deno.json` is emitted whenever the runtime **or** the linter is `deno`
  (`uses_deno`), so a Node-runtime project linted by deno still gets one.
- `node_build: none` emits no `tsconfig.json`, even for TypeScript. A project
  that merely happens to be written in TypeScript is not forced into a compiler
  config it never asked for.
- `tsc` owns emit and type-checking (`nodenext`, `declaration` only for a
  library). `tsup` owns emit and declarations, so `tsconfig.json` sets `noEmit`
  and only type-checks.
- When `node_lint` is not `deno`, deno is no longer the formatter of record for
  that repository, and the row above in the LSP matrix does not apply. `biome`
  is emitted as a `devDependency`.
- `publishConfig.provenance` is honoured by npm only, so `publish.yml` always
  runs `npm publish` regardless of `node_package_manager`.

## Publishable node packages

`node_purpose: library` adds the npm publishing surface: `private: false`, a
`files` allowlist, `exports` with `types` first, `engines`, `repository`,
`publishConfig.provenance`, and a tag-triggered `publish.yml`. Publishing uses
[npm trusted publishing](https://docs.npmjs.com/trusted-publishers) over OIDC —
there is no `NPM_TOKEN` to store, but the package must be registered as a
trusted publisher on npmjs.com before the first tag push.

`package.json` is not in `_skip_if_exists`: `copier update` regenerates it from
the answers like any other derived file, so the Node answers always describe the
manifest on disk. Anything the adopter added by hand — extra scripts, extra
dependencies — is lost on update and must be re-applied. The post-update message
says so. This is deliberate: a manifest that silently disagrees with
`node_runtime`, `node_purpose` and `node_build` is worse than one that has to be
merged.

`plugin` is the third purpose. It emits no `"."` export by default: OpenCode
resolves `<package>/server` and `<package>/tui` by entrypoint name, so a plugin
whose manifest exports only a root has no loadable entrypoint. With a build the
entrypoints are one-line root shims re-exporting `dist/`; without one they point
at the `.ts` sources directly, which is the shape OpenCode documents and its
loader resolves.

## Staying current with the template

`check-template-update.yml` runs weekly and on demand. It shells out to
`copier check-update --quiet`, which exits **2** when a newer template version
exists and **0** when the project is current — any other exit is treated as a
failure rather than as "up to date". On a stale result it opens one issue
labelled `template-update`, and skips if one is already open.

This only works when the template is tagged: `check-update` compares PEP 440
versions derived from git tags on both sides. `git describe --tags` reports the
highest-ranking tag at a commit, so two tags on the same commit are
indistinguishable — a new version requires a new commit *and* a new tag.

## Migrations

`copier update` overwrites the files the template renders and leaves everything
else alone. That is the right default and it covers most changes, but three
kinds of change it cannot make on its own:

- a file that stopped being rendered is **never deleted** — the old copy stays,
  now owned by nobody;
- an answer silently changed meaning, so the stored answers file says one thing
  while the new templates assume another;
- a hand-added key moved to a different place in a regenerated file.

A `_migrations` entry is the escape hatch, and it is worth being strict about
when to reach for one. A migration is warranted when an *existing project* is
wrong after `update` in a way no template change can fix — not when a file's
content changed (that is just a template edit), and not when a new question was
added (answering it is the adopter's job).

```yaml
_migrations:
  - version: 1.1.0
    command: "python3 scripts/migrations/v1_1_0_remove_static.py ."
    when: "{{ _copier_operation == 'update' }}"
```

`version` is the template version that introduces the change. Migrations at or
below the version the project recorded are skipped, so an entry is written once
and never edited; a mistake in one is fixed by the next version, not by rewriting
history. It is a plain version number, not a git ref: `v1.1.0` is not PEP 440
and Copier rejects it. The `when` clause is a template expression evaluated per
run — this example restricts the migration to `update`, because a fresh `copy`
has nothing to migrate.

The command is a script under the template repo's `scripts/migrations/`, never an
inline shell pipeline. Copier runs it from the destination project, so the path
addresses the installed template source, not the adopter's tree; the script
receives the project root as its argument and must resolve everything under that
and nothing else. A migration runs with the adopter's files, so it must be
reviewable in a diff, testable on its own, and refuse rather than guess when it
finds something it does not recognise. The shipped
`v1_1_0_remove_static.py` is the worked example of that discipline: it removes
`static/` only when the directory exists **and** is empty, and otherwise tells
the operator what to move and exits non-zero. No version of this template ever
rendered `static/`, so it finds nothing — which is the property that makes it
safe to ship as a reference before the first real migration needs it.
