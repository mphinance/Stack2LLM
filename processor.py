"""
Stack2LLM Processor v2.0 — Voice Analysis + LLM-Ready Export

Converts Substack content to clean Markdown AND analyzes writing voice:
- Word frequency analysis
- Sentence structure fingerprint
- Readability metrics (Flesch-Kincaid, avg sentence length)
- Vocabulary richness (TTR, hapax legomena)
- Tone markers (questions, exclamations, em dashes, parentheticals)
- Gemini-powered voice fingerprint generation

Original processor preserved with new analysis layer on top.
"""

import os
import re
import json
import math
import pandas as pd
import zipfile
import shutil
from collections import Counter
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import feedparser
import requests
import traceback


# ============================================================
# CORE: HTML → Markdown Conversion (original, improved)
# ============================================================

def clean_substack_html(html_content):
    """Cleans Substack-specific HTML noise and converts to clean Markdown."""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove common Substack noise
    for tag in soup.find_all(['script', 'style', 'button', 'svg', 'iframe']):
        tag.decompose()

    for div in soup.find_all('div', class_=['button-wrapper', 'image-link-expand',
                                            'pc-display-flex', 'subscription-widget-wrap',
                                            'captioned-button-wrap', 'pencraft']):
        div.decompose()

    # Remove share/subscribe buttons
    for a in soup.find_all('a', class_=['button', 'subscribe-widget']):
        a.decompose()

    # Handle captioned images
    for figure in soup.find_all('figure'):
        caption = figure.find('figcaption')
        if caption:
            new_tag = soup.new_tag("p")
            new_tag.string = f"[Image: {caption.get_text().strip()}]"
            figure.replace_with(new_tag)
        else:
            figure.decompose()

    # Convert to markdown
    markdown_text = md(str(soup), heading_style="ATX", strip=['img'])

    # Clean up multiple newlines
    while "\n\n\n" in markdown_text:
        markdown_text = markdown_text.replace("\n\n\n", "\n\n")

    return markdown_text.strip()


# ============================================================
# VOICE ANALYSIS ENGINE
# ============================================================

def analyze_voice(text: str) -> dict:
    """
    Analyze writing voice from markdown text.
    Returns a comprehensive fingerprint of writing style.
    """
    # Clean markdown formatting for analysis
    clean = re.sub(r'[#*_`\[\]()]', '', text)
    clean = re.sub(r'!\[.*?\]\(.*?\)', '', clean)
    clean = re.sub(r'\[.*?\]\(.*?\)', '', clean)
    clean = re.sub(r'---+', '', clean)
    clean = re.sub(r'\n{2,}', '\n', clean).strip()

    # Sentences
    sentences = [s.strip() for s in re.split(r'[.!?]+', clean) if s.strip() and len(s.strip()) > 5]
    words = clean.split()
    word_count = len(words)

    if word_count == 0 or len(sentences) == 0:
        return {"error": "Not enough content to analyze"}

    # Word frequency (excluding stop words)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'is', 'it', 'that', 'this', 'was', 'are', 'be',
                  'have', 'has', 'had', 'not', 'you', 'we', 'they', 'he', 'she',
                  'from', 'as', 'can', 'will', 'do', 'if', 'my', 'your', 'our',
                  'i', 'me', 'them', 'its', 'what', 'when', 'how', 'so', 'up',
                  'about', 'just', 'than', 'more', 'been', 'would', 'could',
                  'into', 'some', 'then', 'no', 'out', 'all', 'were', 'their',
                  'there', 'which', 'one', 'don', 't', 's', 're', 've', 'll'}

    clean_words = [w.lower().strip('.,!?;:()[]"\'—–-') for w in words]
    content_words = [w for w in clean_words if w and w not in stop_words and len(w) > 2]
    word_freq = Counter(content_words)

    # Sentence lengths
    sent_lengths = [len(s.split()) for s in sentences]
    avg_sent_len = sum(sent_lengths) / len(sent_lengths)

    # Syllable count (approximation)
    def count_syllables(word):
        word = word.lower()
        count = 0
        vowels = 'aeiouy'
        if word[0] in vowels:
            count += 1
        for i in range(1, len(word)):
            if word[i] in vowels and word[i-1] not in vowels:
                count += 1
        if word.endswith('e'):
            count -= 1
        if count == 0:
            count = 1
        return count

    total_syllables = sum(count_syllables(w) for w in clean_words if w)

    # Flesch-Kincaid Grade Level
    fk_grade = 0.39 * (word_count / len(sentences)) + 11.8 * (total_syllables / word_count) - 15.59

    # Flesch Reading Ease
    fk_ease = 206.835 - 1.015 * (word_count / len(sentences)) - 84.6 * (total_syllables / word_count)

    # Type-Token Ratio (vocabulary richness)
    unique_words = len(set(clean_words))
    ttr = unique_words / word_count if word_count else 0

    # Hapax legomena (words used only once)
    hapax = sum(1 for count in word_freq.values() if count == 1)
    hapax_ratio = hapax / len(word_freq) if word_freq else 0

    # Tone markers
    question_count = text.count('?')
    exclamation_count = text.count('!')
    em_dash_count = text.count('—') + text.count('--')
    ellipsis_count = text.count('...')
    parenthetical_count = text.count('(')
    bold_count = len(re.findall(r'\*\*.*?\*\*', text))
    italic_count = len(re.findall(r'(?<!\*)\*(?!\*).*?(?<!\*)\*(?!\*)', text))
    code_count = len(re.findall(r'`[^`]+`', text))

    # Paragraph analysis
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and not p.strip().startswith('#')]
    avg_para_len = sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0

    # First-person vs third-person
    first_person = sum(1 for w in clean_words if w in ('i', 'me', 'my', 'mine', 'we', 'our', 'us'))
    second_person = sum(1 for w in clean_words if w in ('you', 'your', 'yours'))
    third_person = sum(1 for w in clean_words if w in ('he', 'she', 'they', 'them', 'his', 'her', 'their'))

    return {
        "word_count": word_count,
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "avg_sentence_length": round(avg_sent_len, 1),
        "avg_paragraph_length": round(avg_para_len, 1),
        "sentence_length_range": {"min": min(sent_lengths), "max": max(sent_lengths)},
        "flesch_kincaid_grade": round(fk_grade, 1),
        "flesch_reading_ease": round(fk_ease, 1),
        "readability_label": (
            "Very Easy" if fk_ease >= 90 else
            "Easy" if fk_ease >= 70 else
            "Standard" if fk_ease >= 50 else
            "Difficult" if fk_ease >= 30 else
            "Very Difficult"
        ),
        "vocabulary": {
            "unique_words": unique_words,
            "type_token_ratio": round(ttr, 3),
            "hapax_legomena": hapax,
            "hapax_ratio": round(hapax_ratio, 3),
        },
        "top_words": word_freq.most_common(25),
        "tone_markers": {
            "questions": question_count,
            "exclamations": exclamation_count,
            "em_dashes": em_dash_count,
            "ellipses": ellipsis_count,
            "parentheticals": parenthetical_count,
            "bold_emphasis": bold_count,
            "italic_emphasis": italic_count,
            "code_references": code_count,
        },
        "perspective": {
            "first_person": first_person,
            "second_person": second_person,
            "third_person": third_person,
            "dominant": (
                "first_person" if first_person > second_person and first_person > third_person else
                "second_person" if second_person > third_person else
                "third_person"
            ),
        },
        "questions_per_1000_words": round(question_count / (word_count / 1000), 1) if word_count > 0 else 0,
        "exclamations_per_1000_words": round(exclamation_count / (word_count / 1000), 1) if word_count > 0 else 0,
        "em_dashes_per_1000_words": round(em_dash_count / (word_count / 1000), 1) if word_count > 0 else 0,
    }


def generate_voice_report(analysis: dict, author_name: str = "Author") -> str:
    """Generate a human-readable voice analysis report."""
    if "error" in analysis:
        return f"❌ {analysis['error']}"

    top_words_str = ", ".join(f"**{w}** ({c})" for w, c in analysis['top_words'][:15])
    tone = analysis['tone_markers']
    persp = analysis['perspective']

    report = f"""# 🎙️ Voice Analysis: {author_name}

## 📊 Overview
| Metric | Value |
|--------|-------|
| Total Words | {analysis['word_count']:,} |
| Sentences | {analysis['sentence_count']:,} |
| Paragraphs | {analysis['paragraph_count']:,} |
| Avg Sentence Length | {analysis['avg_sentence_length']} words |
| Avg Paragraph Length | {analysis['avg_paragraph_length']} words |
| Sentence Range | {analysis['sentence_length_range']['min']}–{analysis['sentence_length_range']['max']} words |

## 📖 Readability
| Metric | Score |
|--------|-------|
| Flesch-Kincaid Grade | {analysis['flesch_kincaid_grade']} |
| Flesch Reading Ease | {analysis['flesch_reading_ease']} |
| Readability | **{analysis['readability_label']}** |

## 🧠 Vocabulary
| Metric | Value |
|--------|-------|
| Unique Words | {analysis['vocabulary']['unique_words']:,} |
| Type-Token Ratio | {analysis['vocabulary']['type_token_ratio']} |
| Hapax Legomena | {analysis['vocabulary']['hapax_legomena']:,} ({analysis['vocabulary']['hapax_ratio']:.1%} unique) |

## 🔑 Top Words
{top_words_str}

## 🎭 Tone Markers (per 1,000 words)
| Marker | Count | Per 1K |
|--------|-------|--------|
| Questions (?) | {tone['questions']} | {analysis['questions_per_1000_words']} |
| Exclamations (!) | {tone['exclamations']} | {analysis['exclamations_per_1000_words']} |
| Em dashes (—) | {tone['em_dashes']} | {analysis['em_dashes_per_1000_words']} |
| Ellipses (...) | {tone['ellipses']} | — |
| Parentheticals | {tone['parentheticals']} | — |
| Bold emphasis | {tone['bold_emphasis']} | — |
| Code references | {tone['code_references']} | — |

## 👤 Perspective
- First person (I/we): **{persp['first_person']}**
- Second person (you): **{persp['second_person']}**
- Third person (they): **{persp['third_person']}**
- Dominant: **{persp['dominant'].replace('_', ' ').title()}**

## 🎯 Voice Fingerprint Summary
"""
    # Generate summary observations
    observations = []
    if analysis['avg_sentence_length'] < 12:
        observations.append("✍️ Short, punchy sentences — conversational, high-energy style")
    elif analysis['avg_sentence_length'] > 20:
        observations.append("📝 Long, flowing sentences — literary or academic tone")
    else:
        observations.append("📖 Medium sentence length — balanced, readable prose")

    if analysis['questions_per_1000_words'] > 5:
        observations.append("❓ Heavy use of questions — engages reader, Socratic style")
    if analysis['exclamations_per_1000_words'] > 3:
        observations.append("❗ Frequent exclamations — energetic, emphatic voice")
    if analysis['em_dashes_per_1000_words'] > 3:
        observations.append("— Heavy em-dash user — parenthetical thinker, aside-driven")
    if tone['code_references'] > 5:
        observations.append("💻 Technical writer — embeds code in narrative")
    if analysis['vocabulary']['type_token_ratio'] > 0.6:
        observations.append("🧠 Rich vocabulary — diverse word choice, avoids repetition")
    elif analysis['vocabulary']['type_token_ratio'] < 0.4:
        observations.append("🔁 Focused vocabulary — hammers key terms, builds familiarity")
    if persp['dominant'] == 'first_person':
        observations.append("👤 First-person dominant — personal, confessional, authentic")
    elif persp['dominant'] == 'second_person':
        observations.append("👉 Second-person dominant — instructional, 'you should' energy")

    report += "\n".join(f"- {obs}" for obs in observations)
    return report


# ============================================================
# SUBSTACK PROCESSING (original functions, improved)
# ============================================================

def process_substack_zip(zip_path, output_dir, combine=True):
    """Processes a Substack export zip file."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    temp_dir = os.path.join(output_dir, "_temp_extract")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        root = temp_dir
        contents = os.listdir(temp_dir)
        if len(contents) == 1 and os.path.isdir(os.path.join(temp_dir, contents[0])):
            root = os.path.join(temp_dir, contents[0])

        posts_csv_path = os.path.join(root, "posts.csv")
        posts_dir = os.path.join(root, "posts")

        if not os.path.exists(posts_csv_path) or not os.path.exists(posts_dir):
            return False, "Could not find posts.csv or posts folder in the ZIP."

        df = pd.read_csv(posts_csv_path)
        published_posts = df[df['is_published'] == True].sort_values(by='post_date', ascending=False)

        processed_files = []
        combined_content = []

        for _, row in published_posts.iterrows():
            post_id = str(row['post_id'])
            title = str(row['title'])
            date = str(row['post_date'])

            html_file = os.path.join(posts_dir, f"{post_id}.html")
            if os.path.exists(html_file):
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                clean_md = clean_substack_html(content)
                header = f"# {title}\nDate: {date}\n\n"
                full_post = header + clean_md + "\n\n---\n\n"

                if combine:
                    combined_content.append(full_post)
                else:
                    file_name = f"{post_id}.md"
                    safe_file_name = "".join([c for c in file_name if c.isalnum() or c in "._- "]).strip()
                    output_path = os.path.join(output_dir, safe_file_name)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(full_post)
                    processed_files.append(output_path)

        if combine:
            combined_file_path = os.path.join(output_dir, "substack_archive.md")
            with open(combined_file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(combined_content))
            return True, combined_file_path
        else:
            zip_output = os.path.join(output_dir, "substack_markdown_files.zip")
            with zipfile.ZipFile(zip_output, 'w') as zip_out:
                for file_path in processed_files:
                    zip_out.write(file_path, os.path.basename(file_path))
            return True, zip_output

    except Exception as e:
        return False, f"Error processing ZIP: {str(e)}"
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def scrape_substack_rss(substack_url, output_dir, combine=True):
    """Scrapes a Substack RSS feed for public posts."""
    original_url = substack_url
    substack_name = substack_url.replace("https://", "").replace("http://", "").split("/")[0].split(".")[0]

    if not substack_url.endswith("/feed"):
        substack_url = substack_url.rstrip("/") + "/feed"

    if not substack_url.startswith("http"):
        substack_url = "https://" + substack_url

    try:
        feed = feedparser.parse(substack_url)
        if hasattr(feed, 'status') and feed.status != 200:
            return False, f"Could not access RSS feed. Status code: {feed.status}"

        if not feed.entries:
            return False, "No posts found in the RSS feed."

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        combined_content = []
        processed_files = []

        for entry in feed.entries:
            title = entry.title
            date = entry.published if hasattr(entry, 'published') else "Unknown Date"
            content = entry.content[0].value if hasattr(entry, 'content') else entry.summary

            clean_md = clean_substack_html(content)
            header = f"# {title}\nDate: {date}\nURL: {entry.link}\n\n"
            full_post = header + clean_md + "\n\n---\n\n"

            if combine:
                combined_content.append(full_post)
            else:
                safe_title = "".join([c for c in title if c.isalnum() or c in "._- "]).strip()
                file_name = f"{safe_title}.md"
                output_path = os.path.join(output_dir, file_name)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(full_post)
                processed_files.append(output_path)

        if combine:
            combined_file_path = os.path.join(output_dir, f"{substack_name}.md")
            with open(combined_file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(combined_content))
            return True, combined_file_path
        else:
            zip_output = os.path.join(output_dir, f"{substack_name}_markdown.zip")
            with zipfile.ZipFile(zip_output, 'w') as zip_out:
                for file_path in processed_files:
                    zip_out.write(file_path, os.path.basename(file_path))
            return True, zip_output

    except Exception as e:
        return False, f"Error scraping RSS: {str(e)}"


if __name__ == "__main__":
    # Quick test
    success, result = scrape_substack_rss("mphinance.substack.com", "test_scrape")
    print(f"RSS Success: {success}, Result: {result}")
