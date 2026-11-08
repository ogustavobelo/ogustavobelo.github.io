const { Plugin } = require("obsidian");

const OPEN_TAG = '{{< admonition spoiler "🚨 Área com spoilers 🚨" false >}}';
const CLOSE_TAG = "{{< /admonition >}}";

module.exports = class HugoSpoilerShortcodePlugin extends Plugin {
  async onload() {
    this.addCommand({
      id: "wrap-spoiler",
      name: "Wrap selection in spoiler admonition",
      hotkeys: [{ modifiers: ["Mod", "Shift"], key: "p" }],
      editorCallback: (editor) => this.wrapSpoiler(editor),
    });
  }

  wrapSpoiler(editor) {
    const selection = editor.getSelection().replace(/^\n+|\n+$/g, "");

    if (selection === "") {
      // No selection: insert an empty block and leave the cursor inside it.
      const cursor = editor.getCursor();
      editor.replaceSelection(`${OPEN_TAG}\n\n\n${CLOSE_TAG}\n`);
      editor.setCursor({ line: cursor.line + 2, ch: 0 });
      return;
    }

    // Same layout used in existing posts: blank line after the opening tag,
    // closing tag right after the last line of content.
    editor.replaceSelection(`${OPEN_TAG}\n\n${selection}\n${CLOSE_TAG}`);
  }
};
