#!/usr/bin/env python3
"""Self-contained OpenSpec helpers bundled with goal-spec.

This file intentionally uses only the Python standard library. It exists so the
writer skill can scaffold and validate OpenSpec change packages even when the
target repository does not vendor openspec/scripts helpers and the harness does
not expose an openspec_workflow tool.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html as html_lib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
SOURCE_CANDIDATES = (
    ("proposal.md", "proposal"),
    ("design.md", "design"),
    ("tasks.md", "tasks"),
)
DEFAULT_REQUIRED_SECTIONS = [
    "why",
    "what-changes",
    "before-after",
    "flow",
    "affected-surfaces",
    "scope-boundaries",
    "rollout",
    "current-status",
]
DEFAULT_BACKLOG_MARKERS = [
    "backlog",
    "follow-up",
    "follow up",
    "後續",
    "待辦",
    "另案",
]
VIEWPORT_CASES = (
    ("mobile", 390, 844),
    ("tablet", 768, 1024),
    ("desktop", 1280, 800),
)
REMOTE_DEP_RE = re.compile(
    r'<(?:script|link|img|iframe|video|audio)[^>]+(?:src|href)=["\']https?://|@import\s+url\(["\']?https?://|url\(["\']?https?://',
    flags=re.IGNORECASE,
)
CHANGE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


@dataclass(slots=True)
class Policy:
    project_root: Path
    changes_dir: Path
    specs_dir: Path
    explainer_required: bool = True
    explainer_locale: str = "zh-Hant"
    explainer_required_sections: list[str] = field(default_factory=lambda: DEFAULT_REQUIRED_SECTIONS.copy())
    explainer_minimum_cjk_chars: int = 24
    explainer_require_viewport_meta: bool = True
    explainer_allow_remote_dependencies: bool = False
    skip_browser_layout_check_env: str = "OPENSPEC_GOAL_SPEC_SKIP_BROWSER_LAYOUT_CHECK"
    archive_require_explainer: bool = True
    archive_require_no_unchecked_tasks: bool = True
    archive_backlog_markers: list[str] = field(default_factory=lambda: DEFAULT_BACKLOG_MARKERS.copy())


@dataclass(slots=True)
class ValidationResult:
    status: str
    data: dict[str, Any]


def _strip_yaml_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    out: list[str] = []
    for ch in line:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\" and in_double:
            out.append(ch)
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        if ch == "#" and not in_single and not in_double:
            break
        out.append(ch)
    return "".join(out).rstrip()


def _scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if lowered in {"null", "none", "~"}:
        return None
    try:
        return int(value)
    except ValueError:
        return value


def _yaml_top_block(text: str, key: str) -> str:
    pattern = re.compile(rf"(?ms)^{re.escape(key)}:\s*\n(?P<body>(?:[ \t]+.*(?:\n|$))*)")
    match = pattern.search(text)
    return match.group("body") if match else ""


def _yaml_value(block: str, key: str) -> Any | None:
    match = re.search(rf"(?m)^\s+{re.escape(key)}:\s*([^\n]*)$", block)
    if not match:
        return None
    value = _strip_yaml_comment(match.group(1))
    return _scalar(value)


def _yaml_list(block: str, key: str) -> list[str] | None:
    match = re.search(rf"(?ms)^\s+{re.escape(key)}:\s*\n(?P<body>(?:\s+-\s+.*(?:\n|$))*)", block)
    if not match:
        return None
    items: list[str] = []
    for line in match.group("body").splitlines():
        item = re.sub(r"^\s+-\s+", "", _strip_yaml_comment(line)).strip()
        if item:
            value = _scalar(item)
            if value is not None:
                items.append(str(value))
    return items or None


def _resolve_dir(project_root: Path, raw: Any, default: str) -> Path:
    rel = str(raw or default)
    path = Path(rel)
    return path if path.is_absolute() else project_root / path


def load_policy(project_root: Path, policy_path: Path | None = None) -> Policy:
    policy = Policy(
        project_root=project_root,
        changes_dir=project_root / "openspec" / "changes",
        specs_dir=project_root / "openspec" / "specs",
    )
    path = policy_path or (project_root / ".openspec-workflow.yaml")
    if not path.exists():
        return policy

    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text())
        if not isinstance(payload, dict):
            raise ValueError(f"Policy file must contain an object: {path}")
        project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
        explainer = payload.get("changeExplainer") if isinstance(payload.get("changeExplainer"), dict) else {}
        archive = payload.get("archive") if isinstance(payload.get("archive"), dict) else {}
        policy.changes_dir = _resolve_dir(project_root, project.get("changesDir"), "openspec/changes")
        policy.specs_dir = _resolve_dir(project_root, project.get("specsDir"), "openspec/specs")
        if "required" in explainer:
            policy.explainer_required = bool(explainer["required"])
        if "locale" in explainer:
            policy.explainer_locale = str(explainer["locale"])
        if isinstance(explainer.get("requiredSections"), list) and explainer["requiredSections"]:
            policy.explainer_required_sections = [str(item) for item in explainer["requiredSections"]]
        if "minimumCjkChars" in explainer:
            policy.explainer_minimum_cjk_chars = int(explainer["minimumCjkChars"])
        if "requireViewportMeta" in explainer:
            policy.explainer_require_viewport_meta = bool(explainer["requireViewportMeta"])
        if "allowRemoteDependencies" in explainer:
            policy.explainer_allow_remote_dependencies = bool(explainer["allowRemoteDependencies"])
        if "skipBrowserLayoutCheckEnv" in explainer:
            policy.skip_browser_layout_check_env = str(explainer["skipBrowserLayoutCheckEnv"])
        if "requireExplainer" in archive:
            policy.archive_require_explainer = bool(archive["requireExplainer"])
        if "requireNoUncheckedTasks" in archive:
            policy.archive_require_no_unchecked_tasks = bool(archive["requireNoUncheckedTasks"])
        if isinstance(archive.get("backlogMarkers"), list) and archive["backlogMarkers"]:
            policy.archive_backlog_markers = [str(item).lower() for item in archive["backlogMarkers"]]
        return policy

    text = path.read_text()
    project_block = _yaml_top_block(text, "project")
    if project_block:
        policy.changes_dir = _resolve_dir(project_root, _yaml_value(project_block, "changesDir"), "openspec/changes")
        policy.specs_dir = _resolve_dir(project_root, _yaml_value(project_block, "specsDir"), "openspec/specs")

    explainer_block = _yaml_top_block(text, "changeExplainer")
    if explainer_block:
        value = _yaml_value(explainer_block, "required")
        if value is not None:
            policy.explainer_required = bool(value)
        value = _yaml_value(explainer_block, "locale")
        if value:
            policy.explainer_locale = str(value)
        values = _yaml_list(explainer_block, "requiredSections")
        if values:
            policy.explainer_required_sections = values
        value = _yaml_value(explainer_block, "minimumCjkChars")
        if value is not None:
            policy.explainer_minimum_cjk_chars = int(value)
        value = _yaml_value(explainer_block, "requireViewportMeta")
        if value is not None:
            policy.explainer_require_viewport_meta = bool(value)
        value = _yaml_value(explainer_block, "allowRemoteDependencies")
        if value is not None:
            policy.explainer_allow_remote_dependencies = bool(value)
        value = _yaml_value(explainer_block, "skipBrowserLayoutCheckEnv")
        if value:
            policy.skip_browser_layout_check_env = str(value)

    archive_block = _yaml_top_block(text, "archive")
    if archive_block:
        value = _yaml_value(archive_block, "requireExplainer")
        if value is not None:
            policy.archive_require_explainer = bool(value)
        value = _yaml_value(archive_block, "requireNoUncheckedTasks")
        if value is not None:
            policy.archive_require_no_unchecked_tasks = bool(value)
        values = _yaml_list(archive_block, "backlogMarkers")
        if values:
            policy.archive_backlog_markers = [item.lower() for item in values]

    return policy


def change_dir(policy: Policy, change_name: str) -> Path:
    return policy.changes_dir / change_name


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def detect_sources(base: Path) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    for rel, kind in SOURCE_CANDIDATES:
        path = base / rel
        if path.exists():
            sources.append({"path": rel, "kind": kind, "sha256": sha256_file(path)})
    specs_dir = base / "specs"
    if specs_dir.exists():
        for spec_path in sorted(specs_dir.rglob("spec.md")):
            sources.append(
                {
                    "path": spec_path.relative_to(base).as_posix(),
                    "kind": "spec-delta",
                    "sha256": sha256_file(spec_path),
                }
            )
    return sources


def build_manifest(change_name: str, base: Path) -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "changeName": change_name,
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sources": detect_sources(base),
    }


def write_manifest(change_name: str, base: Path) -> Path:
    manifest = build_manifest(change_name, base)
    output = base / "source-manifest.json"
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return output


def validate_manifest(change_name: str, base: Path) -> ValidationResult:
    manifest_path = base / "source-manifest.json"
    errors: list[str] = []
    stale: list[str] = []
    missing: list[str] = []

    if not manifest_path.exists():
        return ValidationResult(
            "fail",
            {
                "changeName": change_name,
                "manifestFile": str(manifest_path),
                "errors": ["missing_source_manifest"],
            },
        )

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as err:
        return ValidationResult(
            "fail",
            {
                "changeName": change_name,
                "manifestFile": str(manifest_path),
                "errors": [f"invalid_json: {err}"],
            },
        )

    if not isinstance(manifest, dict):
        errors.append("source-manifest root must be an object")
    else:
        allowed = {"schemaVersion", "changeName", "generatedAt", "sources"}
        extra = sorted(set(manifest) - allowed)
        if extra:
            errors.append("unexpected source-manifest keys: " + ", ".join(extra))
        if manifest.get("schemaVersion") != SCHEMA_VERSION:
            errors.append("source-manifest.schemaVersion must be 1.0")
        if manifest.get("changeName") != change_name:
            errors.append("source-manifest.changeName does not match target change")
        if not isinstance(manifest.get("generatedAt"), str) or not manifest.get("generatedAt"):
            errors.append("source-manifest.generatedAt must be a non-empty string")
        sources = manifest.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append("source-manifest.sources must be a non-empty array")
            sources = []
        for index, src in enumerate(sources):
            if not isinstance(src, dict):
                errors.append(f"source-manifest.sources[{index}] must be an object")
                continue
            extra_src = sorted(set(src) - {"path", "kind", "sha256"})
            if extra_src:
                errors.append(f"source-manifest.sources[{index}] has unexpected keys: " + ", ".join(extra_src))
            rel = src.get("path")
            kind = src.get("kind")
            digest = src.get("sha256")
            if not isinstance(rel, str) or not rel:
                errors.append(f"source-manifest.sources[{index}].path must be a non-empty string")
                continue
            rel_path = Path(rel)
            if rel_path.is_absolute() or ".." in rel_path.parts:
                errors.append(f"source-manifest.sources[{index}].path must stay inside the change directory")
                continue
            if kind not in {"proposal", "design", "tasks", "spec-delta"}:
                errors.append(f"source-manifest.sources[{index}].kind is invalid")
            if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                errors.append(f"source-manifest.sources[{index}].sha256 must be a lowercase sha256 hex digest")
                continue
            path = base / rel
            if not path.exists():
                missing.append(rel)
            elif sha256_file(path) != digest:
                stale.append(rel)

    if missing:
        errors.append("missing source files referenced by source-manifest.json")
    if stale:
        errors.append("stale source hashes in source-manifest.json")

    data: dict[str, Any] = {
        "changeName": change_name,
        "manifestFile": str(manifest_path),
        "staleCount": len(stale),
        "missingSourceCount": len(missing),
    }
    if stale:
        data["stale"] = stale
    if missing:
        data["missingSources"] = missing
    if errors:
        data["errors"] = errors
        return ValidationResult("fail", data)
    return ValidationResult("ok", data)


def strip_tags(text: str) -> str:
    text = re.sub(r"<script\b[\s\S]*?</script>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<style\b[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<!--([\s\S]*?)-->", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return html_lib.unescape(text)


def attrs_for_tag(tag: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in re.finditer(r"([:\w-]+)\s*=\s*(['\"])(.*?)\2", tag, flags=re.DOTALL):
        attrs[match.group(1).lower()] = html_lib.unescape(match.group(3))
    return attrs


def has_meta(text: str, name: str, content: str | None = None) -> bool:
    for match in re.finditer(r"<meta\b[^>]*>", text, flags=re.IGNORECASE):
        attrs = attrs_for_tag(match.group(0))
        if attrs.get("name", "").lower() != name.lower():
            continue
        if content is None:
            return True
        if attrs.get("content", "").lower() == content.lower():
            return True
    return False


def has_id(text: str, section_id: str) -> bool:
    return bool(re.search(rf"\bid\s*=\s*(['\"]){re.escape(section_id)}\1", text, flags=re.IGNORECASE))


def find_browser() -> str | None:
    for name in ("google-chrome", "chromium", "chromium-browser"):
        path = shutil.which(name)
        if path:
            return path
    return None


def build_probe_html(target_html: str) -> str:
    source = json.dumps(target_html).replace("</", "<\\/")
    cases = json.dumps([{"name": name, "width": width, "height": height} for name, width, height in VIEWPORT_CASES])
    return f"""<!doctype html>
<html>
<head><meta charset=\"utf-8\"><title>goal-spec-layout-probe</title></head>
<body>
<pre id=\"result\">pending</pre>
<script>
const source = {source};
const cases = {cases};
async function wait(ms) {{ return new Promise((resolve) => setTimeout(resolve, ms)); }}
async function runCase(spec) {{
  const host = document.createElement('div');
  host.style.width = spec.width + 'px';
  host.style.height = spec.height + 'px';
  host.style.position = 'absolute';
  host.style.left = '0';
  host.style.top = '0';
  host.style.overflow = 'hidden';
  const frame = document.createElement('iframe');
  frame.setAttribute('sandbox', 'allow-scripts allow-same-origin');
  frame.style.width = '100%';
  frame.style.height = '100%';
  frame.style.border = '0';
  host.appendChild(frame);
  document.body.appendChild(host);
  await new Promise((resolve) => {{
    let finished = false;
    const done = () => {{
      if (finished) return;
      finished = true;
      setTimeout(resolve, 300);
    }};
    frame.onload = done;
    setTimeout(done, 1500);
    frame.srcdoc = source;
  }});
  const doc = frame.contentDocument;
  const root = doc && doc.documentElement ? doc.documentElement : null;
  const body = doc && doc.body ? doc.body : root;
  const scrollWidth = Math.max(root ? root.scrollWidth : 0, body ? body.scrollWidth : 0);
  const clientWidth = frame.clientWidth;
  const offscreen = [];
  if (doc && body) {{
    const walker = doc.createTreeWalker(body, NodeFilter.SHOW_ELEMENT);
    while (walker.nextNode()) {{
      const el = walker.currentNode;
      const rect = el.getBoundingClientRect();
      if (!rect || rect.width <= 0 || rect.height <= 0) continue;
      if (rect.left < clientWidth && rect.right > clientWidth + 4) {{
        offscreen.push(el.tagName.toLowerCase());
        if (offscreen.length >= 8) break;
      }}
    }}
  }}
  host.remove();
  return {{
    name: spec.name,
    width: spec.width,
    height: spec.height,
    scrollWidth,
    clientWidth,
    horizontalOverflow: scrollWidth > clientWidth + 2,
    offscreenCount: offscreen.length,
    offscreen,
    pass: scrollWidth <= clientWidth + 2 && offscreen.length === 0,
  }};
}}
(async () => {{
  const results = [];
  for (const spec of cases) {{
    results.push(await runCase(spec));
    await wait(50);
  }}
  document.getElementById('result').textContent = JSON.stringify(results);
}})().catch((err) => {{
  document.getElementById('result').textContent = JSON.stringify({{error: String(err)}});
}});
</script>
</body>
</html>
"""


def run_browser_probe(browser: str, target_html: str) -> list[dict[str, Any]]:
    probe_html = build_probe_html(target_html)
    with tempfile.TemporaryDirectory(prefix="goal-spec-layout-") as tmpdir:
        probe_path = Path(tmpdir) / "probe.html"
        probe_path.write_text(probe_html)
        base_args = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--allow-file-access-from-files",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=10000",
            "--dump-dom",
            probe_path.as_uri(),
        ]
        proc = subprocess.run(base_args, check=False, capture_output=True, text=True, timeout=20)
        if proc.returncode != 0:
            fallback = base_args.copy()
            fallback[1] = "--headless"
            proc = subprocess.run(fallback, check=False, capture_output=True, text=True, timeout=20)
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout or "browser probe failed").strip())
        match = re.search(r'<pre\b[^>]*id=["\']result["\'][^>]*>([\s\S]*?)</pre>', proc.stdout)
        if not match:
            raise RuntimeError("browser probe did not produce a result payload")
        payload = html_lib.unescape(match.group(1).strip())
        if not payload or payload == "pending":
            raise RuntimeError("browser probe result was not ready")
        data = json.loads(payload)
        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(str(data["error"]))
        if not isinstance(data, list):
            raise RuntimeError("browser probe result was not a list")
        return data


def validate_presentation(html_path: Path, policy: Policy, *, skip_browser_layout: bool = False) -> ValidationResult:
    if not html_path.exists():
        return ValidationResult("fail", {"htmlFile": str(html_path), "errors": ["missing_html_file"]})
    text = html_path.read_text(errors="replace")
    lang_match = re.search(r'<html\b[^>]*\blang=["\']([^"\']+)["\']', text, flags=re.IGNORECASE)
    lang_value = lang_match.group(1) if lang_match else ""
    viewport_present = has_meta(text, "viewport")
    visible_text = strip_tags(text)
    cjk_count = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", visible_text))

    fixed_stage_markers: list[str] = []
    if re.search(r"width\s*:\s*1920px", text, flags=re.IGNORECASE):
        fixed_stage_markers.append("width_1920px")
    if re.search(r"(?:height|min-height)\s*:\s*1080px", text, flags=re.IGNORECASE):
        fixed_stage_markers.append("height_1080px")
    if re.search(r"transform-origin\s*:\s*top left", text, flags=re.IGNORECASE):
        fixed_stage_markers.append("transform_origin_top_left")
    if re.search(r"\bscaleDeck\s*\(", text):
        fixed_stage_markers.append("scaleDeck_js")
    if 'id="viewport"' in text and 'id="deck"' in text:
        fixed_stage_markers.append("viewport_deck_ids")

    browser_status = "not_run"
    browser_cases: list[dict[str, Any]] = []
    browser_error = ""
    browser = find_browser()
    skip_env_names = {
        policy.skip_browser_layout_check_env,
        "OPENSPEC_AGW_SKIP_BROWSER_LAYOUT_CHECK",  # legacy goal-writer compatibility
        "OPENSPEC_WORKFLOW_SKIP_BROWSER_LAYOUT_CHECK",
    }
    if skip_browser_layout or any(os.environ.get(name) == "1" for name in skip_env_names):
        browser_status = "skipped_by_env_or_flag"
    elif policy.explainer_require_viewport_meta and not viewport_present:
        browser_status = "skipped_missing_viewport"
    elif fixed_stage_markers:
        browser_status = "skipped_fixed_stage_detected"
    elif browser is None:
        browser_status = "browser_missing"
        browser_error = "Chrome/Chromium is required for browser layout confirmation"
    else:
        try:
            browser_cases = run_browser_probe(browser, text)
            browser_status = "ok"
        except Exception as err:  # noqa: BLE001
            browser_status = "probe_failed"
            browser_error = str(err)

    errors: list[str] = []
    if lang_value.lower() != policy.explainer_locale.lower():
        errors.append("missing_expected_lang")
    if policy.explainer_require_viewport_meta and not viewport_present:
        errors.append("missing_viewport_meta")
    if cjk_count < policy.explainer_minimum_cjk_chars:
        errors.append("insufficient_cjk_copy")
    if fixed_stage_markers:
        errors.append("fixed_stage_layout_detected")
    if browser_status in {"browser_missing", "probe_failed"}:
        errors.append("layout_confirmation_unavailable")
    if browser_cases and any(not bool(case.get("pass")) for case in browser_cases):
        errors.append("layout_overflow_detected")

    data: dict[str, Any] = {
        "htmlFile": str(html_path),
        "htmlLang": lang_value or "missing",
        "expectedLang": policy.explainer_locale,
        "viewportMeta": "present" if viewport_present else "missing",
        "cjkCharCount": cjk_count,
        "minimumCjkCharCount": policy.explainer_minimum_cjk_chars,
        "fixedStageMarkers": fixed_stage_markers or ["none"],
        "layoutBrowserStatus": browser_status,
    }
    if browser:
        data["layoutBrowserBin"] = browser
    if browser_cases:
        data["layoutCases"] = browser_cases
    if browser_error:
        data["layoutBrowserError"] = browser_error
    if errors:
        data["errors"] = errors
        return ValidationResult("fail", data)
    return ValidationResult("ok", data)


def _check_regex(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL))


def validate_decision_review_contract(text: str) -> ValidationResult:
    checks: dict[str, bool] = {
        "mode_meta": has_meta(text, "openspec-explainer-mode", "decision-review"),
        "primary_navigation": _check_regex(text, r"<nav\b|role=[\"']navigation[\"']"),
        "before_after": has_id(text, "before-after") and _check_regex(text, r"變更前|before") and _check_regex(text, r"變更後|after"),
        "decision_points": _check_regex(text, r"decision[-_ ]?point|data-[\w-]*decision|id=[\"'][^\"']*decision|決策點|決策"),
        "implementation_slices": _check_regex(text, r"implementation[-_ ]?slice|實作切片|交付切片|slice"),
        "verification_plan": _check_regex(text, r"verification[-_ ]?plan|驗證計畫|驗證方案|驗證"),
        "risk_register": _check_regex(text, r"risk[-_ ]?register|風險登錄|風險清單|風險"),
        "high_risk_filter": _check_regex(text, r"high[-_ ]?risk|高風險") and _check_regex(text, r"filter|篩選|data-filter"),
        "copy_controls": _check_regex(text, r"navigator\.clipboard|data-copy|copy-button|複製"),
        "task_json_export": _check_regex(text, r"task[-_ ]?json|tasks[-_ ]?json|任務\s*JSON|application/json"),
        "implementation_agent_prompt": _check_regex(text, r"implementation[^<]{0,80}agent[^<]{0,80}prompt|實作[^<]{0,80}agent[^<]{0,80}prompt|實作代理提示"),
        "review_agent_prompt": _check_regex(text, r"review[^<]{0,80}agent[^<]{0,80}prompt|審查[^<]{0,80}agent[^<]{0,80}prompt|reviewer[^<]{0,80}prompt"),
        "verification_agent_prompt": _check_regex(text, r"verification[^<]{0,80}agent[^<]{0,80}prompt|驗證[^<]{0,80}agent[^<]{0,80}prompt|測試[^<]{0,80}agent[^<]{0,80}prompt"),
        "svg_visual": _check_regex(text, r"<svg\b"),
        "responsive_css": _check_regex(text, r"@media\b") and has_meta(text, "viewport"),
    }
    missing = [name for name, ok in checks.items() if not ok]
    data: dict[str, Any] = {"checks": checks}
    if missing:
        data["missing"] = missing
        data["errors"] = ["missing_decision_review_affordances"]
        return ValidationResult("fail", data)
    return ValidationResult("ok", data)


def validate_explainer(
    change_name: str,
    base: Path,
    policy: Policy,
    *,
    require_decision_review: bool = False,
    skip_browser_layout: bool = False,
) -> ValidationResult:
    html_path = base / "change-explainer.html"
    if not html_path.exists():
        return ValidationResult(
            "fail",
            {
                "changeName": change_name,
                "changeDir": str(base),
                "explainerFile": str(html_path),
                "errors": ["missing_explainer_file"],
            },
        )

    text = html_path.read_text(errors="replace").replace("\r", "")
    missing_markers = [section_id for section_id in policy.explainer_required_sections if not has_id(text, section_id)]

    errors: list[str] = []
    if not re.search(r"<html\b", text, flags=re.IGNORECASE):
        errors.append("html_root_missing")
    if not re.search(r"<body\b", text, flags=re.IGNORECASE):
        errors.append("body_root_missing")
    if missing_markers:
        errors.append("missing_required_markers")
    if not policy.explainer_allow_remote_dependencies and REMOTE_DEP_RE.search(text):
        errors.append("remote_runtime_dependency_detected")

    presentation = validate_presentation(html_path, policy, skip_browser_layout=skip_browser_layout)
    manifest = validate_manifest(change_name, base)
    decision_review = None
    env_requires_decision_review = os.environ.get("OPENSPEC_CHANGE_EXPLAINER_REQUIRE_DECISION_REVIEW") == "1"
    if require_decision_review or env_requires_decision_review:
        decision_review = validate_decision_review_contract(text)
        if decision_review.status != "ok":
            errors.append("invalid_decision_review_contract")
    if presentation.status != "ok":
        errors.append("invalid_presentation_contract")
    if manifest.status != "ok":
        errors.append("invalid_source_manifest")

    data: dict[str, Any] = {
        "changeName": change_name,
        "changeDir": str(base),
        "explainerFile": str(html_path),
        "presentation": presentation.data,
        "sourceManifest": manifest.data,
    }
    if decision_review is not None:
        data["decisionReview"] = decision_review.data
    if missing_markers:
        data["missingMarkers"] = missing_markers
    if errors:
        data["errors"] = errors
        return ValidationResult("fail", data)
    return ValidationResult("ok", data)


def find_blocking_tasks(tasks_path: Path, backlog_markers: list[str]) -> dict[str, list[str]]:
    if not tasks_path.exists():
        return {"blocking": ["tasks.md not found"], "backlog": []}
    current_heading = ""
    blocking: list[str] = []
    backlog: list[str] = []
    for raw_line in tasks_path.read_text().splitlines():
        line = raw_line.strip()
        if line.startswith("#"):
            current_heading = line.lstrip("#").strip().lower()
            continue
        if line.lower().startswith("- [x]") or line.lower().startswith("- [~]"):
            continue
        if not line.startswith("- [ ]"):
            continue
        lowered = line.lower()
        is_backlog = "[backlog]" in lowered or any(marker in current_heading for marker in backlog_markers)
        if is_backlog:
            backlog.append(line)
        else:
            blocking.append(line)
    return {"blocking": blocking, "backlog": backlog}


PROPOSAL_TEMPLATE = """# {change_name}

## Why

Describe the problem, pressure, or opportunity that makes this change necessary.

## What Changes

- Describe the main behavior or workflow changes.
- Describe the main artifacts or modules affected.
- Describe any important constraints or non-goals.

## Impact

- Affected specs: `{capability}`
- Affected modules/repos: `TBD`
- Affected APIs/events/data: `TBD`
- Migration/deployment impact: `TBD`
- User-visible impact: `TBD`

## Non-Goals

- TBD

## Success Signal

Describe observable proof that the change achieved its goal.

## Assumptions

- [ASSUMPTION] TBD

## Open Questions

- [ ] TBD
"""

DESIGN_TEMPLATE = """# Design: {change_name}

## Context

Summarize the current state and the design pressure behind the change.

## Spec Kernel

- Why: TBD
- Capabilities:
  - TBD
- Constraints:
  - TBD
- Non-goals:
  - TBD
- Success signal: TBD

## Goals

- Goal 1
- Goal 2

## Non-Goals

- Non-goal 1

## Concern Scan

| Concern | Relevance | Design response |
| --- | --- | --- |
| TBD | TBD | TBD |

## Decisions

### D1. Name the first decision

**Choice**
Describe the chosen direction.

**Rationale**
Explain why this direction is preferred.

**Alternatives considered**
- Alternative: why rejected or deferred.

## Detailed Design

### Data / Contract Changes

TBD

### Execution Flow

TBD

### Module Boundaries

TBD

### Migration / Rollout

TBD

## Risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| TBD | TBD | TBD |

## Verification Plan

- TBD

## Load-Bearing Preservation Notes

- TBD
"""

TASKS_TEMPLATE = """# Tasks: {change_name}

## 1. Spec and Contract

- [ ] 1.1 Update `{capability}` spec delta.
- [ ] 1.2 Confirm affected APIs/events/data contracts.

## 2. Implementation

- [ ] 2.1 Implement the required behavior.

## 3. Verification

- [ ] 3.1 Run relevant validation commands.
- [ ] 3.2 Validate `change-explainer.html` with the bundled writer helper.

## 4. Documentation / Closeout

- [ ] 4.1 Update relevant docs if user-visible behavior, API contracts, deployment, module responsibility, or cross-module interaction changed.
- [ ] 4.2 Refresh `source-manifest.json`.
- [ ] 4.3 Validate `change-explainer.html` if required.
- [ ] 4.4 Run archive preflight when implementation is complete.

## Backlog / Follow-ups

- [ ] [BACKLOG] Optional polish or future follow-up.
"""

SPEC_TEMPLATE = """# {capability} Specification

## Purpose

Describe what this capability owns.

## Requirements

### Requirement: TBD

The system SHALL provide the required behavior described by this change.

#### Scenario: TBD

- **GIVEN** TBD
- **WHEN** TBD
- **THEN** TBD
"""

SPEC_YAML_TEMPLATE = """name: {change_name}
created: {created}
status: draft
"""


def scaffold_change(policy: Policy, change_name: str, capability: str | None, *, force: bool = False, no_manifest: bool = False) -> Path:
    if not CHANGE_NAME_RE.fullmatch(change_name):
        raise ValueError("change name must be kebab-case: ^[a-z0-9][a-z0-9-]*$")
    cap = capability or "change-capability"
    if not CHANGE_NAME_RE.fullmatch(cap):
        raise ValueError("capability name must be kebab-case: ^[a-z0-9][a-z0-9-]*$")
    base = change_dir(policy, change_name)
    if base.exists() and any(base.iterdir()) and not force:
        raise FileExistsError(f"Change already exists and is not empty: {base}")
    base.mkdir(parents=True, exist_ok=True)
    created = dt.datetime.now(dt.timezone.utc).date().isoformat()
    (base / ".openspec.yaml").write_text(SPEC_YAML_TEMPLATE.format(change_name=change_name, created=created))
    (base / "proposal.md").write_text(PROPOSAL_TEMPLATE.format(change_name=change_name, capability=cap))
    (base / "design.md").write_text(DESIGN_TEMPLATE.format(change_name=change_name))
    (base / "tasks.md").write_text(TASKS_TEMPLATE.format(change_name=change_name, capability=cap))
    spec_dir = base / "specs" / cap
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "spec.md").write_text(SPEC_TEMPLATE.format(capability=cap))
    if not no_manifest:
        write_manifest(change_name, base)
    return base


def publish_closeout(
    change_name: str,
    base: Path,
    policy: Policy,
    *,
    remote: str = "origin",
    branch: str | None = None,
    commit_message: str | None = None,
    non_published: bool = False,
    require_decision_review: bool = False,
    skip_browser_layout: bool = False,
) -> dict[str, Any]:
    """Publish closeout for an OpenSpec change package.

    Validation-first closeout:
      1. Validate source-manifest.json and required change-explainer.html.
      2. Compute owned paths under openspec/changes/<change-name>/,
         excluding .goal-spec/ operational artifacts.
      3. Stage only owned paths.
      4. Block on unrelated dirty files or ambiguous owned paths.
      5. Block on detached HEAD, missing upstream, or missing remote.
      6. Commit with a generated or provided message.
      7. Non-force push to the remote branch.
      8. Verify the remote branch contains the pushed commit.
      9. Re-check worktree cleanliness.
     10. Support explicit non-published mode (skip commit/push, report as such).

    Returns a result dict with mode, diagnostics, and optional commitSha.
    """
    report: dict[str, Any] = {
        "changeName": change_name,
        "changeDir": str(base),
        "mode": "blocked",
        "diagnostics": [],
        "checks": {},
    }

    if not base.exists():
        report["diagnostics"].append({
            "severity": "blocker",
            "code": "change_directory_not_found",
            "message": f"Change directory not found: {base}",
        })
        return report

    cwd = policy.project_root

    # ------------------------------------------------------------------
    # 1. Validation-first: validate source-manifest and explainer
    # ------------------------------------------------------------------
    manifest = validate_manifest(change_name, base)
    report["checks"]["sourceManifest"] = {"status": manifest.status, **manifest.data}
    if manifest.status != "ok":
        report["diagnostics"].append({
            "severity": "blocker",
            "code": "invalid_source_manifest",
            "message": "source-manifest.json validation failed; cannot publish with invalid manifest",
        })

    if policy.explainer_required:
        explainer = validate_explainer(
            change_name,
            base,
            policy,
            require_decision_review=require_decision_review,
            skip_browser_layout=skip_browser_layout,
        )
        report["checks"]["explainer"] = {"status": explainer.status, **explainer.data}
        if explainer.status != "ok":
            report["diagnostics"].append({
                "severity": "blocker",
                "code": "invalid_change_explainer",
                "message": "change-explainer.html validation failed; cannot publish with invalid explainer",
            })

    # If validation failed, return early with diagnostics
    if any(d["severity"] == "blocker" for d in report["diagnostics"]):
        return report

    # ------------------------------------------------------------------
    # 2. Non-published mode: skip all git operations
    # ------------------------------------------------------------------
    if non_published:
        report["mode"] = "non_published"
        report["diagnostics"].append({
            "severity": "info",
            "code": "non_published_mode",
            "message": "Non-published mode: skipping commit and push. Closeout result labeled as non-published.",
        })
        return report

    # ------------------------------------------------------------------
    # 3. Compute owned paths
    # ------------------------------------------------------------------
    # Owned paths are everything under openspec/changes/<change-name>/
    # except .goal-spec/ operational artifacts. Also include source-manifest.json
    # and change-explainer.html at the change root.
    owned_relative = f"openspec/changes/{change_name}"
    owned_path_str = owned_relative.replace("/", os.sep)

    # ------------------------------------------------------------------
    # 4-5. Git status and staging
    # ------------------------------------------------------------------
    try:
        # Check for detached HEAD
        result = subprocess.run(
            ["git", "symbolic-ref", "-q", "HEAD"],
            capture_output=True, text=True, cwd=cwd, timeout=15,
        )
        if result.returncode != 0:
            report["diagnostics"].append({
                "severity": "blocker",
                "code": "detached_head",
                "message": "Git HEAD is detached; cannot publish from detached state. Switch to a branch first.",
            })
            return report

        current_branch = result.stdout.strip().removeprefix("refs/heads/")
        target_branch = branch or current_branch

        # Check for missing upstream
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", f"{target_branch}@{{upstream}}"],
            capture_output=True, text=True, cwd=cwd, timeout=15,
        )
        upstream_ref = f"refs/remotes/{remote}/{target_branch}"
        if result.returncode != 0:
            report["diagnostics"].append({
                "severity": "blocker",
                "code": "missing_upstream",
                "message": f"Branch '{target_branch}' has no upstream tracking branch on '{remote}'. Set upstream or push manually.",
            })
            # Check if remote exists at all
            result_remote = subprocess.run(
                ["git", "remote", "get-url", remote],
                capture_output=True, text=True, cwd=cwd, timeout=15,
            )
            if result_remote.returncode != 0:
                report["diagnostics"].append({
                    "severity": "blocker",
                    "code": "missing_remote",
                    "message": f"Remote '{remote}' is not configured.",
                })
            return report

        # Check for unrelated dirty files
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=cwd, timeout=15,
        )
        porcelain_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]

        if porcelain_lines:
            # Classify changes
            owned_prefix = owned_path_str + os.sep
            owned_variants = [
                owned_path_str,                   # openspec/changes/<name>
                owned_relative.replace("/", os.sep),  # same, differently resolved
            ]

            unrelated_paths: list[str] = []
            staging_paths: list[str] = []

            for line in porcelain_lines:
                # Status format: XY filename or XY filename -> renamed
                if len(line) < 3:
                    continue
                status_code = line[:2].strip()
                # Handle rename: "R  from -> to" or "R  from -> to"
                filepath_part = line[3:].strip()
                if " -> " in filepath_part:
                    # Rename: status line is like "R  oldpath -> newpath"
                    parts = filepath_part.split(" -> ")
                    filepath_part = parts[-1].strip()

                # Normalize path separators
                normalized_path = filepath_part.replace("/", os.sep)

                # Check if path is owned
                is_owned = normalized_path.startswith(owned_prefix) or normalized_path.startswith(owned_path_str + os.sep) or normalized_path == owned_path_str

                # Exclude .goal-spec/ paths (operational artifacts)
                if is_owned:
                    # Check it's not inside .goal-spec/
                    if ".goal-spec" in normalized_path.split(os.sep):
                        continue

                if is_owned:
                    staging_paths.append(normalized_path)
                else:
                    unrelated_paths.append(normalized_path)

            if unrelated_paths:
                report["diagnostics"].append({
                    "severity": "blocker",
                    "code": "unrelated_dirty_files",
                    "message": f"Unrelated dirty files prevent clean closeout: {unrelated_paths}",
                })
                return report

        # Check if there's anything to commit
        if not porcelain_lines:
            report["mode"] = "no_changes"
            report["diagnostics"].append({
                "severity": "info",
                "code": "no_changes",
                "message": "No changes to commit; worktree is clean.",
            })
            return report

        # ------------------------------------------------------------------
        # 5. Stage only owned paths
        # ------------------------------------------------------------------
        if staging_paths:
            subprocess.run(
                ["git", "add", "--"] + staging_paths,
                capture_output=True, text=True, cwd=cwd, timeout=15, check=True,
            )

        # ------------------------------------------------------------------
        # 6. Create commit
        # ------------------------------------------------------------------
        msg = commit_message or f"goal-spec closeout: {change_name}"
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            capture_output=True, text=True, cwd=cwd, timeout=15,
        )
        if result.returncode != 0:
            report["diagnostics"].append({
                "severity": "blocker",
                "code": "commit_failed",
                "message": f"Git commit failed: {result.stderr.strip() or result.stdout.strip()}",
            })
            return report

        # Extract commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=cwd, timeout=15, check=True,
        )
        commit_sha = result.stdout.strip()
        report["commitSha"] = commit_sha

        # ------------------------------------------------------------------
        # 7. Non-force push
        # ------------------------------------------------------------------
        try:
            result = subprocess.run(
                ["git", "push", "--no-force", remote, target_branch],
                capture_output=True, text=True, cwd=cwd, timeout=60,
            )
        except subprocess.TimeoutExpired:
            report["diagnostics"].append({
                "severity": "blocker",
                "code": "push_timeout",
                "message": f"Git push to {remote}/{target_branch} timed out after 60s.",
            })
            return report

        if result.returncode != 0:
            stderr = result.stderr.strip()
            # Classify push failure
            if "rejected" in stderr and "non-fast-forward" in stderr:
                code = "push_rejected_non_fast_forward"
                msg_detail = "Push rejected: non-fast-forward update. Remote branch has diverged or contains commits not in local branch."
            elif "rejected" in stderr:
                code = "push_rejected"
                msg_detail = f"Push rejected: {stderr}"
            elif "Authentication failed" in stderr or "auth" in stderr.lower():
                code = "auth_failure"
                msg_detail = f"Authentication failure: {stderr}"
            elif "Could not resolve" in stderr or "Could not read from remote" in stderr:
                code = "network_failure"
                msg_detail = f"Network failure: {stderr}"
            else:
                code = "push_failed"
                msg_detail = f"Git push failed: {stderr or result.stdout.strip()}"

            report["diagnostics"].append({
                "severity": "blocker",
                "code": code,
                "message": msg_detail,
            })
            return report

        # ------------------------------------------------------------------
        # 8. Remote verification
        # ------------------------------------------------------------------
        try:
            result = subprocess.run(
                ["git", "ls-remote", remote, target_branch],
                capture_output=True, text=True, cwd=cwd, timeout=30,
            )
        except subprocess.TimeoutExpired:
            report["diagnostics"].append({
                "severity": "blocker",
                "code": "remote_verify_timeout",
                "message": f"Remote verification (ls-remote {remote} {target_branch}) timed out after 30s.",
            })
            report["mode"] = "blocked"
            return report

        if result.returncode != 0:
            report["diagnostics"].append({
                "severity": "blocker",
                "code": "remote_verify_failed",
                "message": f"Remote verification failed: {result.stderr.strip() or 'ls-remote returned non-zero'}",
            })
            report["mode"] = "blocked"
            return report

        remote_refs = result.stdout.strip().splitlines()
        remote_contains = any(commit_sha in line for line in remote_refs)

        if not remote_contains:
            report["diagnostics"].append({
                "severity": "blocker",
                "code": "remote_verification_failed",
                "message": f"Remote does not contain commit {commit_sha} on {target_branch}. The push may have been rejected or the remote has not been updated.",
            })
            report["mode"] = "blocked"
            return report

        # ------------------------------------------------------------------
        # 9. Re-check worktree cleanliness
        # ------------------------------------------------------------------
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=cwd, timeout=15,
        )
        post_porcelain = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if post_porcelain:
            # Allow .goal-spec/ paths (they are operational artifacts)
            owned_allowed: list[str] = []
            truly_dirty: list[str] = []
            for line in post_porcelain:
                filepath = line[3:].strip()
                normalized = filepath.replace("/", os.sep) if filepath else ""
                if ".goal-spec" in normalized.split(os.sep):
                    owned_allowed.append(normalized)
                else:
                    truly_dirty.append(normalized)

            if truly_dirty:
                report["diagnostics"].append({
                    "severity": "warning",
                    "code": "post_publish_dirty_worktree",
                    "message": f"Worktree has new dirty files after publish: {truly_dirty}. Expected clean after commit.",
                })

        report["mode"] = "published"
        report["diagnostics"].append({
            "severity": "info",
            "code": "published",
            "message": f"OpenSpec change '{change_name}' published to {remote}/{target_branch} at commit {commit_sha}.",
        })

    except FileNotFoundError:
        report["diagnostics"].append({
            "severity": "blocker",
            "code": "git_not_found",
            "message": "Git not found. Ensure git is installed and on PATH.",
        })
    except subprocess.CalledProcessError as err:
        report["diagnostics"].append({
            "severity": "blocker",
            "code": "git_command_failed",
            "message": f"Git command failed: {err}",
        })

    return report


def archive_preflight(change_name: str, base: Path, policy: Policy, *, require_decision_review: bool = False, skip_browser_layout: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {
        "changeName": change_name,
        "changeDir": str(base),
        "checks": {},
        "errors": [],
    }
    if not base.exists():
        report["errors"].append("change_directory_not_found")
        report["status"] = "fail"
        return report

    task_result = find_blocking_tasks(base / "tasks.md", policy.archive_backlog_markers)
    report["checks"]["tasks"] = task_result
    if policy.archive_require_no_unchecked_tasks and task_result["blocking"]:
        report["errors"].append("blocking_unchecked_tasks")

    manifest = validate_manifest(change_name, base)
    report["checks"]["sourceManifest"] = {"status": manifest.status, **manifest.data}
    if manifest.status != "ok":
        report["errors"].append("invalid_source_manifest")

    if policy.archive_require_explainer:
        explainer = validate_explainer(
            change_name,
            base,
            policy,
            require_decision_review=require_decision_review,
            skip_browser_layout=skip_browser_layout,
        )
        report["checks"]["explainer"] = {"status": explainer.status, **explainer.data}
        if explainer.status != "ok":
            report["errors"].append("invalid_change_explainer")

    report["status"] = "ok" if not report["errors"] else "fail"
    return report


def _project_root(raw: str | None) -> Path:
    return Path(raw or ".").resolve()


def _policy(project_root: Path, raw_policy: str | None) -> Policy:
    return load_policy(project_root, Path(raw_policy).resolve() if raw_policy else None)


def _dump(payload: dict[str, Any], json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            print(f"{key}={json.dumps(value, ensure_ascii=False)}")
        else:
            print(f"{key}={value}")


def cmd_propose(args: argparse.Namespace) -> int:
    try:
        root = _project_root(args.project_root)
        policy = _policy(root, args.policy)
        base = scaffold_change(policy, args.change_name, args.capability, force=args.force, no_manifest=args.no_manifest)
        payload = {
            "status": "ok",
            "changeName": args.change_name,
            "changeDir": str(base),
            "capability": args.capability or "change-capability",
            "manifest": "skipped" if args.no_manifest else str(base / "source-manifest.json"),
        }
    except Exception as err:  # noqa: BLE001
        payload = {"status": "fail", "error": str(err)}
        _dump(payload, args.json)
        return 1
    _dump(payload, args.json)
    return 0


def cmd_build_source_manifest(args: argparse.Namespace) -> int:
    try:
        root = _project_root(args.project_root)
        policy = _policy(root, args.policy)
        base = change_dir(policy, args.change_name)
        if not base.exists():
            raise FileNotFoundError(f"Change directory not found: {base}")
        output = write_manifest(args.change_name, base)
        payload = {"status": "ok", "output": str(output)}
    except Exception as err:  # noqa: BLE001
        payload = {"status": "fail", "error": str(err)}
        _dump(payload, args.json)
        return 1
    _dump(payload, args.json)
    return 0


def cmd_validate_source_manifest(args: argparse.Namespace) -> int:
    try:
        root = _project_root(args.project_root)
        policy = _policy(root, args.policy)
        base = change_dir(policy, args.change_name)
        result = validate_manifest(args.change_name, base)
        payload = {"status": result.status, **result.data}
    except Exception as err:  # noqa: BLE001
        payload = {"status": "fail", "error": str(err)}
        _dump(payload, args.json)
        return 1
    _dump(payload, args.json)
    return 0 if result.status == "ok" else 1


def cmd_validate_explainer(args: argparse.Namespace) -> int:
    try:
        root = _project_root(args.project_root)
        policy = _policy(root, args.policy)
        base = change_dir(policy, args.change_name)
        result = validate_explainer(
            args.change_name,
            base,
            policy,
            require_decision_review=args.require_decision_review,
            skip_browser_layout=args.skip_browser_layout,
        )
        payload = {"status": result.status, **result.data}
    except Exception as err:  # noqa: BLE001
        payload = {"status": "fail", "error": str(err)}
        _dump(payload, args.json)
        return 1
    _dump(payload, args.json)
    return 0 if result.status == "ok" else 1


def cmd_publish_closeout(args: argparse.Namespace) -> int:
    try:
        root = _project_root(args.project_root)
        policy = _policy(root, args.policy)
        base = change_dir(policy, args.change_name)
        payload = publish_closeout(
            args.change_name,
            base,
            policy,
            remote=args.remote,
            branch=args.branch,
            commit_message=args.commit_message,
            non_published=args.non_published,
            require_decision_review=args.require_decision_review,
            skip_browser_layout=args.skip_browser_layout,
        )
    except Exception as err:  # noqa: BLE001
        payload = {"status": "fail", "error": str(err)}
        _dump(payload, args.json)
        return 1
    _dump(payload, args.json)
    return 0 if payload.get("mode") in ("published", "no_changes", "non_published") else 1


def cmd_archive_preflight(args: argparse.Namespace) -> int:
    try:
        root = _project_root(args.project_root)
        policy = _policy(root, args.policy)
        base = change_dir(policy, args.change_name)
        payload = archive_preflight(
            args.change_name,
            base,
            policy,
            require_decision_review=args.require_decision_review,
            skip_browser_layout=args.skip_browser_layout,
        )
    except Exception as err:  # noqa: BLE001
        payload = {"status": "fail", "error": str(err)}
        _dump(payload, args.json)
        return 1
    _dump(payload, args.json)
    return 0 if payload.get("status") == "ok" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Self-contained OpenSpec helpers bundled with goal-spec")
    parser.add_argument("--json", action="store_true", help="emit JSON output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    common.add_argument("--project-root", default=".", help="target project root")
    common.add_argument("--policy", help="explicit .openspec-workflow.yaml/json policy file")

    propose = subparsers.add_parser("propose", parents=[common], help="scaffold an OpenSpec change")
    propose.add_argument("change_name")
    propose.add_argument("--capability", help="capability/spec name to scaffold", default=None)
    propose.add_argument("--force", action="store_true")
    propose.add_argument("--no-manifest", action="store_true")
    propose.set_defaults(func=cmd_propose)

    manifest = subparsers.add_parser("build-source-manifest", parents=[common], help="write source-manifest.json")
    manifest.add_argument("change_name")
    manifest.set_defaults(func=cmd_build_source_manifest)

    validate_manifest_parser = subparsers.add_parser("validate-source-manifest", parents=[common], help="validate source-manifest.json")
    validate_manifest_parser.add_argument("change_name")
    validate_manifest_parser.set_defaults(func=cmd_validate_source_manifest)

    validate = subparsers.add_parser("validate-explainer", parents=[common], help="validate change-explainer.html")
    validate.add_argument("change_name")
    validate.add_argument("--require-decision-review", action="store_true", help="require strict decision-review affordances")
    validate.add_argument("--skip-browser-layout", action="store_true", help="skip Chrome/Chromium layout probe")
    validate.set_defaults(func=cmd_validate_explainer)

    publish = subparsers.add_parser("publish-closeout", parents=[common], help="publish closeout: validate, stage, commit, push, verify")
    publish.add_argument("change_name")
    publish.add_argument("--remote", default="origin", help="Git remote name (default: origin)")
    publish.add_argument("--branch", help="Target branch (default: current branch)")
    publish.add_argument("--commit-message", help="Commit message (auto-generated if omitted)")
    publish.add_argument("--non-published", action="store_true", help="Skip commit/push, label result as non-published")
    publish.add_argument("--require-decision-review", action="store_true", help="require strict decision-review affordances")
    publish.add_argument("--skip-browser-layout", action="store_true", help="skip Chrome/Chromium layout probe")
    publish.set_defaults(func=cmd_publish_closeout)

    archive = subparsers.add_parser("archive-preflight", parents=[common], help="run archive readiness checks")
    archive.add_argument("change_name")
    archive.add_argument("--require-decision-review", action="store_true", help="require strict decision-review affordances")
    archive.add_argument("--skip-browser-layout", action="store_true", help="skip Chrome/Chromium layout probe")
    archive.set_defaults(func=cmd_archive_preflight)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
