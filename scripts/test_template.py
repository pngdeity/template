#!/usr/bin/env python3
"""Render this template under every supported answer combination and verify the output.

Every template change is verified by a render, not by reading. This script is that
render: it copies the template into a scratch directory once per config, then
asserts on the result.

Checks applied to every render:
  * the render succeeded
  * every JSON file parses
  * every workflow parses as YAML
  * no unevaluated Jinja markers survive into output (GitHub's `${{ }}` aside)
  * `@tasks-md/lint TASKS.md` reports zero errors
  * `python3 scripts/audit.py` reports Grade A
  * no document contains a double blank line
  * README `## Usage` is not a fence of comments only

One config (`adopt-node`) exercises the update path instead of a fresh copy: it
copies the template onto a project that already has a `package.json`, then runs
`copier update` from a commit containing the working tree.

Usage:
    python3 scripts/test_template.py            # full matrix
    python3 scripts/test_template.py --changed  # only what the working tree touches
    python3 scripts/test_template.py --full     # ignore the pass cache
    python3 scripts/test_template.py --list     # list config names
    python3 scripts/test_template.py bun py-app # only these configs
    python3 scripts/test_template.py --keep     # leave renders in the work dir

A config that already passed against this exact template tree is reported as
cached instead of rendered again; any edit anywhere invalidates the cache, so
it never stands in for a render of the change under test. The cache is
per-machine and opt-in: CI renders everything, because a job cannot inherit the
tree hash a previous run verified.

`--shard N/M` splits the selected configs into M contiguous slices and runs
slice N, which is how CI spreads the matrix across jobs. A shard reports its
holdings on the first line so a fan-out that silently drops a config is
visible in the log.

Exit status is non-zero if any check fails.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = REPO_ROOT

JSON_FILES = (
    "package.json",
    "biome.json",
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

# Must match the last line of template/.gitignore.jinja. Copier rewrites the
# whole file, so this marker is what tells an adopter where their own rules
# begin; a render that stops before it, or continues past it, means the
# generated half would clobber them on update.
GITIGNORE_ADOPTER_MARKER = (
    "# --- Everything below this line is yours; template updates never touch it. ---"
)

# Jinja allowlist: this file is a Go template for terraform-docs, so its
# `{{ .Header }}` and friends are output, not unevaluated Jinja. GitHub
# expressions (`${{ ... }}`) are handled separately in check_jinja, because
# they appear in workflows that must still be scanned for real Jinja.
JINJA_ALLOWED = (".terraform-docs.yml",)
GITHUB_EXPRESSION = re.compile(r"\$\{\{.*?\}\}", re.DOTALL)


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
            "ts-plugin-scoped",
            {
                **ts,
                "node_purpose": "plugin",
                "node_package_manager": "bun",
                "node_runtime": "bun",
                "node_lint": "biome",
                "node_package_scope": "pngdeity",
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
        Config("go-toolchain", {LANGUAGES: "[go]", "go_toolchain": "go1.26.0"}),
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


def lint_command() -> list[str]:
    # npx re-resolves the package for every render's directory, which is the
    # slowest part of a render that is otherwise clean. Prefer a binary npx
    # has already unpacked.
    found = shutil.which("tasks-lint")
    if found:
        return [found]
    # npm follows the XDG base directory spec and names the directory itself,
    # so ask it: hardcoding ~/.npm finds nothing on a machine with
    # XDG_CACHE_HOME set, and hardcoding ~/.cache/npm finds nothing on a
    # machine without it.
    roots = []
    probe = subprocess.run(
        ["npm", "config", "get", "cache"], capture_output=True, text=True
    )
    if probe.returncode == 0 and probe.stdout.strip():
        roots.append(Path(probe.stdout.strip()))
    roots.append(Path.home() / ".cache/npm")
    roots.append(Path.home() / ".npm")
    for root in roots:
        for candidate in (root / "_npx").glob("*/node_modules/.bin/tasks-lint"):
            return [str(candidate)]
    return ["npx", "--yes", "@tasks-md/lint"]


def copier_binary() -> str:
    # The system copier cannot load this template's jinja2_time extension, so
    # probe each candidate before trusting it.
    candidates = [shutil.which("copier"), "/tmp/opencode/.venv/bin/copier"]
    for candidate in candidates:
        if not candidate or not Path(candidate).exists():
            continue
        # The extension is imported from the copier script's own interpreter,
        # so asking that interpreter costs one process instead of two.
        interpreter = Path(candidate).with_name("python")
        if not interpreter.exists():
            continue
        check = subprocess.run(
            [str(interpreter), "-c", "import jinja2_time"],
            capture_output=True,
            text=True,
        )
        if check.returncode == 0:
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
        text = path.read_text()
        if text != text.rstrip() + "\n":
            problems.append(f"{rel} does not end with exactly one newline")
        try:
            json.loads(text)
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
        if rel in JINJA_ALLOWED:
            continue
        text = path.read_text(errors="replace")
        # GitHub expressions are `${{ ... }}`, so they are output rather than
        # unevaluated Jinja. Exempting the whole `.github/workflows` directory
        # instead would let a real `{{ repo_name }}` pasted into a workflow
        # through unnoticed, which is what this check exists to catch.
        stripped = GITHUB_EXPRESSION.sub("", text)
        if "{% " in stripped or "{{ " in stripped:
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


def check_usage_placeholder(dest: Path, problems: list[str]) -> None:
    # A fence whose only content is a comment reads as a runnable command and
    # is not one: the reader cannot tell it apart from a finished example.
    readme = dest / "README.md"
    if not readme.exists():
        return
    text = readme.read_text()
    if "## Usage" not in text:
        return
    usage = text.split("## Usage", 1)[1].split("\n## ", 1)[0]
    for block in usage.split("```")[1::2]:
        body = [line.strip() for line in block.splitlines() if line.strip()]
        if body and all(line.startswith("#") for line in body):
            problems.append("README.md ## Usage is a fence of comments only")


def check_gitignore(dest: Path, problems: list[str]) -> None:
    # The generated half must end at the adopter marker, or an `update` would
    # overwrite whatever the adopter put below it.
    path = dest / ".gitignore"
    if not path.exists():
        problems.append(".gitignore was not rendered")
        return
    lines = path.read_text().splitlines()
    marker = GITIGNORE_ADOPTER_MARKER
    if marker not in lines:
        problems.append(".gitignore has no adopter-rules marker")
    elif lines[-1] != marker:
        problems.append(".gitignore continues past the adopter-rules marker")
    if lines.count(marker) > 1:
        problems.append(".gitignore repeats the adopter-rules marker")


def check_lint(dest: Path, problems: list[str]) -> str:
    proc = subprocess.run(
        [*lint_command(), "TASKS.md"],
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
    try:
        data = json.loads(manifest.read_text())
    except json.JSONDecodeError:
        # check_json already reports the parse failure for this file; raising
        # here would abort the whole matrix instead of one config.
        return
    if "leftover-key" in data:
        problems.append("package.json kept the adopter's hand-written keys")
    if not data.get("exports"):
        problems.append("package.json is missing the template's exports block")


def template_fingerprint() -> str:
    """Hash every input a render depends on: the whole tree, minus git.

    Paths as well as contents are hashed, because a rename changes the output.
    """
    digest = hashlib.sha256()
    for path in sorted(REPO_ROOT.glob("**/*")):
        if not path.is_file():
            continue
        parts = path.relative_to(REPO_ROOT).parts
        if any(p in (".git", "__pycache__", ".ruff_cache", ".serena") for p in parts):
            continue
        digest.update(path.relative_to(REPO_ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def cache_path() -> Path:
    key = hashlib.sha256(str(REPO_ROOT).encode()).hexdigest()[:12]
    return Path(tempfile.gettempdir()) / f"template-matrix-{key}.json"


def cached_configs(fingerprint: str) -> dict[str, list[str]]:
    """Configs already passed against this exact template fingerprint.

    Keyed by a hash of the whole tree, so any edit anywhere invalidates all of
    them: the cache answers "is this file still verified", never "is it probably
    still fine". That is why it is advisory and `--full` ignores it.
    """
    try:
        data = json.loads(cache_path().read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if data.get("fingerprint") != fingerprint:
        return {}
    return data.get("passed", {})


def remember(fingerprint: str, results: dict[str, list[str]]) -> None:
    passed = {name: problems for name, problems in results.items() if not problems}
    try:
        cache_path().write_text(
            json.dumps({"fingerprint": fingerprint, "passed": passed})
        )
    except OSError:
        pass


def changed_configs(all_configs: list[Config]) -> list[Config]:
    """Configs a change could plausibly affect, from the working tree.

    Coarse on purpose: over-selecting costs a render, under-selecting costs a
    false pass. A change to `copier.yml`, a partial, or a file rendered into
    every config reaches everything; a change confined to one conditional file
    narrows to configs whose answers select that file.
    """
    proc = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    paths = [line[3:].strip() for line in proc.stdout.splitlines() if line.strip()]
    if not paths:
        return []
    for path in paths:
        name = Path(path).name
        if (
            path == "copier.yml"
            or "/_partials/" in path
            or path.startswith("_partials/")
            # A filename with no condition is rendered into every config, but
            # only files under `template/` are rendered at all.
            or ("{%" not in name and path.startswith("template/"))
        ):
            return all_configs
    selected = []
    for cfg in all_configs:
        for path in paths:
            conditions = re.findall(r"\{%\s*if\s+([^%]+?)\s*%\}", Path(path).name)
            if any(condition_gate(cfg, condition) for condition in conditions):
                selected.append(cfg)
                break
    return selected


def condition_gate(cfg: Config, condition: str) -> bool:
    """Whether this config could take the branch guarded by `condition`.

    Answers never pass through Copier here, so the condition is matched against
    the config's data. Terms are `and`-joined `has_<lang>` tests or
    `<answer> <op> '<value>'` comparisons; anything else is assumed to apply,
    because a wrong "no" silently drops a config from the run.
    """
    return all(gate_term(cfg, term) for term in condition.split(" and "))


def gate_term(cfg: Config, term: str) -> bool:
    term = term.strip()
    match = re.fullmatch(r"has_(\w+)", term)
    if match:
        languages = cfg.data.get(LANGUAGES, "")
        if match.group(1) == "node":
            return "typescript" in languages or "javascript" in languages
        return match.group(1) in languages
    match = re.fullmatch(r"(\w+)\s*(==|!=)\s*'([^']*)'", term)
    if match:
        key, operator, value = match.groups()
        if key not in cfg.data:
            return True
        equal = cfg.data[key] == value
        return equal if operator == "==" else not equal
    return True


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


_SNAPSHOT: tuple[str, str] | None = None
_SNAPSHOT_LOCK = threading.Lock()


def snapshot_template(dest: Path) -> tuple[str | None, str]:
    """Commit the working tree into a scratch clone, so an update can replay it.

    `copier update` replays the revision recorded in `_commit`, not the working
    tree. Pointing that at a git tag would test the tag instead of the change
    under test, so the copy is made from a commit containing exactly what is on
    disk now.
    """
    with _SNAPSHOT_LOCK:
        global _SNAPSHOT
        if _SNAPSHOT is not None:
            return _SNAPSHOT[0], ""
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(
            REPO_ROOT,
            dest,
            ignore=shutil.ignore_patterns(
                ".git", "__pycache__", ".ruff_cache", ".serena"
            ),
        )
        for args in (("init", "-q"), ("add", "-A"), ("commit", "-q", "-m", "snapshot")):
            result = git(dest, *args)
            if result.returncode != 0:
                return None, (result.stdout + result.stderr).strip()
        head = git(dest, "rev-parse", "HEAD")
        if head.returncode != 0:
            return None, (head.stdout + head.stderr).strip()
        _SNAPSHOT = (head.stdout.strip(), str(dest))
        return _SNAPSHOT[0], ""


def prepare_snapshot(out_dir: Path) -> None:
    """Build the snapshot before the pool opens, not inside one worker.

    `copier update` needs a commit of the working tree, and the copy is cheap
    but serialised behind a lock. Left to the adopt config it lands on the
    critical path of a single worker while the rest of the pool idles, which
    is what made the matrix slower than the copies it replaced.
    """
    snapshot_template(out_dir / "template-snapshot")


def adopt(copier: str, cfg: Config, dest: Path) -> tuple[bool, str]:
    """Prove the update path, not just the copy path.

    A project that already has its own `package.json` is copied from the
    template, then updated from it. The two runs are deliberately different
    revisions: the copy comes from the working tree so the project starts with
    the template's current answers, and the update replays a commit taken from
    the same working tree, so any file the template stopped skipping is
    regenerated. Recording the copy against a tag would test the tag.
    """
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "package.json").write_text(
        json.dumps({"name": "hand-written", "leftover-key": True}, indent=2) + "\n"
    )
    (dest / "README.md").write_text("# Hand written\n")

    snapshot, log = snapshot_template(dest.parent / "template-snapshot")
    if snapshot is None:
        return False, log

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
            "--data",
            f"repo_name=m-{cfg.name}",
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

    # `update` refuses a dirty destination. Rewrite `_commit` to the snapshot
    # before committing, so the single commit both cleans the tree and pins the
    # revision the update replays.
    answers = dest / ".copier-answers.yml"
    answers.write_text(
        "\n".join(
            f"_commit: {snapshot}" if line.startswith("_commit:") else line
            for line in answers.read_text().splitlines()
        )
        + "\n"
    )
    # `_src_path` is what `update` clones, and `_commit` is resolved inside that
    # clone — not in the destination, which already holds the commit. So the
    # answers must point at the snapshot repo as the source, or the update
    # fails with `Unknown revision: <snapshot>`.
    lines = answers.read_text().splitlines()
    snapshot_repo = _SNAPSHOT[1] if _SNAPSHOT else ""
    rewritten: list[str] = []
    for line in lines:
        if line.startswith("_src_path:"):
            rewritten.append(f"_src_path: {snapshot_repo}")
        elif line.startswith("_commit:"):
            rewritten.append(f"_commit: {snapshot}")
        else:
            rewritten.append(line)
    answers.write_text("\n".join(rewritten) + "\n")
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
    return check_output(cfg, dest)


def check_output(cfg: Config, dest: Path) -> list[str]:
    problems: list[str] = []
    check_json(dest, problems)
    check_yaml(dest, problems)
    check_jinja(dest, problems)
    check_blank_lines(dest, problems)
    check_usage_placeholder(dest, problems)
    check_gitignore(dest, problems)
    if cfg.adopt:
        check_manifest_overwritten(dest, problems)
    check_lint(dest, problems)
    check_audit(dest, problems)
    return problems


def check_detect_coverage(problems: list[str]) -> None:
    # Runs once, not per render: the registry describes the template, and a
    # question added without a marker or a stated reason is a gap in it.
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "template" / "scripts" / "detect.py"),
            "--check-coverage",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        # detail[0] is the header; every line after it is a question name.
        names = [
            line.strip().lstrip("- ").strip()
            for line in (proc.stdout + proc.stderr).strip().splitlines()[1:]
        ]
        problems.append(
            "detect.py --check-coverage failed: "
            + (", ".join(name for name in names if name) or "no output")
        )


def parse_shard(spec: str) -> tuple[int, int]:
    """Parse `N/M` into a zero-based shard index and a shard count."""
    match = re.fullmatch(r"(\d+)/(\d+)", spec.strip())
    if not match:
        raise argparse.ArgumentTypeError(f"expected N/M, got {spec!r}")
    index, count = int(match.group(1)), int(match.group(2))
    if count < 1 or not 0 <= index < count:
        raise argparse.ArgumentTypeError(f"shard {index}/{count} is out of range")
    return index, count


def shard(configs: list[Config], index: int, count: int) -> list[Config]:
    """Contiguous slice `index` of `count`.

    Contiguous rather than strided so a shard is a readable block of the matrix,
    and so adding a config shifts one shard instead of moving every one.
    """
    start = len(configs) * index // count
    end = len(configs) * (index + 1) // count
    return configs[start:end]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("names", nargs="*", help="config names to run (default: all)")
    parser.add_argument(
        "--list", action="store_true", help="list config names and exit"
    )
    parser.add_argument("--keep", action="store_true", help="keep the render directory")
    parser.add_argument("--out", help="render directory (implies --keep)")
    parser.add_argument(
        "--changed",
        action="store_true",
        help="only configs a changed path could affect (default: all)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="ignore the pass cache and render every selected config",
    )
    parser.add_argument(
        "--shard",
        type=parse_shard,
        metavar="N/M",
        help="render slice N of M selected configs (0-based), for a CI fan-out",
    )
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

    fingerprint = template_fingerprint()
    already_passed = {} if args.full else cached_configs(fingerprint)
    if args.changed:
        selected = changed_configs(selected)
        if not selected:
            print("=== no changed path reaches a config; nothing to render ===")
            return 0
    if args.shard:
        index, count = args.shard
        whole = selected
        selected = shard(selected, index, count)
        print(
            f"shard {index}/{count}: {len(selected)} of {len(whole)} selected config(s)"
        )
        if not selected:
            # A shard with no work is a fan-out bug, not a pass.
            print(f"=== shard {index}/{count} is empty ===")
            return 1
    skipped = [cfg for cfg in selected if cfg.name in already_passed]
    selected = [cfg for cfg in selected if cfg.name not in already_passed]
    if skipped:
        print(f"cached {len(skipped)} config(s) already passing this template")

    copier = copier_binary()
    keep = args.keep or bool(args.out)
    out_dir = (
        Path(args.out)
        if args.out
        else Path(tempfile.mkdtemp(prefix="template-matrix-"))
    )

    failures = 0
    coverage_problems: list[str] = []
    check_detect_coverage(coverage_problems)
    for problem in coverage_problems:
        failures += 1
        print("FAIL detect-coverage")
        print(f"     {problem}")
    if any(cfg.adopt for cfg in selected):
        prepare_snapshot(out_dir)
    results: dict[str, list[str]] = {}
    try:
        if selected:
            # Each config renders into its own directory, so the matrix is
            # independent work and the render dominates the runtime. Two workers
            # per core measured fastest: past that the renders contend without
            # gaining anything, and a host already busy makes it worse.
            workers = max((os.cpu_count() or 1) * 2, 4)
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=min(workers, len(selected))
            ) as pool:
                results = dict(
                    pool.map(
                        lambda c: (c.name, run_config(copier, c, out_dir)), selected
                    )
                )
    finally:
        if not keep:
            shutil.rmtree(out_dir, ignore_errors=True)

    if not args.changed:
        remember(fingerprint, {**already_passed, **results})
    for name, problems in results.items():
        if problems:
            failures += 1
            print(f"FAIL {name}")
            for problem in problems:
                print(f"     {problem}")
        else:
            print(f"ok   {name}")

    print()
    if failures:
        print(
            f"=== {failures} of {len(results)} configs failed, {len(skipped)} cached ==="
        )
        return 1
    print(f"=== {len(results)} configs passed, {len(skipped)} cached ===")
    if keep:
        print(f"renders: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
