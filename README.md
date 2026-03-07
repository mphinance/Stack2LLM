# Stack2LLM 📖 v2.0

Convert Substack posts into clean, LLM-optimized Markdown **+ Voice Analysis**.

**Live Streamlit App:** [stack2llm.streamlit.app](https://stack2llm.streamlit.app) (basic version)

## 🚀 What's New in v2.0

- **CLI-first** — no browser needed, works in pipelines and scripts
- **Voice Analysis Engine** — word frequency, Flesch-Kincaid readability, vocabulary richness, tone markers, perspective analysis
- **Voice Fingerprint** — auto-generates a "write as me" system prompt for any LLM
- **Ghost Alpha Integration** — feed into mphinance VOICE.md for Sam's writing calibration

## ✨ Features

- **Official Export Support**: Process your full Substack ZIP export in seconds
- **Instant Scraper**: Paste any public Substack URL to pull the latest posts via RSS
- **LLM-Ready Markdown**: Strips HTML noise and converts images to searchable captions
- **Voice Analysis**: Sentence structure, readability, em-dash frequency, vocabulary richness, tone profiling
- **Voice Prompt Generator**: Creates an LLM system prompt that captures the author's writing fingerprint

## 🛠️ CLI Usage

```bash
# Install
pip install -r requirements.txt

# Scrape a Substack + run voice analysis
python3 cli.py scrape mphinance.substack.com --analyze

# Process a ZIP export
python3 cli.py process export.zip --analyze

# Analyze an existing markdown file
python3 cli.py analyze archive.md --name "Author Name"

# Generate a "write as me" system prompt
python3 cli.py voice-prompt archive.md --name "Michael" -o voice_prompt.md
```

## 📊 Voice Analysis Output

Running `--analyze` produces a full voice fingerprint:

| Metric | Example |
|--------|---------|
| Avg Sentence Length | 13.4 words |
| Flesch-Kincaid Grade | 8.0 |
| Em dashes per 1K words | 10.0 |
| Bold emphasis count | 484 |
| Type-Token Ratio | 0.227 |
| Dominant perspective | First person |

Plus top words, tone markers, and a summary like:
> 📖 Medium sentence length — balanced, readable prose
> — Heavy em-dash user — parenthetical thinker, aside-driven
> 💻 Technical writer — embeds code in narrative

## 🌐 Streamlit App

The original Streamlit app (`app.py`) still works for browser-based usage:

```bash
streamlit run app.py
```

## 🧠 Why Voice Analysis?

NotebookLM and other LLMs perform best when they understand your voice. The voice fingerprint captures:

- How long your sentences are
- Your favorite punctuation habits (em dashes, anyone?)
- Whether you bold everything or let the words speak
- Your vocabulary diversity
- Whether you write to yourself (first person) or to the reader (second person)

This feeds directly into "write as me" prompts that actually work.

---

Built for writers. Analyzed for AI. Optimized for the future.

*Part of the [mphinance](https://mphinance.com) ecosystem.*
