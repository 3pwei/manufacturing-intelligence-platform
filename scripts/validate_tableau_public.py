#!/usr/bin/env python3
"""Smoke-test the published PR #13 Tableau Public dashboards.

This check intentionally validates rendering and publication health. Workbook
semantics (calculations, LODs, actions and Apply to Worksheets scope) are
validated from the packaged TWBX by pytest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright

ERROR_MARKERS = (
    "unable to complete action",
    "unexpected error",
    "sheet unavailable",
    "could not load the visualization",
    "dashboard references sheet",
    "contains errors",
)
RENDER_SELECTORS = (
    "canvas",
    "iframe",
    "svg",
    ".tabCanvas",
    "[class*='tableau']",
)


def _url_with_parameters(url: str, parameters: dict[str, str]) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.setdefault(":showVizHome", "no")
    query.setdefault(":showShareOptions", "false")
    for name, value in parameters.items():
        query[f"Parameters.{name}"] = value
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _render_count(page: Page) -> int:
    return sum(page.locator(selector).count() for selector in RENDER_SELECTORS)


def _visit(
    page: Page, *, name: str, url: str, output_dir: Path, timeout_ms: int
) -> dict:
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text)
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: page_errors.append(str(error)))

    response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(15_000)
    body_text = page.locator("body").inner_text(timeout=timeout_ms)
    normalized = body_text.lower()
    detected_errors = [marker for marker in ERROR_MARKERS if marker in normalized]
    render_count = _render_count(page)

    screenshot = output_dir / f"{_safe_name(name)}.png"
    page.screenshot(path=str(screenshot), full_page=True)
    screenshot_sha256 = hashlib.sha256(screenshot.read_bytes()).hexdigest()
    result = {
        "name": name,
        "url": url,
        "http_status": response.status if response else None,
        "title": page.title(),
        "render_elements": render_count,
        "detected_errors": detected_errors,
        "console_errors": console_errors[-20:],
        "page_errors": page_errors[-20:],
        "screenshot": str(screenshot),
        "screenshot_sha256": screenshot_sha256,
    }
    result["passed"] = bool(
        response
        and response.ok
        and render_count > 0
        and not detected_errors
        and not page_errors
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executive-url", required=True)
    parser.add_argument("--quality-url", required=True)
    parser.add_argument("--rca-url", required=True)
    parser.add_argument("--output-dir", default="artifacts/tableau-public")
    parser.add_argument("--timeout-ms", type=int, default=90_000)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    scenarios = (
        (
            "Executive Overview - FPY Overall",
            args.executive_url,
            {"Metric Selector": "FPY", "Benchmark Selector": "Overall"},
        ),
        (
            "Executive Overview - DPPM Product",
            args.executive_url,
            {"Metric Selector": "DPPM", "Benchmark Selector": "Product"},
        ),
        ("Manufacturing Quality", args.quality_url, {}),
        ("Root Cause Analysis", args.rca_url, {}),
    )

    results: list[dict] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1100})
        for name, base_url, parameters in scenarios:
            page = context.new_page()
            try:
                results.append(
                    _visit(
                        page,
                        name=name,
                        url=_url_with_parameters(base_url, parameters),
                        output_dir=output_dir,
                        timeout_ms=args.timeout_ms,
                    )
                )
            except PlaywrightError as error:  # Preserve evidence from every scenario.
                results.append(
                    {
                        "name": name,
                        "url": base_url,
                        "passed": False,
                        "error": str(error),
                    }
                )
            finally:
                page.close()
        browser.close()

    executive_hashes = {
        row.get("screenshot_sha256")
        for row in results
        if row["name"].startswith("Executive Overview") and row.get("passed")
    }
    parameter_scenarios_differ = len(executive_hashes) == 2
    report = {
        "passed": all(row.get("passed", False) for row in results)
        and parameter_scenarios_differ,
        "parameter_scenarios_differ": parameter_scenarios_differ,
        "results": results,
    }
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
