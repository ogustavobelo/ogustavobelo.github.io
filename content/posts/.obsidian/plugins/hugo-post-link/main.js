const { Plugin, FuzzySuggestModal } = require("obsidian");

// The vault root is content/posts, and posts are page bundles
// (YYYY/MM/DD/slug/index.md) without custom url/slug, so the published path
// is /posts/ + the bundle folder.
const URL_PREFIX = "/posts/";

// Posts use TOML front matter (+++), which Obsidian's metadataCache doesn't
// parse, so pull the few fields we need straight from the file.
function frontMatterValue(frontMatter, key) {
  const match = frontMatter.match(new RegExp(`^${key}\\s*=\\s*(?:"([^"]*)"|'([^']*)'|(\\S+))`, "m"));
  if (!match) return null;
  return match[1] ?? match[2] ?? match[3];
}

async function loadPosts(vault, currentFile) {
  const files = vault
    .getMarkdownFiles()
    .filter((f) => f.name === "index.md" && f.parent && f !== currentFile);

  const posts = [];
  for (const file of files) {
    // Posts imported from Bear use CRLF line endings.
    const content = (await vault.cachedRead(file)).replace(/\r\n/g, "\n");
    const match = content.match(/^\+\+\+\n([\s\S]*?)\n\+\+\+/);
    if (!match) continue;
    const frontMatter = match[1];
    // Drafts aren't published, so a link to one would 404.
    if (frontMatterValue(frontMatter, "draft") === "true") continue;
    posts.push({
      title: frontMatterValue(frontMatter, "title") || file.parent.name,
      date: (frontMatterValue(frontMatter, "date") || "").slice(0, 10),
      path: `${URL_PREFIX}${file.parent.path.toLowerCase()}/`,
    });
  }
  return posts.sort((a, b) => b.date.localeCompare(a.date));
}

class PostSuggestModal extends FuzzySuggestModal {
  constructor(app, posts, onChoose) {
    super(app);
    this.posts = posts;
    this.onChoose = onChoose;
    this.setPlaceholder("Buscar postagem…");
  }

  getItems() {
    return this.posts;
  }

  getItemText(post) {
    return `${post.title} (${post.date})`;
  }

  onChooseItem(post) {
    this.onChoose(post);
  }
}

module.exports = class HugoPostLinkPlugin extends Plugin {
  async onload() {
    this.addCommand({
      id: "link-to-post",
      name: "Link selection to a blog post",
      hotkeys: [{ modifiers: ["Mod", "Shift"], key: "k" }],
      editorCallback: (editor, view) => this.linkToPost(editor, view),
    });
  }

  async linkToPost(editor, view) {
    // Capture the selection before the modal steals focus.
    const from = editor.getCursor("from");
    const to = editor.getCursor("to");
    const selection = editor.getSelection();

    const posts = await loadPosts(this.app.vault, view.file);
    new PostSuggestModal(this.app, posts, (post) => {
      const text = selection || post.title;
      editor.replaceRange(`[${text}](${post.path})`, from, to);
    }).open();
  }
};
