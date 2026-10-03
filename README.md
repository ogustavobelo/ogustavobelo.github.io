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

Hugo prints the local URL when the server starts.

### Personal settings

Values that identify the blog owner are not committed, so a fork starts clean
and can set its own. If a value is missing, the related feature is simply not
rendered.

| Setting | Purpose | Environment variable | GitHub Actions variable |
|---|---|---|---|
| `social.email` | E-mail linked in the contact note at the end of each post | `HUGO_PARAMS_SOCIAL_EMAIL` | `BLOG_EMAIL` |
| `analytics.goatcounter.code` | GoatCounter site code (`xxx` in `xxx.goatcounter.com`) | `HUGO_PARAMS_ANALYTICS_GOATCOUNTER_CODE` | `GOATCOUNTER_CODE` |

**Locally**, copy the example file and fill in your values. Hugo merges it with
`hugo.toml` on every `hugo server` and `hugo` run:

```sh
cp config/_default/params.toml.example config/_default/params.toml
```

`config/_default/params.toml` is gitignored. GoatCounter is only loaded in
production builds, so `hugo server` never counts visits.

**In the deploy**, create the GitHub Actions variables under
**Settings → Secrets and variables → Actions → Variables**; the deploy workflow
passes them to the build as environment variables. Environment variables always
take precedence over the local file.

To run the automated tests,
install `pytest` and run:

```sh
python3 -m pytest -q
```

## Create a Post

Run the post creation script from the repository root:

```sh
python3 scripts/create_post.py
```

Enter a title, then pick from the existing tags (ordered by how often each is
used across the blog) with the arrow keys, space to toggle, and enter to
confirm. Afterwards you can optionally type new, comma-separated tags to add
to the selection. In a non-interactive terminal, the script falls back to a
numbered list where you type the numbers you want (e.g. `1,3,5`). The script
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

## Add a Work to the Shelf

The shelf at `/estante/` lists series, movies, books, games, and comics. Run the shelf
script from the repository root:

```sh
python3 scripts/create_shelf_item.py
```

Enter a title, pick the kind and status with the arrow keys and enter (a
numbered list in a non-interactive terminal), then the start date (defaults to
today). Finished works also ask for an end date, and concluded ones for an
optional post path. Finally, drag a cover image into the terminal, or press
Enter to add it later.

Each work is a page bundle under `content/estante/<slug>/` with a `cover.*`
image (cropped to 9:16 automatically) and an `index.md` like:

```toml
+++
title = "O segredo de Widow's Bay"
kind = "series"        # series | movie | book | game | comic
status = "concluded"   # in-progress | concluded | abandoned
startDate = 2026-09-01
endDate = 2026-10-01   # optional
post = "/posts/2026/10/02/o-segredo-de-widows-bay"  # optional, concluded only
+++
```

Works have no page of their own. In-progress works are listed first, then the
rest grouped by the month of their `endDate` (or `startDate`), newest first. A
missing `startDate`, an invalid
`kind`/`status` or a `post` path that doesn't exist fails the build.

## AI Project Documentation

- [Copilot instructions](.github/copilot-instructions.md): repository-wide
  conventions and validation requirements for AI coding tools.
- [Architecture](.github/ARCHITECTURE.md): project structure, source-of-truth
  boundaries, build, and deployment rules, including AI-use requirements.
- [Content-authoring skill](.github/skills/content-authoring/SKILL.md): guidance
  for posts, page bundles, assets, and Bear imports.
- [Architecture-validation skill](.github/skills/architecture-validation/SKILL.md):
  validation steps for changes that affect project architecture.