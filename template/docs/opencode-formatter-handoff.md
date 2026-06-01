# OpenCode Configuration Handoff

Handoff document mapping every formatter and LSP in `~/.config/opencode/opencode.jsonc`
to the Copier project template, identifying gaps and prescribing actions.

---

## 1. Formatters

### Complete mapping

| OpenCode formatter | Extensions | Command | Copier template | Action |
|---|---|---|---|---|
| `ruff` | `.py`, `.pyi` | `ruff` (default) | `pyproject.toml` — [tool.ruff] linter + formatter | Already present |
| `gofmt` | `.go` | `gofmt` (default) | `.golangci.yml` — gofmt + goimports linters enabled | Already present |
| `deno` | `.js`, `.jsx`, `.ts`, `.tsx`, `.json`, `.jsonc`, `.css`, `.scss`, `.sass`, `.less`, `.html`, `.sql` | `deno fmt --unstable-css --unstable-sql $FILE` | `.prettierrc` + `eslint.config.mjs` (Node projects only) | Intentional divergence — Copier chose Prettier+ESLint over Deno. Deno requires a Deno runtime; Prettier+ESLint is the wider ecosystem standard. |
| `shfmt` | `.sh`, `.bash`, `.zsh`, `.ksh`, `PKGBUILD`, `Makefile` | `shfmt` (default) | **MISSING** | **Add `.editorconfig` rule for shell** (already present). No separate shell formatter config needed — `shfmt` uses EditorConfig. |
| `yamlfmt` | `.yaml`, `.yml` | `yamlfmt $FILE` | `.editorconfig` (indentation) + `.prettierrc` (Node) | Partial — EditorConfig covers indentation; Prettier covers YAML for Node projects but is disabled in OpenCode. **Add `.yamlfmt.yaml`** if YAML formatting matters outside Node projects (CI configs, etc.). |
| `xmllint` | `.xml`, `.csproj`, `.slnx` | `xmllint --format --output $FILE $FILE` | `Directory.Build.props` — build-time code style analyzers | Low priority — .NET projects get build-time formatting. Only needed if non-.NET XML files exist. |
| `tofu` | `.tf`, `.tfvars` | `tofu fmt $FILE` | **MISSING** | No IaC ecosystem in template. Skip unless Terraform/OpenTofu support is added as a language option. |
| `regal` | `.rego` | `regal fix $FILE` | **MISSING** | No Rego/OPA ecosystem in template. Skip. |
| `pkl` | `.pkl` | `pkl format -w $FILE` | **MISSING** | No Pkl ecosystem in template. Skip. |
| **`rumdl`** | `.md` | `rumdl fmt --fixable "MD009,MD010,MD012,MD018,MD019,MD020,MD021,MD037,MD038,MD039,MD047,MD048,MD049,MD050,MD055,MD064" $FILE` | **MISSING** | **Add `.rumdl.toml`** (done — see section 1.1 below) |

### Disabled formatters in OpenCode

| Formatter | Why disabled |
|---|---|
| `prettier` | Conflicts with `deno`. Copier template includes `.prettierrc` for Node projects but OpenCode doesn't invoke it. |
| `rustfmt` | OpenCode default. Copier template has `rustfmt.toml` — re-enable in OpenCode if Rust becomes a primary language. |
| `air`, `biome`, `cargofmt`, `clang-format`, `cljfmt`, `dart`, `dfmt`, `gleam`, `htmlbeautifier`, `ktlint`, `mix`, `nixfmt`, `ocamlformat`, `ormolu`, `oxfmt`, `pint`, `rubocop`, `standardrb`, `terraform`, `uv`, `zig` | All intentionally disabled — not in active use. Copier template doesn't target these ecosystems. |

### 1.1 Action: `.rumdl.toml` (markdown) — COMPLETE

The template scaffolds 5 markdown files (README, CHANGELOG, CONTRIBUTING,
CODE\_OF\_CONDUCT, SECURITY) with no markdown formatting config. OpenCode has
`rumdl` as both formatter (conservative Tier 1 auto-fix) and LSP (diagnostics).

**File created**: `template/.rumdl.toml` — static, unconditional. Disables 17
structural rules (MD001, MD007, MD013, MD014, MD022, MD026, MD028, MD029,
MD031, MD032, MD034, MD036, MD040, MD041, MD056, MD058, MD060), sets
`flavor = "standard"`, configures MD024 `siblings-only=true`, and MD033
`allowed-elements` for common inline HTML tags.

**Why these 17 rules**: Each one enforces structural/document conventions
(heading hierarchy, code-fence language tags, inline HTML stripping) that vary
between projects. Auto-fixing them would restructure documents. They mirror
the existing `skills/.markdownlint-cli2.jsonc` config.

**OpenCode formatter behavior**: Auto-fixes only 16 cosmetic rules (MD009
trailing spaces, MD010 tabs, MD012 blank lines, MD018-021 hash spacing,
MD037-039 emphasis/code/link spacing, MD047 trailing newline, MD048 code fence
style, MD049-050 emphasis style, MD055 table pipes, MD064 double spaces). All
other rules are diagnostics-only. Structural rules are completely suppressed.

**Verification after adding**:
```bash
copier copy ~/repos/pngdeity/template /tmp/test-rumdl
cd /tmp/test-rumdl
rumdl config file          # → /tmp/test-rumdl/.rumdl.toml
rumdl fmt --check README.md  # issues reported, no structural rewrites
```

### 1.2 Action: `.yamlfmt.yaml` (YAML) — OPTIONAL

`yamlfmt` has no corresponding config in the template. The `.editorconfig` sets
indentation, and Prettier handles YAML for Node projects. For non-Node projects,
`yamlfmt` uses its own defaults (2-space indent, retain line breaks, no formatter
extensions).

**No config file needed by default** — `yamlfmt` with zero config is reasonable.
If custom YAML formatting is desired, add `.yamlfmt.yaml`:

```yaml
# template/.yamlfmt.yaml (static, unconditional)
formatter:
  type: basic
  indent: 2
  include_document_start: false
  retain_line_breaks: true
  max_line_length: 0
  scan_folded_as_literal: false
```

`_exclude` in `copier.yml` does not block `.yamlfmt.yaml`, so it would be
included automatically.

### 1.3 Action: shell formatting — NO CHANGE

`shfmt` uses EditorConfig for indentation settings. The template already includes
`.editorconfig` with shell rules. No separate config needed — `shfmt` reads
EditorConfig directly.

Current `.editorconfig` shell section (already present, no changes needed):
```ini
[*.sh]
indent_style = tab
indent_size = 4
```

---

## 2. LSP Servers

### Complete mapping

| OpenCode LSP | Command | Extensions | Copier template | Notes |
|---|---|---|---|---|
| `bash` | `bash-language-server start` | `.sh`, `.bash`, `.zsh`, `.ksh`, `PKGBUILD`, `Makefile` | EditorConfig | No bash-language-server config needed — uses `shfmt` integration for formatting |
| `docker` | `docker-langserver --stdio` | `.dockerfile`, `Dockerfile`, `Containerfile` | **MISSING** | No Docker ecosystem in template. System-level tool only. |
| `just` | `just-lsp` | `Justfile`, `justfile` | **MISSING** | No justfile ecosystem in template. System-level tool only. |
| `csharp` | `roslyn-language-server --stdio --autoLoadProjects` | `.cs` | `Directory.Build.props` | Build-time analyzers complement LSP |
| `razor` | `roslyn-language-server --stdio --autoLoadProjects` | `.razor` | `Directory.Build.props` | Same roslyn server, different file type |
| `gopls` | `gopls` | `.go` | `.golangci.yml` | golangci-lint runs gofmt/goimports; gopls provides IDE diagnostics |
| `lua-ls` | `lua-language-server` | `.lua` | **MISSING** | No Lua ecosystem in template |
| `pkl` | `pkl-lsp` | `.pkl`, `.pcf` | **MISSING** | No Pkl ecosystem in template |
| `pyright` | `pyright-langserver --stdio` | `.py`, `.pyi` | `pyproject.toml` | Ruff covers linting+formatting; pyright covers type checking |
| `regal` | `regal language-server` | `.rego` | **MISSING** | No Rego ecosystem in template |
| **`rumdl`** | `rumdl server` | `.md` | `.rumdl.toml` (added) | Diagnostics only — never modifies files |
| `terraform` | `terraform-ls serve` | `.tf` | **MISSING** | Uses `tofu` binary instead of terraform via `initialization.terraform.path` |
| `typescript` | `typescript-language-server --stdio` | `.ts`, `.tsx` | `eslint.config.mjs` | ESLint for linting; TS server for IDE features |
| `yaml-ls` | `yaml-language-server --stdio` | `.yaml`, `.yml` | `.editorconfig` | Schema store enabled, APM schema registered |

### Disabled LSP servers in OpenCode

| Server | Why disabled |
|---|---|
| `clangd` | No C/C++ ecosystem in template |
| `dart` | No Dart ecosystem |
| `deno` | Prettier+ESLint preferred |
| `eslint` | ESLint requires project-level npm dep — Copier includes it but OpenCode defaults to off |
| `nixd` | No Nix ecosystem |
| `rust` | Enabled in Copier (rustfmt.toml) but disabled in OpenCode — re-enable for Rust projects |

---

## 3. Summary of Actions

| Priority | Action | Status |
|---|---|---|
| **P0** | Add `.rumdl.toml` to template | **DONE** |
| P1 | Add `.yamlfmt.yaml` (optional — only if YAML formatting matters for non-Node projects) | Unconfirmed |
| P2 | Re-enable `rustfmt` formatter + `rust-analyzer` LSP in OpenCode if Rust becomes primary | Monitor |
| P3 | Add Terraform/OpenTofu to Copier template as language option (+ `.tofu.toml` or `.terraform.hcl`) | Monitor |
| N/A | `shfmt` — already covered by EditorConfig | No action |
| N/A | `xmllint`, `tofu`, `regal`, `pkl`, `docker`, `just`, `lua-ls` — ecosystems not in template | Skip |

## 4. Reference

- OpenCode config: `~/.config/opencode/opencode.jsonc`
  - Formatters: lines 48-123
  - LSP servers: lines 125-231
- Copier template: `~/repos/pngdeity/template/copier.yml`
  - Language flags: `languages` (multiselect), `has_node`, `has_typescript`, `has_python`, `has_dotnet`
  - Conditional files: `{% if 'python' in languages %}...{% endif %}`
  - Excluded from copy: `copier.yml`, `**/__pycache__`, `.git`
- rumdl rule docs: <https://rumdl.dev>
- Existing rumdl config: `~/repos/pngdeity/skills/.rumdl.toml` (generated from `.markdownlint-cli2.jsonc` via `rumdl import`)
