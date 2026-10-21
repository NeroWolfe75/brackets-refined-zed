# Changelog

All notable changes to this project will be documented in this file.

This changelog follows the Keep a Changelog format.

## [0.1.2] - 2026-10-21

### Added

- A dependency-free Python 3.11+ contrast audit for both theme variants, with alpha compositing, per-pair results, variant summaries, and nonzero exit codes for critical failures or input errors.
- **Brackets Refined - Arctic** as a second theme variant, with a darker background and a cool color palette.
- New syntax keys for both Classic and Arctic, covering function and method definitions and calls, additional variable, constant, and type categories, documentation, strings, characters, and configuration files.

### Changed

- Improved Classic comment and documentation readability with neutral gray `#8C8C8C`, meeting 4.5:1 on both editor and active-line backgrounds.
- Improved contrast audit reporting by eliminating duplicate terminal checks on equivalent backgrounds and summarizing unique problematic color pairs while preserving detailed syntax results.
- Classic and Arctic are now bundled in one Brackets Refined extension.
- Renamed the original **Brackets Refined** theme to **Brackets Refined - Classic**, preserving its palette except for the comment and documentation adjustment above. Existing users may need to select the renamed theme again in Zed's Theme Selector after updating.

## [0.1.1] - 2026-10-07

### Added

- Explicit version control colors for added, deleted, modified, renamed, conflicted, and ignored items.
- Word-level addition and deletion highlights, and colors for both sides of conflict markers.
- Italic `predictive` syntax highlighting.
- Syntax highlighting for `punctuation.list_marker`, `punctuation.markup`, and `punctuation.special`.
- Syntax highlighting for `selector` and `selector.pseudo`.
