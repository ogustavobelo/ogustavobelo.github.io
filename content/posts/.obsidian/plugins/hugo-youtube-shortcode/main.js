const { Plugin } = require("obsidian");

const VIDEO_ID = /^[A-Za-z0-9_-]{11}$/;
const YOUTUBE_HOSTS = ["youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"];

// Accepts "90", "90s", "1m30s", "1h2m3s" (the formats YouTube uses in t=/start=).
function parseSeconds(value) {
  if (!value) return 0;
  if (/^\d+$/.test(value)) return Number(value);
  const match = value.match(/^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$/);
  if (!match) return 0;
  const [, h = 0, m = 0, s = 0] = match;
  return Number(h) * 3600 + Number(m) * 60 + Number(s);
}

function parseYouTubeUrl(text) {
  let url;
  try {
    url = new URL(text);
  } catch {
    return null;
  }

  let id = null;
  if (url.hostname === "youtu.be") {
    id = url.pathname.slice(1);
  } else if (YOUTUBE_HOSTS.includes(url.hostname)) {
    if (url.pathname === "/watch") {
      id = url.searchParams.get("v");
    } else {
      const match = url.pathname.match(/^\/(?:shorts|embed|live)\/([^/]+)/);
      if (match) id = match[1];
    }
  }
  if (!id || !VIDEO_ID.test(id)) return null;

  const start = parseSeconds(url.searchParams.get("t") || url.searchParams.get("start"));
  return { id, start };
}

function shortcodeFor({ id, start }) {
  // Positional form matches existing posts; named params are needed for start.
  if (start > 0) return `{{< youtube id="${id}" start="${start}" >}}`;
  return `{{< youtube ${id} >}}`;
}

module.exports = class HugoYouTubeShortcodePlugin extends Plugin {
  async onload() {
    this.registerEvent(
      this.app.workspace.on("editor-paste", (evt, editor) => this.handlePaste(evt, editor))
    );
  }

  handlePaste(evt, editor) {
    if (evt.defaultPrevented || !evt.clipboardData) return;

    const video = parseYouTubeUrl(evt.clipboardData.getData("text/plain").trim());
    if (!video) return;

    // Only convert when pasting on an empty line: a URL pasted mid-sentence or
    // over a selection (Obsidian turns that into a [text](url) link) stays a link.
    if (editor.somethingSelected()) return;
    if (editor.getLine(editor.getCursor().line).trim() !== "") return;

    evt.preventDefault();
    editor.replaceSelection(shortcodeFor(video));
  }
};
