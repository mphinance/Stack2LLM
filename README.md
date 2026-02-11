# Stack2LLM 📖

**Live App:** [https://stack2llm.streamlit.app](https://stack2llm.streamlit.app)

Convert Substack posts into clean, LLM-optimized Markdown. Perfect for "Write as Me" training, NotebookLM, or custom RAG pipelines.

## 🚀 The Vision
Every Substack writer has a unique voice. This tool bridges the gap between your published archive and personal AI models. Whether you're using NotebookLM to brainstorm new ideas or training a custom LLM to mimic your style, **Substack Flow** ensures your data is clean, formatted, and ready to go.

## ✨ Features
- **Official Export Support**: Process your full Substack ZIP export in seconds.
- **Instant Scraper**: Paste any public Substack URL to pull the latest posts via RSS.
- **LLM-Ready Markdown**: Automatically strips HTML noise (buttons, scripts, SVGs) and converts images to searchable captions.
- **Voice Preservation**: Maintains your narrative structure better than flat CSV or messy PDF exports.

## 🛠️ How to Use
1. **Upload**: Drop your official Substack export ZIP.
2. **Scrape**: Or simply enter a URL (e.g., `vixqueen.substack.com`).
3. **Convert**: Download your clean `.md` files or a combined archive.

## 📦 Setup & Installation
```bash
git clone https://github.com/mph/substack-flow.git
cd substack-flow
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 🧠 Why Markdown?
NotebookLM and other LLMs perform best when they understand headers and context. Substack Flow prioritizes structural integrity over raw data, giving you the best results for personality-driven AI.

---
Built for writers. Optimized for the future.
