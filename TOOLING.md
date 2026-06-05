# Tooling

Source of truth for LSP servers and formatters in use. Derive editor configs, CI checks, and pre-commit hooks from this document.

## LSP and Formatter Matrix

| Language | File extension | LSP binary | Formatter binary | Formatter config file |
|---|---|---|---|---|
| Bash / Shell | `.sh`, `.bash`, `.zsh`, `.ksh`, `PKGBUILD` | `bash-language-server` | `shfmt` | — |
| C# | `.cs`, `.csx` | `roslyn-language-server` | `csharpier` | — |
| C# (Razor) | `.razor` | `roslyn-language-server` | `csharpier` | — |
| CSS | `.css`, `.scss`, `.sass`, `.less` | — | `deno` | — |
| Docker | `Dockerfile`, `Containerfile`, `.dockerfile` | `docker-langserver` | — | — |
| F# | `.fs`, `.fsi`, `.fsx` | `fsautocomplete` | `fantomas` | — |
| Go | `.go` | `gopls` | `gofmt` | — |
| HTML | `.html` | `html` | `deno` | — |
| JavaScript / JSX | `.js`, `.jsx`, `.mjs`, `.cjs` | `typescript-language-server` | `deno` | — |
| JSON / JSONC | `.json`, `.jsonc` | — | `deno` | — |
| Jupyter | `.ipynb` | — | `deno` | — |
| Just | `Justfile`, `justfile` | `just-lsp` | — | — |
| Lua | `.lua` | `lua-language-server` | `stylua` | — |
| Markdown | `.md` | `rumdl` | `rumdl` | [`.rumdl.toml`](template/.rumdl.toml) |
| Pkl | `.pkl`, `.pcf` | `pkl-lsp` | `pkl` | — |
| Python | `.py`, `.pyi` | `pyright-langserver` | `ruff` | — |
| Rego | `.rego` | `regal` | `regal` | — |
| SQL | `.sql` | — | `deno` | — |
| TOML | `.toml` | `taplo` | `taplo` | — |
| Terraform / OpenTofu | `.tf`, `.tfvars` | `terraform-ls` | `tofu` | — |
| TypeScript / TSX | `.ts`, `.tsx`, `.mts`, `.cts` | `typescript-language-server` | `deno` | — |
| XML / .NET project | `.xml`, `.csproj`, `.slnx` | — | `xmllint` | — |
| YAML | `.yaml`, `.yml` | `yaml-language-server` | `yamlfmt` | [`.yamlfmt.yaml`](template/.yamlfmt.yaml) |
