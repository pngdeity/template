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

| Question               | Choices                      | Governance                                                          |
| ---------------------- | ---------------------------- | ------------------------------------------------------------------- |
| `node_package_manager` | `npm`, `pnpm`, `yarn`, `bun` | Install commands, lockfile handling, `setup-node.jinja`             |
| `node_runtime`         | `node`, `deno`               | Test runner in `package.json`; whether `package.json` exists at all |
| `node_build`           | `none`, `tsc`, `tsup`        | `tsconfig.json` presence and emit settings                          |
| `node_lint`            | `deno`, `biome`              | Pre-commit hooks, CI lint step                                      |

`node_purpose` and `node_build` are not asked when the runtime is `deno`: a Deno
project has no compiler config to choose and cannot be an npm library. That
constraint is what keeps the reachable matrix small enough to verify.

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

`package.json` is in `_skip_if_exists`, so `copier update` will not rewrite it in
an existing project. Merge new publish fields by hand.
