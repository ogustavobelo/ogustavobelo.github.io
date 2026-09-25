# Notas de uma mente inquieta

A personal blog about technology, productivity, and curiosity, built with Hugo
and published as a static site on GitHub Pages.

Read the live blog at [ogustavobelo.github.io](https://ogustavobelo.github.io/).

## Theme

The site is based on the [Hugo KeepIt theme](https://github.com/Fastbyte01/KeepIt).
Its templates and assets are integrated into this repository and customized to
fit the project's individual visual and functional needs.

## Run Locally

Install Hugo Extended **0.166.0** (the version used by the deployment workflow)
and Python 3. From the repository root, start the local server with drafts
enabled:

```sh
hugo server --buildDrafts
```

Hugo prints the local URL when the server starts. To run the automated tests,
install `pytest` and run:

```sh
python3 -m pytest -q
```

## Create a Post

Run the post creation script from the repository root:

```sh
python3 scripts/create_post.py
```

Enter a title and optional comma-separated tags when prompted. The script
creates a dated page bundle under `content/posts/YYYY/MM/DD/`, generates a
URL-friendly slug, and marks the new post as a draft. Review the generated
`index.md` and set `draft = false` when it is ready to publish.

## Import a Post from Bear

Export the Bear blog data as a CSV and place it at
`bear-data/Bear Blog Settings.csv`, or pass a different path with `--csv`. Find
the post's `uid` in the CSV, then run:

```sh
python3 scripts/import_bear_post.py <uid>
```

For example:

```sh
python3 scripts/import_bear_post.py abc123
```

The importer creates a Hugo page bundle under `content/posts/`, converts Bear
metadata and `tab:` links, and downloads referenced remote images into the
bundle. Preview the generated content without writing files with `--dry-run`;
use `--force` only when you intend to overwrite an existing post. Review the
imported post, especially its content, images, dates, tags, and draft state,
before publishing.

## AI Project Documentation

- [Copilot instructions](.github/copilot-instructions.md): repository-wide
  conventions and validation requirements for AI coding tools.
- [Architecture](.github/ARCHITECTURE.md): project structure, source-of-truth
  boundaries, build, and deployment rules, including AI-use requirements.
- [Content-authoring skill](.github/skills/content-authoring/SKILL.md): guidance
  for posts, page bundles, assets, and Bear imports.
- [Architecture-validation skill](.github/skills/architecture-validation/SKILL.md):
  validation steps for changes that affect project architecture.