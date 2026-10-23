"""Detect existing repo characteristics for copier template adoption."""

import json
import os
import argparse
import glob as _glob


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_registry():
    with open(os.path.join(_SCRIPT_DIR, "_registry.json")) as f:
        return json.load(f)


COPIER_YML = os.path.join(
    os.path.dirname(os.path.dirname(_SCRIPT_DIR)), "copier.yml"
)


def detectable_questions(registry):
    """Question names this registry can answer, read from copier.yml itself.

    Reading the questions rather than hard-coding them means a question added
    later without a marker fails the check below instead of going unnoticed.
    Only questions a user answers are considered: `when: false` marks a
    computed variable, and listing one would override its derivation. Choices
    (languages, ci_provider) are answered by their own marker tables.
    """
    import yaml

    with open(COPIER_YML) as f:
        config = yaml.safe_load(f)
    questions = []
    for name, spec in config.items():
        if name.startswith("_") or not isinstance(spec, dict):
            continue
        if spec.get("when") is False:
            continue
        if name in ("languages", "ci_provider"):
            continue
        questions.append(name)
    detectable = set(registry.get("tool_markers", {}))
    detectable |= set(registry.get("undetectable", {}))
    return [q for q in questions if q not in detectable]


def _glob_match(repo_path, pattern):
    return bool(_glob.glob(os.path.join(repo_path, pattern), recursive=False))


def detect(repo_path):
    registry = _load_registry()
    results = {"languages": [], "ci_provider": "none"}

    for lang, markers in registry["language_markers"].items():
        for marker in markers:
            if marker.startswith("*"):
                if _glob_match(repo_path, marker):
                    results["languages"].append(lang)
                    break
            elif os.path.exists(os.path.join(repo_path, marker)):
                results["languages"].append(lang)
                break

    # Root markers miss repos that keep their source below the root, e.g. a
    # Node package whose Python lives in bin/. These patterns are deliberately
    # anchored to a named subdirectory rather than matched recursively, and a
    # language found this way must also have a runtime present at the root:
    # stray .ts files in a Python repo say nothing about its language.
    runtimes = registry.get("nested_language_runtime", {})
    for lang, markers in registry.get("nested_language_markers", {}).items():
        if lang in results["languages"]:
            continue
        if not any(_glob_match(repo_path, marker) for marker in markers):
            continue
        if not any(
            _glob_match(repo_path, m)
            if m.startswith("*")
            else os.path.exists(os.path.join(repo_path, m))
            for m in runtimes.get(lang, [])
        ):
            continue
        results["languages"].append(lang)

    if "typescript" in results["languages"] and "javascript" not in results["languages"]:
        results["languages"].append("javascript")

    for provider, markers in registry["ci_markers"].items():
        for marker in markers:
            if marker.startswith("*"):
                if _glob_match(repo_path, marker):
                    results["ci_provider"] = provider
                    break
            elif os.path.exists(os.path.join(repo_path, marker)):
                results["ci_provider"] = provider
                break

    for tool, markers in registry["tool_markers"].items():
        results[tool] = any(
            _glob_match(repo_path, m) if m.startswith("*")
            else os.path.exists(os.path.join(repo_path, m))
            for m in markers
        )

    return results


def to_copier_args(results):
    args = []
    for key, value in results.items():
        if isinstance(value, list):
            quoted = ",".join(f'"{v}"' for v in value)
            args.append(f'--data {key}="[{quoted}]"')
        elif isinstance(value, bool):
            args.append(f'--data {key}=true' if value else f'--data {key}=false')
        else:
            args.append(f'--data {key}={value}')
    return " ".join(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect repo characteristics")
    parser.add_argument("repo_path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--check-coverage",
        action="store_true",
        help="fail if a copier.yml question is neither detected nor listed as undetectable",
    )
    args = parser.parse_args()
    if args.check_coverage:
        uncovered = detectable_questions(_load_registry())
        if uncovered:
            print("questions with no marker and no stated reason:")
            for name in uncovered:
                print(f"  - {name}")
            raise SystemExit(1)
        print("every question is detected or documented as undetectable")
        raise SystemExit(0)
    result = detect(args.repo_path)
    if args.json:
        print(json.dumps(result))
    else:
        print(to_copier_args(result))
