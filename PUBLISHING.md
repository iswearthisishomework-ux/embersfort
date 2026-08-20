# Publishing This Repository Online

This tree is already ready to commit to a normal Git host. The original fort is the repository root; generated crawler helpers are additive.

## GitHub repository

1. Create an empty GitHub repository named `embersfort` (or any name you prefer).
2. Upload/commit the contents of this directory to the default branch.
3. Markdown-relative links such as the fort's `## Thresholds` links will work directly in GitHub's file renderer.

## GitHub Pages crawler view

The repository includes a static `docs/` site that uses ordinary `<a href>` links and does not require JavaScript for navigation.

- Easiest manual option: in repository **Settings → Pages**, publish from the default branch's `/docs` folder.
- Or use the included `.github/workflows/pages.yml` workflow and configure Pages to deploy with GitHub Actions.

Once Pages is live, give another browsing agent the site's root URL ending in `/docs/` (or the Pages root if `/docs` is configured as the source). It can then traverse `index.html`, directory pages, individual file pages, and each page's explicit **Crawlable Thresholds** links.

## Local Git

This package also ships with a Git bundle next to the upload ZIP. A Git bundle can be cloned without preserving a `.git/` directory inside the upload archive.
