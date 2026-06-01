# pngdeity/template

Standardized Git repository template for pngdeity projects. Scaffolds consistent
governance files, language tooling configs, CI/CD pipelines, and agent scaffolding
across new and existing repositories.

## Usage

```bash
# Install
pip install copier

# Scaffold a new project
copier copy gh:pngdeity/template /path/to/new-project

# Adopt into an existing project
copier adopt gh:pngdeity/template /path/to/existing-project
```

## Languages Supported

| Language | Configs Generated |
|----------|-------------------|
| Python | pyproject.toml (ruff, mypy, pytest) |
| JavaScript/TypeScript | deno.json, package.json |
| Go | go.mod, .golangci.yml, .go-version |
| Rust | Cargo.toml, rustfmt.toml, rust-toolchain.toml |
| .NET / C# | .csproj, Directory.Build.props, Directory.Packages.props, global.json, NuGet.config |
| OpenTofu | versions.tf, main.tf, variables.tf, outputs.tf, backend.tf, .tflint.hcl, .env.example |

## Features

- Root governance files (README, LICENSE, CONTRIBUTING, SECURITY, CHANGELOG, CODEOWNERS)
- Language-specific linter and formatter configurations
- GitHub Actions CI workflows (Go, signed commit verification, APM audit)
- Pre-commit hooks (formatters, linters, commitlint)
- APM agent scaffolding (apm.yml, .apm/ directory)
- Task tracking (TASKS.md, inline TODO conventions)
- Compliance audit script (A–D grade scoring)

## License

MIT
