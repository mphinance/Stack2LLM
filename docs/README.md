# Stack2LLM

> Convert your Substack archive into clean, LLM-ready Markdown — entirely client-side.

**Single HTML file. No backend. No API keys. No server.**

## Features

- **ZIP Upload** — Drop your Substack export ZIP and parse all posts client-side using JSZip
- **RSS Scrape** — Paste any `yourname.substack.com` URL, fetch the `/feed`, parse and convert
- **HTML → Markdown** — Strips nav/buttons/scripts/SVGs; converts headings, links, images, lists, tables, code blocks
- **AI Voice Analysis** — Sends a sample of your posts to Puter AI for a detailed writing style breakdown
- **Per-Post AI Summary** — One-click 2-sentence summary for any post, via Puter AI
- **Save to Puter Drive** — Sign in with Puter and save your full Markdown archive to the cloud
- **Download All as ZIP** — Export every post as individual `.md` files + a combined file, client-side

## Usage

Just open `index.html` in any modern browser. No install required.

## Tech Stack

| Layer | Library |
|---|---|
| AI + Cloud | [Puter.js](https://puter.com) |
| ZIP handling | JSZip (cdnjs) |
| Fonts | Syne + DM Mono (Google Fonts) |
| Everything else | Vanilla HTML/CSS/JS |

## Legacy

The original Python-based implementation (Flask + html2text) is preserved in [`legacy/`](./legacy/).
