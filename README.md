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
install `pytest` and `pillow` and run:

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

### Writing in Obsidian

`content/posts/` can be opened as an Obsidian vault. The repository includes
plugins that insert Hugo shortcodes for images, spoilers, and YouTube videos,
and link to other posts. See [Obsidian Plugins](docs/obsidian-plugins.md).

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
Enter to add it later. PNG and JPEG covers are saved as `cover.webp` (see
[Optimize Images](#optimize-images)).

Each work is a page bundle under `content/estante/<year>/<month>/<slug>/`, the
month of its `startDate` (e.g. `content/estante/2026/09/o-segredo-de-widows-bay/`),
with a `cover.*` (or `image.*`) image (cropped to 9:16 automatically) and an `index.md` like:

```toml
+++
title = "O segredo de Widow's Bay"
kind = "series"        # series | movie | book | game | comic
status = "concluded"   # in-progress | concluded | abandoned
startDate = 2026-09-01
endDate = 2026-10-01   # optional
post = "/posts/2026/10/02/o-segredo-de-widows-bay"  # optional, concluded only
cover = "/posts/2026/10/02/o-segredo-de-widows-bay/widows-bay.webp"  # optional
+++
```

Instead of a `cover.*` or `image.*` file, `cover` can point at an image already in the
project, such as the post's own picture, so it isn't duplicated.

Works have no page of their own. In-progress works are listed first, then the
rest grouped by the month of their `endDate` (or `startDate`), newest first.
The shelf shows one year at a time: the current year first, with a link to the
previous year at the end of the page (`/estante/?year=2025`). A
missing `startDate`, an invalid
`kind`/`status`, or a `post` or `cover` path that doesn't exist fails the build.
A `post` or `cover` path into a draft post only warns: until the post is
published, the production shelf shows the work without its link and cover.

### Turning a shelf work into a post

To write about a work that is still in progress, run:

```sh
python3 scripts/shelf_item_to_post.py
```

Pick the work from the in-progress list, confirm the post title (Enter keeps
the work's), choose tags and a description as in `create_post.py`, and enter
the end date. The script creates a draft post with the work's cover as its
image, moving the file into the post bundle instead of copying it (a PNG or
JPEG cover is converted to WebP on the way), and marks
the work as `concluded` with `endDate`, `post`, and a `cover` path pointing at
that image. Write the post and set `draft = false` to publish it.

## Optimize Images

Post images are served as they are, so convert them to WebP before committing.
The script needs [Pillow](https://pillow.readthedocs.io/) (`pip install pillow`):

```sh
python3 scripts/convert_images.py content/posts/2026/10/25/my-post/
```

It accepts files or folders (scanned recursively) and converts every PNG and
JPEG it finds. Each image is encoded lossy at quality 90 with the slowest,
most thorough compression; PNGs are also tried lossless, keeping the smaller
result. Resolution, transparency, orientation, and color profile are kept.
Afterwards, references inside `content/` are updated: the bare file name in the
bundle's own Markdown (`images = [...]`, `{{< image src=... >}}`) and absolute
paths anywhere, such as a shelf work's `cover`. The original is then deleted.
An image that would get larger as WebP is left untouched.

Use `--dry-run` to only see the expected savings and `--keep-original` to keep
the source files.

Since every committed image stays in the Git history for good, a pre-commit
hook runs the same conversion on PNG/JPEG files staged under `content/`, staging
the WebP, the removed original, and the Markdown files whose references
changed. Images above 500 KB only get a warning. Enable it once per clone:

```sh
git config core.hooksPath .githooks
```

Use `git commit --no-verify` to commit an image as it is.

## Instagram Stories

### Creating the story image

Render a 1080×1920 story for a post (needs Pillow):

```sh
python3 scripts/create_story.py content/posts/2026/10/25/my-post/
```

The post's cover fills the screen, with the title and description over a dark
gradient at the bottom. The cover is the first of `images = [...]`, then the
first `{{< image >}}` in the body, then any image in the bundle (or a plain
accent-colored background). Without a `description`, the first paragraph is
used. A band at the bottom is left free for the link sticker.

The output goes to the git-ignored `stories/` folder: `stories/<slug>.png` and
`stories/<slug>.json` with the title, description, and post URL. Use `--font`
to pick another TTF/OTF font.

### Publishing it from an Android phone

`scripts/publish_story.py` sends the image to an Android phone over adb and
drives the Instagram app to post it as a story with a link sticker to the post
(the official API cannot add link stickers). It automates the app's UI, which
Instagram's terms don't allow, so use it sparingly.

One-time setup:

1. `brew install android-platform-tools` and `pip install uiautomator2`.
2. On the phone, enable Developer options › Wireless debugging, tap "Pair
   device with pairing code", and run `adb pair IP:PAIRING_PORT` with that code.
3. Keep Instagram logged in. The selectors expect the phone in Portuguese
   (English labels are tried as a fallback).

Then, with the IP:PORT shown on the Wireless debugging screen:

```sh
python3 scripts/publish_story.py stories/my-post.json --device 192.168.0.10:41234 --no-share
```

`--no-share` stops right before posting so you can review the story on the
phone; drop it to post. The script never posts when Instagram attached a
suggested song to the story, or while it asks for photo access: it stops and
tells you to fix it on the phone. The device can also come from `STORY_ADB_DEVICE`.
Every step saves a screenshot under `stories/debug/<slug>/`. When Instagram
changes its UI and a step fails, the error names the missing element: add a
matching selector to `SELECTORS` at the top of the script.

## AI Project Documentation

- [Copilot instructions](.github/copilot-instructions.md): repository-wide
  conventions and validation requirements for AI coding tools.
- [Architecture](.github/ARCHITECTURE.md): project structure, source-of-truth
  boundaries, build, and deployment rules, including AI-use requirements.
- [Content-authoring skill](.github/skills/content-authoring/SKILL.md): guidance
  for posts, page bundles, assets, and Bear imports.
- [Architecture-validation skill](.github/skills/architecture-validation/SKILL.md):
  validation steps for changes that affect project architecture.