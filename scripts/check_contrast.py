"""Read-only contrast audit for Brackets Refined (Python 3.11+).

Exit codes: 0 = no critical failures, 1 = contrast failures, 2 = input errors.
WARN is a project policy for secondary elements, not a WCAG exemption.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


THEME_PATH = Path(__file__).resolve().parent.parent / "themes" / "brackets-refined.json"
TEXT_THRESHOLD = 4.5
DECORATIVE_THRESHOLD = 3.0
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?")


@dataclass(frozen=True)
class Color:
    red: float
    green: float
    blue: float
    alpha: float = 1.0

    def over(self, background: Color) -> Color:
        """Composite in sRGB onto an already resolved, opaque background."""
        if background.alpha != 1.0:
            raise ValueError("Compositing requires an opaque background")
        return Color(
            self.red * self.alpha + background.red * (1.0 - self.alpha),
            self.green * self.alpha + background.green * (1.0 - self.alpha),
            self.blue * self.alpha + background.blue * (1.0 - self.alpha),
        )

    def luminance(self) -> float:
        """WCAG 2.1 relative luminance, using the corrected sRGB breakpoint."""
        def linear(channel: float) -> float:
            if channel <= 0.04045:
                return channel / 12.92
            return ((channel + 0.055) / 1.055) ** 2.4

        return (
            0.2126 * linear(self.red)
            + 0.7152 * linear(self.green)
            + 0.0722 * linear(self.blue)
        )


def parse_color(value: object, label: str) -> Color:
    if not isinstance(value, str) or HEX_COLOR.fullmatch(value) is None:
        raise ValueError(f"{label}: expected #RRGGBB or #RRGGBBAA, got {value!r}")
    return Color(
        int(value[1:3], 16) / 255,
        int(value[3:5], 16) / 255,
        int(value[5:7], 16) / 255,
        int(value[7:9], 16) / 255 if len(value) == 9 else 1.0,
    )


def contrast_ratio(foreground: Color, background: Color) -> float:
    first = foreground.over(background).luminance()
    second = background.luminance()
    return (max(first, second) + 0.05) / (min(first, second) + 0.05)


@dataclass(frozen=True)
class Check:
    foreground: str
    background: str
    threshold: float = TEXT_THRESHOLD
    advisory: bool = False


# Backgrounds are resolved from their parent before any foreground is applied.
BACKGROUND_PARENTS = {
    "surface.background": "background",
    "elevated_surface.background": "background",
    "panel.background": "background",
    "toolbar.background": "background",
    "title_bar.background": "background",
    "status_bar.background": "background",
    "tab_bar.background": "background",
    "tab.active_background": "tab_bar.background",
    "tab.inactive_background": "tab_bar.background",
    "editor.background": "background",
    "editor.active_line.background": "editor.background",
    "editor.gutter.background": "editor.background",
    "terminal.background": "background",
    "terminal.ansi.background": "terminal.background",
}


def background_color(style: dict, key: str) -> Color:
    color = parse_color(style.get(key), key)
    if key == "background":
        if color.alpha != 1.0:
            raise ValueError("background must be opaque; the desktop backdrop is unknown")
        return color
    return color.over(background_color(style, BACKGROUND_PARENTS[key]))


def checks_for(style: dict) -> Iterator[Check]:
    ui_backgrounds = (
        "background",
        "surface.background",
        "elevated_surface.background",
        "panel.background",
        "toolbar.background",
        "title_bar.background",
        "status_bar.background",
        "tab.active_background",
        "tab.inactive_background",
    )
    for background in ui_backgrounds:
        yield Check("text", background)
        yield Check("text.muted", background, advisory=True)

    for background in ("editor.background", "editor.active_line.background"):
        yield Check("editor.foreground", background)
        # Comments and documentation are readable content and remain critical.
        syntax = style.get("syntax")
        if not isinstance(syntax, dict) or not syntax:
            raise ValueError("syntax must be a non-empty object")
        for key, token in sorted(syntax.items()):
            if not isinstance(token, dict) or "color" not in token:
                raise ValueError(f"syntax.{key}: an explicit color is required")
            yield Check(f"syntax.{key}", background)

    for key in (
        "editor.line_number",
        "editor.active_line_number",
        "editor.hover_line_number",
    ):
        yield Check(key, "editor.gutter.background", advisory=True)
    yield Check(
        "editor.active_line_number", "editor.active_line.background", advisory=True
    )
    yield Check("editor.code_lens.foreground", "editor.background", advisory=True)
    for key in (
        "editor.invisible",
        "editor.indent_guide",
        "editor.indent_guide_active",
        "editor.wrap_guide",
        "editor.active_wrap_guide",
    ):
        yield Check(key, "editor.background", DECORATIVE_THRESHOLD, advisory=True)

    for key in ("terminal.foreground", "terminal.bright_foreground", "terminal.dim_foreground"):
        yield Check(key, "terminal.background", advisory=key == "terminal.dim_foreground")

    # Require the full normal, bright and dim ANSI palette; never silently skip it.
    for prefix in ("", "bright_", "dim_"):
        for color in ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"):
            key = f"terminal.ansi.{prefix}{color}"
            advisory = prefix == "dim_" or color == "black"
            for background in ("terminal.background", "terminal.ansi.background"):
                yield Check(key, background, advisory=advisory)


def foreground_color(style: dict, key: str) -> Color:
    if key.startswith("syntax."):
        token = key.removeprefix("syntax.")
        return parse_color(style["syntax"][token]["color"], key)
    return parse_color(style.get(key), key)


def audit_variant(variant: object, index: int) -> tuple[Counter, bool]:
    counts: Counter = Counter()
    name = variant.get("name") if isinstance(variant, dict) else None
    print(f"\n=== {name if isinstance(name, str) else f'Variant {index}'} ===")
    try:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("variant name must be a non-empty string")
        style = variant.get("style")
        if not isinstance(style, dict):
            raise ValueError("style must be an object")
        checks = list(checks_for(style))
    except ValueError as error:
        counts["FAIL"] += 1
        print(f"FAIL | input | contrast=n/a | threshold=n/a | {error}")
        print_summary(counts, measured=0, errors=1)
        return counts, True

    errors = 0
    measured = 0
    skipped = 0
    terminal_pairs: set[tuple[str, Color, float, bool]] = set()
    problems: dict[tuple[Color, Color], list[tuple[Check, str, float]]] = {}
    for check in checks:
        pair = f"{check.foreground} / {check.background}"
        policy = "advisory" if check.advisory else "critical"
        try:
            foreground = foreground_color(style, check.foreground)
            background = background_color(style, check.background)
            if check.foreground.startswith("terminal."):
                terminal_pair = (
                    check.foreground, background, check.threshold, check.advisory
                )
                if terminal_pair in terminal_pairs:
                    skipped += 1
                    continue
                terminal_pairs.add(terminal_pair)
            ratio = contrast_ratio(foreground, background)
        except ValueError as error:
            errors += 1
            counts["FAIL"] += 1
            print(
                f"FAIL | {pair} | contrast=n/a | threshold={check.threshold:.1f}:1"
                f" | input error: {error}"
            )
            continue
        # Compare the full precision result, not the displayed rounded value.
        status = "PASS" if ratio >= check.threshold else ("WARN" if check.advisory else "FAIL")
        counts[status] += 1
        measured += 1
        if status != "PASS":
            colors = (foreground.over(background), background)
            problems.setdefault(colors, []).append((check, status, ratio))
        print(
            f"{status:4} | {pair} | contrast={ratio:.3f}:1"
            f" | threshold={check.threshold:.1f}:1 | {policy}"
        )
    print_summary(counts, measured, errors)
    print(f"Equivalent terminal-background checks omitted: {skipped}")
    print_unique_problems(problems)
    return counts, errors > 0


def print_unique_problems(
    problems: dict[tuple[Color, Color], list[tuple[Check, str, float]]],
) -> None:
    """Group exact effective colors without rounding them for comparison."""
    def describe(color: Color) -> str:
        # Fractional channels are retained for alpha-composited colors.
        channels = (color.red, color.green, color.blue)
        return "rgb(" + ", ".join(f"{channel * 255:.3f}" for channel in channels) + ")"

    print(f"Unique problematic color pairs: {len(problems)} (input errors excluded)")
    for (foreground, background), entries in problems.items():
        statuses = "/".join(sorted({status for _, status, _ in entries}))
        thresholds = ", ".join(
            f"{threshold:.1f}:1" for threshold in sorted({c.threshold for c, _, _ in entries})
        )
        print(
            f"  {statuses} | {describe(foreground)} / {describe(background)}"
            f" | contrast={entries[0][2]:.3f}:1 | thresholds={thresholds}"
            f" | affected checks={len(entries)}"
        )
        for check, status, _ in entries:
            print(
                f"    {check.foreground} / {check.background}"
                f" ({status}, threshold={check.threshold:.1f}:1)"
            )


def print_summary(counts: Counter, measured: int, errors: int) -> None:
    print(
        f"Summary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}"
        f" | measured pairs={measured} | input errors={errors}"
    )


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def main() -> int:
    if sys.version_info < (3, 11):
        print("FAIL | Python 3.11 or newer is required", file=sys.stderr)
        return 2
    try:
        document = json.loads(
            THEME_PATH.read_text(encoding="utf-8-sig"),
            object_pairs_hook=unique_object,
        )
        variants = document.get("themes") if isinstance(document, dict) else None
        if not isinstance(variants, list) or not variants:
            raise ValueError("themes must be a non-empty array")
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print(f"FAIL | Cannot read theme data from {THEME_PATH}: {error}", file=sys.stderr)
        return 2

    print(f"Contrast audit: {THEME_PATH}")
    print("Text: 4.5:1; decorative guides: advisory 3.0:1.")
    print("WARN is advisory policy, not a declaration of WCAG compliance.")
    print("Alpha uses sRGB compositing; root background must be opaque.")
    any_failure = False
    any_error = False
    for index, variant in enumerate(variants, start=1):
        counts, has_error = audit_variant(variant, index)
        any_failure = any_failure or counts["FAIL"] > 0
        any_error = any_error or has_error
    return 2 if any_error else (1 if any_failure else 0)


if __name__ == "__main__":
    sys.exit(main())
