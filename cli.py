#!/usr/bin/env python3
"""
Stack2LLM CLI v2.0 — Convert Substack to LLM training data + Voice Analysis

Usage:
    # Scrape & analyze a Substack
    python3 cli.py scrape mphinance.substack.com

    # Scrape + voice analysis report
    python3 cli.py scrape mphinance.substack.com --analyze

    # Process a ZIP export
    python3 cli.py process export.zip

    # Analyze an existing markdown file
    python3 cli.py analyze path/to/archive.md

    # Generate a "write as me" system prompt from analysis
    python3 cli.py voice-prompt path/to/archive.md --name "Michael"
"""

import argparse
import json
import os
import sys
from pathlib import Path

from processor import (
    scrape_substack_rss,
    process_substack_zip,
    analyze_voice,
    generate_voice_report,
)


def cmd_scrape(args):
    """Scrape a Substack RSS feed."""
    url = args.url
    output_dir = args.output or "output"
    combine = not args.separate

    print(f"🔍 Scraping {url}...")
    success, result = scrape_substack_rss(url, output_dir, combine=combine)

    if success:
        print(f"✅ Saved to {result}")

        if args.analyze:
            print("\n🎙️ Running voice analysis...")
            with open(result) as f:
                text = f.read()
            analysis = analyze_voice(text)
            name = url.replace("https://", "").replace("http://", "").split(".")[0]
            report = generate_voice_report(analysis, author_name=name)
            report_path = os.path.join(output_dir, f"{name}_voice_analysis.md")
            with open(report_path, 'w') as f:
                f.write(report)
            print(f"📊 Voice analysis saved to {report_path}")

            # Also save raw JSON
            json_path = os.path.join(output_dir, f"{name}_voice_data.json")
            with open(json_path, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"📦 Raw analysis data saved to {json_path}")
    else:
        print(f"❌ {result}")
        sys.exit(1)


def cmd_process(args):
    """Process a Substack ZIP export."""
    zip_path = args.zip_path
    output_dir = args.output or "output"
    combine = not args.separate

    print(f"📦 Processing {zip_path}...")
    success, result = process_substack_zip(zip_path, output_dir, combine=combine)

    if success:
        print(f"✅ Saved to {result}")

        if args.analyze:
            print("\n🎙️ Running voice analysis...")
            with open(result) as f:
                text = f.read()
            analysis = analyze_voice(text)
            report = generate_voice_report(analysis)
            report_path = os.path.join(output_dir, "voice_analysis.md")
            with open(report_path, 'w') as f:
                f.write(report)
            print(f"📊 Voice analysis saved to {report_path}")
    else:
        print(f"❌ {result}")
        sys.exit(1)


def cmd_analyze(args):
    """Analyze voice from a markdown file."""
    filepath = args.filepath
    name = args.name or Path(filepath).stem

    print(f"🎙️ Analyzing voice in {filepath}...")
    with open(filepath) as f:
        text = f.read()

    analysis = analyze_voice(text)
    report = generate_voice_report(analysis, author_name=name)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"📊 Report saved to {args.output}")
    else:
        print(report)

    # Save raw data
    json_path = args.output.replace('.md', '_data.json') if args.output else f"{name}_voice_data.json"
    with open(json_path, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"📦 Raw data saved to {json_path}")


def cmd_voice_prompt(args):
    """Generate a 'write as me' system prompt from voice analysis."""
    filepath = args.filepath
    name = args.name or "the author"

    print(f"🎯 Generating voice fingerprint for {name}...")
    with open(filepath) as f:
        text = f.read()

    analysis = analyze_voice(text)
    top_words = [w for w, _ in analysis['top_words'][:10]]
    tone = analysis['tone_markers']
    persp = analysis['perspective']

    prompt = f"""You are writing as {name}. Here is their voice fingerprint:

## Writing Style
- Average sentence length: {analysis['avg_sentence_length']} words
- Readability: {analysis['readability_label']} (Flesch-Kincaid Grade {analysis['flesch_kincaid_grade']})
- Perspective: primarily {persp['dominant'].replace('_', ' ')}
- Vocabulary richness: {'high' if analysis['vocabulary']['type_token_ratio'] > 0.5 else 'moderate' if analysis['vocabulary']['type_token_ratio'] > 0.35 else 'focused/repetitive'} (TTR: {analysis['vocabulary']['type_token_ratio']})

## Tone Markers
- Questions per 1K words: {analysis['questions_per_1000_words']} ({'interrogative' if analysis['questions_per_1000_words'] > 5 else 'moderate' if analysis['questions_per_1000_words'] > 2 else 'declarative'})
- Exclamations per 1K words: {analysis['exclamations_per_1000_words']} ({'emphatic' if analysis['exclamations_per_1000_words'] > 3 else 'moderate' if analysis['exclamations_per_1000_words'] > 1 else 'restrained'})
- Em dashes per 1K words: {analysis['em_dashes_per_1000_words']} ({'heavy parenthetical' if analysis['em_dashes_per_1000_words'] > 3 else 'moderate' if analysis['em_dashes_per_1000_words'] > 1 else 'minimal'})
- Code references: {'frequent' if tone['code_references'] > 10 else 'occasional' if tone['code_references'] > 3 else 'rare'}
- Bold emphasis: {'heavy' if tone['bold_emphasis'] > 15 else 'moderate' if tone['bold_emphasis'] > 5 else 'minimal'}

## Key Vocabulary
Frequently used words: {', '.join(top_words)}

## Rules
1. Match the sentence length and paragraph structure
2. Use the same perspective ({persp['dominant'].replace('_', ' ')})
3. Mirror the question frequency — {'ask lots of questions' if analysis['questions_per_1000_words'] > 5 else 'occasional rhetorical questions' if analysis['questions_per_1000_words'] > 2 else 'mostly declarative statements'}
4. {'Use em dashes liberally for asides and parenthetical thoughts' if analysis['em_dashes_per_1000_words'] > 3 else 'Use em dashes occasionally' if analysis['em_dashes_per_1000_words'] > 1 else 'Avoid em dashes'}
5. {'Use bold for emphasis on key terms' if tone['bold_emphasis'] > 10 else 'Use bold sparingly'}
6. {'Include code snippets when discussing technical topics' if tone['code_references'] > 5 else 'Keep code references minimal'}
7. {'Write with high energy — exclamation points welcome' if analysis['exclamations_per_1000_words'] > 3 else 'Write with measured energy'}
8. Maintain a {analysis['readability_label'].lower()} reading level

Write naturally in this voice. Don't try too hard — authenticity over performance.
"""

    if args.output:
        with open(args.output, 'w') as f:
            f.write(prompt)
        print(f"✅ Voice prompt saved to {args.output}")
    else:
        print(prompt)


def main():
    parser = argparse.ArgumentParser(
        prog="stack2llm",
        description="Convert Substack to LLM training data + Voice Analysis"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrape command
    p_scrape = subparsers.add_parser("scrape", help="Scrape a Substack RSS feed")
    p_scrape.add_argument("url", help="Substack URL (e.g., mphinance.substack.com)")
    p_scrape.add_argument("-o", "--output", help="Output directory (default: output)")
    p_scrape.add_argument("--separate", action="store_true", help="Save as separate files instead of combined")
    p_scrape.add_argument("--analyze", action="store_true", help="Run voice analysis after scraping")
    p_scrape.set_defaults(func=cmd_scrape)

    # Process command
    p_process = subparsers.add_parser("process", help="Process a Substack ZIP export")
    p_process.add_argument("zip_path", help="Path to Substack export ZIP")
    p_process.add_argument("-o", "--output", help="Output directory (default: output)")
    p_process.add_argument("--separate", action="store_true", help="Save as separate files")
    p_process.add_argument("--analyze", action="store_true", help="Run voice analysis after processing")
    p_process.set_defaults(func=cmd_process)

    # Analyze command
    p_analyze = subparsers.add_parser("analyze", help="Analyze voice from a markdown file")
    p_analyze.add_argument("filepath", help="Path to markdown file")
    p_analyze.add_argument("--name", help="Author name for report header")
    p_analyze.add_argument("-o", "--output", help="Output file (default: stdout)")
    p_analyze.set_defaults(func=cmd_analyze)

    # Voice prompt command
    p_voice = subparsers.add_parser("voice-prompt", help="Generate a 'write as me' prompt")
    p_voice.add_argument("filepath", help="Path to markdown archive")
    p_voice.add_argument("--name", help="Author name")
    p_voice.add_argument("-o", "--output", help="Output file (default: stdout)")
    p_voice.set_defaults(func=cmd_voice_prompt)

    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
