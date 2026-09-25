# Commit Guidelines

Use small, contextual commits so that each change is easy to understand, review, revert, and release independently.

## Rules

- Separate changes by context. Do not combine layout changes, Hugo configuration, new posts, content edits, tests, and tooling in the same commit unless they are inseparable.
- Use [Conventional Commits](https://www.conventionalcommits.org/).
- Always write commit messages in English.
- Use the imperative mood in the subject and keep it concise.
- Keep the subject focused on what the commit does, not on the implementation process.

## Format

```text
<type>(<scope>): <description>
```

The scope is optional, but use it when it makes the context clearer. Common types for this project include:

- `feat`: adds a user-facing feature or a new post
- `fix`: corrects broken behavior or content
- `style`: changes visual presentation, CSS, or layout without changing behavior
- `config`: changes Hugo, theme, or project configuration
- `test`: adds or updates tests
- `docs`: adds or updates documentation
- `refactor`: restructures code without changing behavior
- `chore`: updates maintenance or development tooling

## Examples

```text
style(layout): refine post header spacing
config(hugo): enable related posts
feat(post): add notes on focused work
fix(content): correct broken image reference
test(import): cover posts with missing dates
docs(commits): document contextual commit rules
```

## Separating Work

When a task touches multiple contexts, split it into separate commits whenever possible. For example:

```text
style(layout): adjust article typography
config(hugo): update site pagination
feat(post): publish notes on reading
test(rendering): cover updated article layout
```

Before committing, review the staged diff and confirm that every file belongs to the commit's stated context.