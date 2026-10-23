#!/usr/bin/env python3
"""Render this template under every supported answer combination and verify the output.

Every template change is verified by a render, not by reading. This script is that
render: it copies the template into a scratch directory once per config, then
asserts on the result.

Checks applied to every render:
  * the render succeeded
  * every JSON file parses
  * every workflow parses as YAML
  * no unevaluated Jinja markers survive into output
  * `npx @tasks-md/lint TASKS.md` reports zero errors
  * `python3 scripts/audit.py` reports Grade A
  * no document contains a double blank line

Usage:
    python3 scripts/test_template.py            # full matrix
    python3 scripts/test_template.py --list     # list config names
    python3 scripts/test_template.py bun py-app # only these configs
    python3 scripts/test_template.py --keep     # leave renders in the work dir

Exit status is non-zero if any check fails.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = REPO_ROOT

JSON_FILES = (
    "package.json",
    "tsconfig.json",
    "deno.json",
    ".devcontainer/devcontainer.json",
)

DOC_FILES = (
    "README.md",
    "AGENTS.md",
    "TASKS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
)

# Jinja allowlist: this file is a Go template for terraform-docs, so its
# `{{ .Header }}` and friends are output, not unevaluated Jinja.
JINJA_ALLOWED = (".github/workflows", ".terraform-docs.yml")


@dataclass
class Config:
    name: str
    data: dict[str, str] = field(default_factory=dict)
    # Adopt an existing project and update it, instead of a fresh copy.
    adopt: bool = False


LANGUAGES = "languages"


def configs() -> list[Config]:
    ts = {LANGUAGES: "[typescript]"}
    js = {LANGUAGES: "[javascript]"}
    py = {LANGUAGES: "[python]"}
    return [
        # --- Node / TypeScript ------------------------------------------------
        Config("ts-def", ts),
        Config("ts-tsc-lib", {**ts, "node_purpose": "library", "node_build": "tsc"}),
        Config("ts-tsup-lib", {**ts, "node_purpose": "library", "node_build": "tsup"}),
        Config(
            "ts-subpaths",
            {
                **ts,
                "node_purpose": "library",
                "node_subpath_exports": "[core, descriptors]",
            },
        ),
        Config("ts-tsc-app", {**ts, "node_build": "tsc"}),
        Config("ts-deno", {**ts, "node_runtime": "deno"}),
        Config("js-def", js),
        Config("ts-biome", {**ts, "node_lint": "biome", "node_build": "tsc"}),
        Config(
            "ts-pnpm",
            {
                **ts,
                "node_package_manager": "pnpm",
                "node_purpose": "library",
                "node_lint": "biome",
            },
        ),
        Config("ts-yarn", {**ts, "node_package_manager": "yarn", "node_build": "tsup"}),
        Config("ts-bun", {**ts, "node_package_manager": "bun", "node_lint": "biome"}),
        Config(
            "ts-bun-runtime",
            {
                **ts,
                "node_runtime": "bun",
                "node_package_manager": "bun",
                "node_lint": "biome",
            },
        ),
        Config(
            "ts-plugin-src",
            {
                **ts,
                "node_purpose": "plugin",
                "node_runtime": "bun",
                "node_package_manager": "bun",
                "node_lint": "biome",
            },
        ),
        Config(
            "ts-plugin-tsc",
            {
                **ts,
                "node_purpose": "plugin",
                "node_build": "tsc",
                "node_package_manager": "pnpm",
                "node_lint": "biome",
            },
        ),
        Config(
            "ts-plugin-tsup",
            {
                **ts,
                "node_purpose": "plugin",
                "node_build": "tsup",
                "node_package_manager": "yarn",
            },
        ),
        Config(
            "ts-plugin-peer",
            {
                **ts,
                "node_purpose": "plugin",
                "node_package_manager": "bun",
                "node_runtime": "bun",
                "node_lint": "biome",
                "author_email": "dev@example.com",
                "node_keywords": "[opencode, plugin]",
                "node_peer_dependencies": '{"@opencode/plugin": ">=2.0.0", "solid-js": "^1.9.0"}',
            },
        ),
        # --- Other languages --------------------------------------------------
        Config("py-app", py),
        Config("py-tool", {**py, "python_scaffolding": "tooling"}),
        Config("go-app", {LANGUAGES: "[go]"}),
        Config("rust", {LANGUAGES: "[rust]"}),
        Config("dotnet", {LANGUAGES: "[dotnet]"}),
        Config("tofu-app", {LANGUAGES: "[tofu]", "tofu_context": "app"}),
        Config("mixed", {LANGUAGES: "[python, go]"}),
        Config("empty", {LANGUAGES: "[]", "ci_provider": "none"}),
        # --- Documentation toggles -------------------------------------------
        # These exist because a deleted partial's TemplateNotFound survived a
        # full matrix that never set include_contributing.
        Config(
            "docs-all",
            {
                **py,
                "include_contributing": "true",
                "include_security": "true",
                "use_codeowners": "true",
                "use_commitizen": "true",
                "include_tasks_lint": "true",
                "include_annotation_gate": "true",
            },
        ),
        Config(
            "docs-compiled",
            {
                LANGUAGES: "[go, rust]",
                "include_contributing": "true",
                "include_security": "true",
            },
        ),
        Config(
            "docs-shell",
            {
                **js,
                "include_shell_tooling": "true",
                "include_contributing": "true",
            },
        ),
        Config(
            "docs-tofu",
            {
                LANGUAGES: "[tofu]",
                "include_contributing": "true",
                "include_security": "true",
            },
        ),
        # --- Adoption ---------------------------------------------------------
        # `package.json` used to be in `_skip_if_exists`, so an adopted project
        # kept its own manifest while every other file followed the template's
        # Node answers. This config proves the manifest is regenerated.
        Config(
            "adopt-node",
            {LANGUAGES: "[typescript]", "node_purpose": "library"},
            adopt=True,
        ),
    ]


def copier_binary() -> str:
    # The system copier cannot load this template's jinja2_time extension, so
    # probe each candidate before trusting it.
    candidates = [shutil.which("copier"), "/tmp/opencode/.venv/bin/copier"]
    for candidate in candidates:
        if not candidate or not Path(candidate).exists():
            continue
        probe = subprocess.run([candidate, "--version"], capture_output=True, text=True)
        if probe.returncode != 0:
            continue
        check = subprocess.run(
            [
                candidate,
                "copy",
                "--trust",
                "--defaults",
                "--quiet",
                "--vcs-ref",
                "HEAD",
                "--pretend",
                str(TEMPLATE),
                str(Path(tempfile.gettempdir()) / "copier-probe"),
                "--data",
                "repo_name=probe",
                "--data",
                "languages=[]",
                "--data",
                "ci_provider=none",
                "--data",
                "use_precommit=false",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if "jinja2_time" not in check.stderr:
            return candidate
    raise SystemExit(
        "no copier with the jinja2_time extension found; install it with "
        "`uv pip install jinja2-time` into the copier environment"
    )


def render(copier: str, cfg: Config, dest: Path) -> tuple[bool, str]:
    cmd = [
        copier,
        "copy",
        "--trust",
        "--defaults",
        "--force",
        "--overwrite",
        "--quiet",
        # Without this Copier renders the last git tag, not the working tree.
        "--vcs-ref",
        "HEAD",
        str(TEMPLATE),
        str(dest),
        "--data",
        f"repo_name=m-{cfg.name}",
        "--data",
        "use_precommit=false",
    ]
    for key, value in cfg.data.items():
        cmd += ["--data", f"{key}={value}"]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def check_json(dest: Path, problems: list[str]) -> None:
    for rel in JSON_FILES:
        path = dest / rel
        if not path.exists():
            continue
        try:
            json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            problems.append(f"{rel} is not valid JSON: {exc}")


def check_yaml(dest: Path, problems: list[str]) -> None:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        problems.append("PyYAML missing; workflow validation skipped")
        return
    for path in sorted((dest / ".github" / "workflows").glob("*.yml")):
        try:
            yaml.safe_load(path.read_text())
        except yaml.YAMLError as exc:
            problems.append(f"{path.name} is not valid YAML: {exc}")


def check_jinja(dest: Path, problems: list[str]) -> None:
    for path in dest.rglob("*"):
        if not path.is_file() or path.suffix not in (".md", ".yml", ".yaml", ".json"):
            continue
        rel = path.relative_to(dest).as_posix()
        if any(rel.startswith(allowed) for allowed in JINJA_ALLOWED):
            continue
        text = path.read_text(errors="replace")
        if "{% " in text or "{{ " in text:
            problems.append(f"unevaluated Jinja in {rel}")


def check_blank_lines(dest: Path, problems: list[str]) -> None:
    for name in DOC_FILES:
        path = dest / name
        if not path.exists():
            continue
        lines = path.read_text().splitlines()
        for index, line in enumerate(lines):
            if line or index == 0:
                continue
            if not lines[index - 1]:
                problems.append(f"{name}:{index + 1} has a double blank line")


def check_lint(dest: Path, problems: list[str]) -> str:
    proc = subprocess.run(
        ["npx", "--yes", "@tasks-md/lint", "TASKS.md"],
        cwd=dest,
        capture_output=True,
        text=True,
    )
    out = proc.stdout + proc.stderr
    if proc.returncode != 0 or "found 0 error" not in out:
        problems.append("TASKS.md failed @tasks-md/lint")
    return out


def check_audit(dest: Path, problems: list[str]) -> str:
    proc = subprocess.run(
        [sys.executable, "scripts/audit.py"],
        cwd=dest,
        capture_output=True,
        text=True,
    )
    out = (proc.stdout + proc.stderr).strip()
    missing = [line.strip() for line in out.splitlines() if "Missing CI config" in line]
    if missing:
        # A repository cannot be told it owns files the template deleted.
        problems.append(f"audit expects unrendered files: {missing[0]}")
    last = out.splitlines()[-1] if out else ""
    if "Grade: A" not in last:
        problems.append(f"audit did not report Grade A: {last or 'no output'}")
    return last


def check_manifest_overwritten(dest: Path, problems: list[str]) -> None:
    # `copier update` must regenerate package.json: a manifest that keeps the
    # adopter's values while the rest of the tree follows the template's Node
    # answers disagrees with itself, silently.
    manifest = dest / "package.json"
    if not manifest.exists():
        return
    data = json.loads(manifest.read_text())
    if "leftover-key" in data:
        problems.append("package.json kept the adopter's hand-written keys")
    if not data.get("exports"):
        problems.append("package.json is missing the template's exports block")


def git(dest: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "git",
            "-c",
            "user.name=matrix",
            "-c",
            "user.email=matrix@example.com",
            *args,
        ],
        cwd=dest,
        capture_output=True,
        text=True,
    )


def adopt(copier: str, cfg: Config, dest: Path) -> tuple[bool, str]:
    # Prove the update path, not just the copy path: adopt a project that
    # already has its own package.json, then update it from the template.
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "package.json").write_text(
        json.dumps({"name": "hand-written", "leftover-key": True}, indent=2) + "\n"
    )
    (dest / "README.md").write_text("# Hand written\n")
    data_args: list[str] = []
    for key, value in cfg.data.items():
        data_args += ["--data", f"{key}={value}"]
    proc = subprocess.run(
        [
            copier,
            "copy",
            "--trust",
            "--defaults",
            "--force",
            "--overwrite",
            "--quiet",
            # Without this Copier renders the last git tag, not the working tree.
            "--vcs-ref",
            "HEAD",
            str(TEMPLATE),
            str(dest),
            *data_args,
            "--data",
            "use_precommit=false",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return False, (proc.stdout + proc.stderr).strip()
    # `update` refuses a dirty destination, and it replays the recorded
    # `_commit` — a revision no clone can resolve after a copy from a dirty
    # working tree. Rewrite it to the tag both sides agree on, and commit that
    # before updating so the tree is clean.
    answers = dest / ".copier-answers.yml"
    answers.write_text(
        "\n".join(
            "_commit: v1.0.0" if line.startswith("_commit:") else line
            for line in answers.read_text().splitlines()
        )
        + "\n"
    )
    for args in (("add", "-A"), ("commit", "-q", "-m", "adopted")):
        result = git(dest, *args)
        if result.returncode != 0:
            return False, (result.stdout + result.stderr).strip()
    proc = subprocess.run(
        [copier, "update", "--trust", "--defaults", "--quiet"],
        cwd=dest,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return False, (proc.stdout + proc.stderr).strip()
    return True, ""


def run_config(copier: str, cfg: Config, out_dir: Path) -> list[str]:
    dest = out_dir / cfg.name
    if cfg.adopt:
        ok, log = adopt(copier, cfg, dest)
    else:
        ok, log = render(copier, cfg, dest)
    if not ok:
        tail = "\n".join(log.splitlines()[-6:])
        return [f"render failed:\n{tail}"]

    problems: list[str] = []
    check_json(dest, problems)
    check_yaml(dest, problems)
    check_jinja(dest, problems)
    check_blank_lines(dest, problems)
    if cfg.adopt:
        check_manifest_overwritten(dest, problems)
    check_lint(dest, problems)
    check_audit(dest, problems)
    return problems


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("names", nargs="*", help="config names to run (default: all)")
    parser.add_argument(
        "--list", action="store_true", help="list config names and exit"
    )
    parser.add_argument("--keep", action="store_true", help="keep the render directory")
    parser.add_argument("--out", help="render directory (implies --keep)")
    args = parser.parse_args(argv)

    all_configs = configs()
    if args.list:
        for cfg in all_configs:
            print(cfg.name)
        return 0

    selected = all_configs
    if args.names:
        known = {cfg.name for cfg in all_configs}
        unknown = [name for name in args.names if name not in known]
        if unknown:
            raise SystemExit(f"unknown config(s): {', '.join(unknown)}")
        selected = [cfg for cfg in all_configs if cfg.name in args.names]

    copier = copier_binary()
    keep = args.keep or bool(args.out)
    out_dir = (
        Path(args.out)
        if args.out
        else Path(tempfile.mkdtemp(prefix="template-matrix-"))
    )

    failures = 0
    try:
        for cfg in selected:
            problems = run_config(copier, cfg, out_dir)
            if problems:
                failures += 1
                print(f"FAIL {cfg.name}")
                for problem in problems:
                    print(f"     {problem}")
            else:
                print(f"ok   {cfg.name}")
    finally:
        if not keep:
            shutil.rmtree(out_dir, ignore_errors=True)

    print()
    if failures:
        print(f"=== {failures} of {len(selected)} configs failed ===")
        return 1
    print(f"=== all {len(selected)} configs passed ===")
    if keep:
        print(f"renders: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
