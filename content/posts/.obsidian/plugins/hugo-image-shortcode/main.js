const { Plugin } = require("obsidian");

const IMAGE_CLASS = "image-frame";

const MIME_EXTENSIONS = {
  "image/png": "png",
  "image/jpeg": "jpg",
  "image/gif": "gif",
  "image/webp": "webp",
  "image/svg+xml": "svg",
  "image/bmp": "bmp",
};

function altFromFilename(filename) {
  const base = filename.replace(/\.[^.]+$/, "");
  return base.replace(/[-_]+/g, " ").trim();
}

function timestamp() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}${pad(
    d.getHours()
  )}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

function nameForFile(file) {
  if (file.name && file.name.trim() !== "") return file.name;
  const ext = MIME_EXTENSIONS[file.type] || "png";
  return `pasted-image-${timestamp()}.${ext}`;
}

// Resolve the destination ourselves instead of relying on
// FileManager.getAvailablePathForAttachment, which follows the vault-wide
// "default location for new attachments" setting and was placing pasted
// images at the vault root instead of next to the note (unlike drop, which
// happened to match this note's folder). Hugo page bundles need the image
// next to index.md regardless of that global setting.
async function availablePathInFolder(vault, folderPath, filename) {
  const dot = filename.lastIndexOf(".");
  const base = dot > 0 ? filename.slice(0, dot) : filename;
  const ext = dot > 0 ? filename.slice(dot) : "";
  let candidate = filename;
  let counter = 1;
  while (vault.getAbstractFileByPath(folderPath ? `${folderPath}/${candidate}` : candidate)) {
    candidate = `${base}-${counter}${ext}`;
    counter += 1;
  }
  return folderPath ? `${folderPath}/${candidate}` : candidate;
}

// clipboardData.files is unreliable for pasted (vs. dropped) images in
// Electron/Chromium: a screenshot or an image copied from another app often
// only shows up in clipboardData.items, not in .files.
function imagesFromClipboard(clipboardData) {
  if (!clipboardData) return [];
  const fromFiles = clipboardData.files ? Array.from(clipboardData.files) : [];
  const fromItems = clipboardData.items
    ? Array.from(clipboardData.items)
        .filter((item) => item.kind === "file")
        .map((item) => item.getAsFile())
        .filter(Boolean)
    : [];
  const seen = new Set();
  const combined = [];
  for (const file of [...fromFiles, ...fromItems]) {
    const key = `${file.name}|${file.size}|${file.type}`;
    if (seen.has(key)) continue;
    seen.add(key);
    combined.push(file);
  }
  return combined;
}

module.exports = class HugoImageShortcodePlugin extends Plugin {
  async onload() {
    this.registerEvent(
      this.app.workspace.on("editor-drop", (evt, editor, info) =>
        this.handleFiles(evt, evt.dataTransfer && evt.dataTransfer.files, editor, info)
      )
    );
    this.registerEvent(
      this.app.workspace.on("editor-paste", (evt, editor, info) =>
        this.handleFiles(evt, imagesFromClipboard(evt.clipboardData), editor, info)
      )
    );
  }

  handleFiles(evt, fileList, editor, info) {
    if (!fileList || fileList.length === 0) return;
    const images = Array.from(fileList).filter((f) => f.type.startsWith("image/"));
    if (images.length === 0) return;

    evt.preventDefault();

    const activeFile = info.file;
    if (!activeFile) return;

    const folderPath = activeFile.parent ? activeFile.parent.path : "";

    (async () => {
      const shortcodes = [];
      for (const file of images) {
        const buffer = await file.arrayBuffer();
        const destPath = await availablePathInFolder(
          this.app.vault,
          folderPath,
          nameForFile(file)
        );
        const created = await this.app.vault.createBinary(destPath, buffer);
        const alt = altFromFilename(created.name);
        shortcodes.push(
          `{{< image src="${created.name}" alt="${alt}" class="${IMAGE_CLASS}" >}}`
        );
      }
      editor.replaceSelection(shortcodes.join("\n") + "\n");
    })();
  }
};
