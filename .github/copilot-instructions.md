# Copilot Instructions

These instructions apply to every task in this repository. Project documentation
must be written in English.

## Before Editing

- Read `.github/ARCHITECTURE.md` before changing project structure, content
  conventions, URLs, assets, build behavior, or deployment.
- Use `.github/skills/content-authoring/SKILL.md` when creating or editing posts
  or other editorial content.
- Use the existing source-of-truth boundaries. Do not edit generated output in
  `public/` or `resources/`.
- Prefer the smallest change that follows the repository's existing Hugo,
  template, asset, and content patterns.
- Ask the user when the expected URL, content model, asset location, language,
  or architectural behavior cannot be inferred from the repository.

## Architecture Changes

- Use `.github/skills/architecture-validation/SKILL.md` for any change that may
  affect the architecture.
- If the architecture changes, update `.github/ARCHITECTURE.md` in the same
  change. Do not leave implementation and architecture documentation out of
  sync.

## Validation

- Run `hugo --buildDrafts` after changes that affect rendering, templates,
  content, configuration, or assets.
- Run `python3 -m pytest -q` after changes that affect import or rendering
  contracts covered by the tests.
- Prefer the narrowest relevant check first, then report any unavailable or
  failing validation clearly.

## Commits

- Follow `.github/COMMIT_GUIDELINES.md`.
- Keep commits contextual and use Conventional Commits.
- Write every commit message in English.