import os
import pandas as pd
import zipfile
import shutil
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import traceback
import feedparser
import requests

def clean_substack_html(html_content):
    """
    Cleans Substack-specific HTML noise and converts to clean Markdown.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove common Substack noise
    for tag in soup.find_all(['script', 'style', 'button', 'svg']):
        tag.decompose()
        
    for div in soup.find_all('div', class_=['button-wrapper', 'image-link-expand', 'pc-display-flex']):
        div.decompose()
        
    # Handle captioned images
    for figure in soup.find_all('figure'):
        caption = figure.find('figcaption')
        if caption:
            new_tag = soup.new_tag("p")
            new_tag.string = f"[Image Caption: {caption.get_text().strip()}]"
            figure.replace_with(new_tag)
        else:
            figure.decompose()

    # Convert to markdown
    markdown_text = md(str(soup), heading_style="ATX")
    
    # Clean up multiple newlines
    while "\n\n\n" in markdown_text:
        markdown_text = markdown_text.replace("\n\n\n", "\n\n")
        
    return markdown_text.strip()

def process_substack_zip(zip_path, output_dir, combine=True):
    """
    Processes a Substack export zip file.
    """
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
    """
    Scrapes a Substack RSS feed for public posts.
    """
    # Extract the substack name from URL for filename
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
            # Substack RSS usually puts full content in content[0].value
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
    # Test RSS
    success, result = scrape_substack_rss("mphinance.substack.com", "test_scrape")
    print(f"RSS Success: {success}, Result: {result}")
