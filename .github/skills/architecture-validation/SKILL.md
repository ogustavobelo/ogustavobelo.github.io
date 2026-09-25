---
name: architecture-validation
description: 'Validate architectural changes in this Hugo project. Use when a change affects the content model, URL structure, build or deployment, source-of-truth boundaries, assets, integrations, or other foundational project rules.'
user-invocable: true
---

# Architecture Validation

Use this skill whenever a proposed change may alter how the application is
structured, built, published, or maintained.

## Core Rule

`.github/ARCHITECTURE.md` is the canonical record of the project's
architecture. If the implementation changes the architecture, the
implementation and `ARCHITECTURE.md` must be updated in the same change.

A validation cannot be considered complete while the code and the architecture
document describe different contracts.

## Architectural Change Signals

Treat a change as architectural when it affects any of the following:

- the content model, front matter, page bundles, or URL structure;
- the boundary between `content/`, `layouts/`, `assets/`, `static/`, and
  generated output;
- Hugo configuration, the build command, the Hugo version, or deployment;
- image storage or processing;
- external services, APIs, databases, authentication, or client-side state;
- a foundational convention that future contributors or AI agents must follow.

Routine editorial changes and isolated visual adjustments are not architectural
unless they change one of these contracts.

## Validation Procedure

1. Read `.github/ARCHITECTURE.md` before modifying an architectural boundary.
2. Identify which rule, source of truth, or contract the change affects.
3. Implement the smallest change that preserves the documented boundaries.
4. If the architecture changed, update `.github/ARCHITECTURE.md` immediately in
   the same change. Keep the documentation in English and describe the new
   contract, source of truth, and validation requirement.
5. Check all references in the architecture document against the repository.
6. Run the check closest to the risk: `hugo --buildDrafts` for rendering and
   `python3 -m pytest -q` for import or rendering contracts covered by tests.
7. Report whether the architecture document was updated. If it was not updated,
   explain why the change was not architectural.

## Completion Criteria

The validation passes only when:

- the implementation follows the current architecture document;
- any changed architectural rule is reflected in `.github/ARCHITECTURE.md`;
- the documentation and implementation use the same paths, commands, and
  conventions; and
- the relevant build or test checks pass, or an unavailable check is reported.

Do not silently introduce a new architectural convention. Ask the user when
the intended URL, content model, asset boundary, integration, or publication
behavior cannot be inferred from the repository and its documentation.