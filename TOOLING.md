# Tooling

Source of truth for LSP servers and formatters in use. Derive editor configs, CI checks, and pre-commit hooks from this document.

## LSP and Formatter Matrix

| Language | File extension | LSP binary | Formatter binary | Config File(s) | Format |
|---|---|---|---|---|---|---|
| Bash / Shell | `.sh`, `.bash`, `.zsh`, `.ksh`, `PKGBUILD` | `bash-language-server` | `shfmt` | `.editorconfig` | EditorConfig |
| C# | `.cs`, `.csx` | `roslyn-language-server` | `csharpier` | `.csharpierrc`* / `.editorconfig` | JSON / YAML / EditorConfig |
| C# (Razor) | `.razor` | `roslyn-language-server` | `csharpier` | `.csharpierrc`* / `.editorconfig` | JSON / YAML / EditorConfig |
| CSS | `.css`, `.scss`, `.sass`, `.less` | — | `deno` | `deno.json` | JSON/JSONC |
| Docker | `Dockerfile`, `Containerfile`, `.dockerfile` | `docker-langserver` | — | — | — |
| F# | `.fs`, `.fsi`, `.fsx` | `fsautocomplete` | `fantomas` | `.editorconfig` | EditorConfig |
| Go | `.go` | `gopls` | `goimports` | — | — |
| HTML | `.html` | `html` | `deno` | `deno.json` | JSON/JSONC |
| JavaScript / JSX | `.js`, `.jsx`, `.mjs`, `.cjs` | `typescript-language-server` | `deno` | `tsconfig.json` / `deno.json` | JSON/JSONC |
| JSON / JSONC | `.json`, `.jsonc` | — | `deno` | `deno.json` | JSON/JSONC |
| Jupyter | `.ipynb` | — | `deno` | `deno.json` | JSON/JSONC |
| Just | `Justfile`, `justfile` | `just-lsp` | — | — | — |
| Lua | `.lua` | `lua-language-server` | `stylua` | `.luarc.json` / `stylua.toml` | JSON / TOML |
| Markdown | `.md` | `rumdl` | `rumdl` | `.rumdl.toml` | TOML |
| Pkl | `.pkl`, `.pcf` | `pkl-lsp` | `pkl` | `PklProject` | Pkl |
| Python | `.py`, `.pyi` | `pyright-langserver` | `ruff` | `pyproject.toml` | TOML |
| Rego | `.rego` | `regal` | `regal` | `.regal.yaml` | YAML |
| SQL | `.sql` | — | `deno` | `deno.json` | JSON/JSONC |
| TOML | `.toml` | `taplo` | `taplo` | `.taplo.toml` | TOML |
| Terraform / OpenTofu | `.tf`, `.tfvars` | `terraform-ls` | `tofu` | — | — |
| TypeScript / TSX | `.ts`, `.tsx`, `.mts`, `.cts` | `typescript-language-server` | `deno` | `tsconfig.json` / `deno.json` | JSON/JSONC |
| XML / .NET project | `.xml`, `.csproj`, `.slnx` | — | `xmllint` | — | — |
| YAML | `.yaml`, `.yml` | `yaml-language-server` | `yamlfmt` | `.yamlfmt.yaml` | YAML |
