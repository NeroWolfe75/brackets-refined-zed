# Brackets Refined — Codex Project Instructions

## Project

Brackets Refined is a dark theme extension for the Zed editor.

Repository: https://github.com/NeroWolfe75/brackets-refined-zed

The extension contains two theme variants:
- Brackets Refined — Classic
- Brackets Refined — Arctic

Both variants are distributed through one Zed extension.

## Theme requirements

- Preserve the existing visual identity of both themes.
- Never modify existing colors without explicit user approval.
- Use the established palette of each variant when adding syntax or UI keys.
- Do not copy colors from other themes.
- Keep Classic and Arctic visually distinct.
- Preserve the current Zed theme schema unless a migration is explicitly requested.
- Do not rename theme variants without approval.
- Do not remove existing theme keys without approval.
- Avoid duplicate JSON keys.

## Repository conventions

- Keep JSON formatting consistent with the existing files.
- Make minimal, targeted changes.
- Do not introduce unnecessary dependencies or build tools.
- Update README documentation when adding user-visible features.
- Do not change the extension version unless explicitly requested.

## Verification

- Do not run tests, validators, formatters, or other checks unless requested.
- Never claim that unperformed checks passed.
- Explain any compatibility concerns before proposing changes.

## Git workflow

- Inspect Git status before modifying files.
- Preserve unrelated working-tree changes.
- Do not create commits, tags, branches, or pull requests without explicit approval.
- Never push changes without explicit approval.
- Do not modify the official Zed extensions registry unless requested.

## Communication

- Communicate with the user in Russian.
- Keep explanations concise and technically precise.
- Before making changes, state which files will be modified.
- After making changes, summarize the modifications.
- Clearly distinguish completed work from proposed changes.
