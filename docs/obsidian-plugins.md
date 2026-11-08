# Obsidian Plugins

`content/posts/` doubles as an [Obsidian](https://obsidian.md/) vault for
writing posts. The repository ships a few small plugins that make the editor
produce Hugo-ready Markdown, so a post written in Obsidian needs no manual
shortcode editing before publishing.

| Plugin | Trigger | Result |
|---|---|---|
| [Hugo Image Shortcode](#hugo-image-shortcode) | Drop or paste an image | `{{< image >}}` shortcode, file saved in the post bundle |
| [Hugo Spoiler Shortcode](#hugo-spoiler-shortcode) | `Cmd+Shift+P` | Selection wrapped in a spoiler admonition |
| [Hugo YouTube Shortcode](#hugo-youtube-shortcode) | Paste a YouTube URL on an empty line | `{{< youtube >}}` shortcode |
| [Hugo Post Link](#hugo-post-link) | `Cmd+Shift+K` | Selection linked to another post |

## Setup

1. Open `content/posts/` as a vault in Obsidian (**Open folder as vault**).
2. Go to **Settings → Community plugins**, turn off Restricted mode, and make
   sure the four plugins above are enabled. `community-plugins.json` already
   lists them, so they are usually enabled on first open.
3. After pulling plugin changes, reload Obsidian (command palette → **Reload app
   without saving**).

Hotkeys are plugin defaults; change them under **Settings → Hotkeys** if they
clash with another binding.

## Hugo Image Shortcode

`plugins/hugo-image-shortcode/`

When an image is dropped or pasted into a note, the plugin saves it next to the
note's `index.md` (the post's page bundle) instead of Obsidian's default
attachment folder, and inserts a shortcode instead of a wikilink:

```
{{< image src="my-photo.png" alt="my photo" class="image-frame" >}}
```

- The `alt` text comes from the file name, with `-` and `_` turned into spaces.
- Pasted images without a name (screenshots) are saved as
  `pasted-image-YYYYMMDDHHMMSS.<ext>`.
- An existing file is never overwritten; a `-1`, `-2`, … suffix is added.

PNG and JPEG files are converted to WebP by the pre-commit hook (see
[Optimize Images](../README.md#optimize-images)), which also updates the
shortcode's `src`.

## Hugo Spoiler Shortcode

`plugins/hugo-spoiler-shortcode/`

Command: **Wrap selection in spoiler admonition** (`Cmd+Shift+P`).

With text selected, wraps it in the spoiler block used across the blog:

```
{{< admonition spoiler "🚨 Área com spoilers 🚨" false >}}

selected text
{{< /admonition >}}
```

With nothing selected, inserts an empty block and puts the cursor inside it.

## Hugo YouTube Shortcode

`plugins/hugo-youtube-shortcode/`

Pasting a YouTube URL on an empty line replaces it with Hugo's built-in
shortcode:

```
https://www.youtube.com/watch?v=9stm18DFD08  →  {{< youtube 9stm18DFD08 >}}
```

- Recognized URLs: `youtube.com/watch?v=`, `youtu.be/`, `/shorts/`, `/embed/`,
  and `/live/`, on `www.`, `m.`, and `music.` hosts. Extra query parameters
  such as `si=` are dropped.
- A start time (`t=90`, `t=1m30s`, or `start=`) is kept, using the named-param
  form: `{{< youtube id="9stm18DFD08" start="90" >}}`.
- The URL is pasted as-is when the line already has text or when text is
  selected, so links in a sentence and Obsidian's paste-over-selection
  `[text](url)` still work. Channel and playlist URLs are also left alone.

## Hugo Post Link

`plugins/hugo-post-link/`

Command: **Link selection to a blog post** (`Cmd+Shift+K`).

Opens a fuzzy search over the blog's posts, newest first, showing each title
and date. Picking one turns the selection into a link to that post:

```
[primeira temporada](/posts/2025/03/04/lost-1a-temporada/)
```

- With nothing selected, the post's title is used as the link text.
- The link uses the post's real path, `/posts/YYYY/MM/DD/slug/`, derived from
  the bundle folder. It works for every post, unlike the short
  `https://www.gustavobelo.com/<slug>/` aliases that only legacy Bear posts
  have.
- Drafts (`draft = true`) are left out, since the link would 404 until the post
  is published. The note being edited is also left out.
- Titles and dates are read straight from each post's TOML front matter
  (`+++`), which Obsidian does not parse itself.

## Repository Layout

The plugins live in `content/posts/.obsidian/plugins/<id>/`, each with a
`manifest.json` and a plain-JavaScript `main.js` (no build step). Only these
files are tracked:

- `content/posts/.obsidian/community-plugins.json`
- `content/posts/.obsidian/plugins/hugo-*/`

Everything else in `.obsidian/` (workspace and graph state, third-party
plugins) is per-machine and gitignored. Hugo skips the folder via
`ignoreFiles` in `hugo.toml`, so none of it is published.

To add a plugin:

1. Create `content/posts/.obsidian/plugins/<id>/` with `manifest.json` and
   `main.js`.
2. Add `<id>` to `community-plugins.json`.
3. Allow the folder in `.gitignore` with a
   `!content/posts/.obsidian/plugins/<id>/` line.
4. Document it here.
