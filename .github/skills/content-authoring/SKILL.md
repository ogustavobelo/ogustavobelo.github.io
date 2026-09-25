---
name: content-authoring
description: 'Create and edit Hugo posts and editorial content in this repository. Use for new posts, front matter, page bundles, local images, shortcodes, imported Bear content, slugs, tags, and content rendering validation.'
user-invocable: true
---

# Content Authoring

Use this skill when creating or editing posts, pages, metadata, or post-local
assets in this Hugo project.

## Content Rules

- Keep editorial source files under `content/`; never edit generated files in
  `public/` or `resources/`.
- Posts belong in a page bundle following
  `content/posts/YYYY/MM/DD/slug/index.md`.
- Preserve the existing TOML front matter style and fields. Posts normally use
  `title`, `date`, `draft`, and `tags`; preserve source identifiers such as
  `bear_uid` when editing imported posts.
- Keep the language of the editorial content consistent with the surrounding
  content. The repository documentation must remain in English, but do not
  translate a Portuguese post unless the user explicitly asks for it.
- Treat published URLs as a public contract. Do not change a post's date or
  slug casually; ask when the intended URL is unclear.
- Use lowercase, URL-safe slugs consistent with existing post directories.

## Images and Media

- Store post-specific images inside the post's page bundle.
- Prefer the existing `image` shortcode for images in post content:
  `{{< image src="image.webp" alt="Description" >}}`.
- Use `class="image-frame"` only when the framed presentation is intentional.
- Use descriptive, accessible `alt` text. Do not use a remote image URL when a
  local page-bundle asset is available.
- Do not copy generated files from `public/` into `content/`; use the original
  source asset and let Hugo process it.

## Creating a Post

1. Confirm the title, publication date, draft state, tags, and desired slug.
2. Create `content/posts/YYYY/MM/DD/slug/index.md` as a page bundle.
3. Add TOML front matter delimited by `+++` and preserve the project's field
   naming and date format.
4. Place post-local images beside `index.md` and reference them with the
   existing shortcode.
5. Write the editorial content without changing unrelated posts or generated
   output.
6. Build the site with `hugo --buildDrafts` and inspect the resulting page when
   the post includes images, shortcodes, links, or unusual Markdown.

## Imported Bear Content

When the source is Bear Blog data, prefer the existing importer in
`scripts/import_bear_post.py` instead of manually reproducing its conversion
rules. The importer handles front matter, slug normalization, tab links, image
downloads, and page-bundle creation.

Run the focused importer tests with:

```text
python3 -m pytest -q tests/test_import_bear_post.py
```

Review imported content before publishing. Confirm that remote image URLs were
downloaded into the page bundle and that links, tags, dates, and draft state are
correct.

## Editing Existing Content

- Preserve the author's voice, formatting, links, and metadata unless the user
  asks for editorial changes.
- Avoid unrelated spelling, formatting, or restructuring changes in the same
  edit.
- Keep image filenames stable when possible because content and tests may refer
  to them.
- Check the rendered page when changing Markdown, shortcodes, front matter,
  images, or links.

## Completion Checklist

- [ ] The source file is under the correct `content/` path.
- [ ] The page bundle and slug preserve the intended public URL.
- [ ] Front matter is valid and uses the expected fields.
- [ ] Local images exist beside the post and use the existing shortcode.
- [ ] No generated output was edited.
- [ ] The relevant Hugo build or importer tests pass.