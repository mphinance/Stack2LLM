import streamlit as st
import os
import tempfile
from processor import process_substack_zip, scrape_substack_rss

st.set_page_config(
    page_title="Substack to NotebookLM",
    page_icon="📖",
    layout="centered"
)

# Custom Styling - Substack Orange Theme
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #FFF5E6 0%, #FFE8CC 100%) !important;
        color: #000000 !important;
    }
    .stApp {
        background: linear-gradient(135deg, #FFF5E6 0%, #FFE8CC 100%) !important;
    }
    .stMarkdown, .stMarkdown p, .stMarkdown div, .stCaption {
        color: #000000 !important;
    }
    .stButton>button {
        width: 100%;
        border-radius: 4px;
        height: 3em;
        background-color: #FF6719;
        color: white;
        font-weight: 600;
        border: none;
        transition: all 0.2s;
        box-shadow: 0 2px 4px rgba(255, 103, 25, 0.2);
    }
    .stButton>button:hover {
        background-color: #E85D15;
        border: none;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(255, 103, 25, 0.3);
    }
    h1, h1 * {
        color: #000000 !important;
        font-weight: 700;
    }
    h2, h3, h2 *, h3 * {
        color: #FF6719 !important;
        font-weight: 600;
    }
    .divider {
        text-align: center;
        margin: 30px 0;
        color: #888;
        font-weight: 600;
    }
    .stTextInput input {
        border-radius: 4px;
        background-color: rgba(255, 255, 255, 0.8);
        border: 1px solid #FFD4A3;
        color: #000000 !important;
    }
    .stTextInput input:focus {
        border-color: #FF6719;
        box-shadow: 0 0 0 1px #FF6719;
    }
    [data-testid="stFileUploader"] {
        background-color: rgba(255, 255, 255, 0.6);
        border-radius: 8px;
        padding: 20px;
        border: 2px dashed #FFD4A3;
    }
</style>
""", unsafe_allow_html=True)

st.title("📖 Substack to NotebookLM")
st.markdown("""
Convert Substack content into clean Markdown ready for **NotebookLM** training.
""")

st.markdown("---")

# ZIP Upload Section
st.markdown("### 📁 Upload Your Own Export")
st.caption("Export your full archive from Substack settings → Account → Export")
uploaded_file = st.file_uploader("Upload Substack Export ZIP", type="zip", label_visibility="collapsed")

if uploaded_file:
    output_format_zip = st.radio(
        "Output Format",
        ["Combined File", "ZIP of Markdown Files"],
        key="zip_format",
        horizontal=True
    )
    
    if st.button("Process My Archive", key="zip_btn", type="primary"):
        combine = output_format_zip == "Combined File"
        with st.spinner("Processing your archive..."):
            with tempfile.TemporaryDirectory() as tmp_dir:
                zip_path = os.path.join(tmp_dir, "export.zip")
                with open(zip_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                final_out_dir = os.path.join(tmp_dir, "output")
                os.makedirs(final_out_dir)
                
                success, result = process_substack_zip(zip_path, final_out_dir, combine=combine)
                
                if success:
                    st.balloons()
                    st.success("✅ Conversion complete!")
                    with open(result, "rb") as f:
                        st.download_button(
                            label="📥 Download Markdown",
                            data=f,
                            file_name=os.path.basename(result),
                            mime="text/markdown" if combine else "application/zip",
                            type="primary"
                        )
                else:
                    st.error(f"❌ Error: {result}")

# Divider
st.markdown('<div class="divider">— OR —</div>', unsafe_allow_html=True)

# URL Scraping Section
st.markdown("### 🌐 Input Your Favorite Author's Link!")
st.caption("Scrapes public posts from any Substack (RSS feeds show ~10-20 recent posts)")
substack_url = st.text_input(
    "Substack URL",
    placeholder="vixqueen.substack.com",
    label_visibility="collapsed"
)

if substack_url:
    if st.button("Scrape Public Posts", key="url_btn", type="primary"):
        with st.spinner("Scraping RSS feed..."):
            with tempfile.TemporaryDirectory() as tmp_dir:
                final_out_dir = os.path.join(tmp_dir, "output")
                os.makedirs(final_out_dir)
                
                success, result = scrape_substack_rss(substack_url, final_out_dir, combine=True)
                
                if success:
                    st.balloons()
                    st.success("✅ Scrape complete!")
                    with open(result, "rb") as f:
                        st.download_button(
                            label="📥 Download Combined Markdown",
                            data=f,
                            file_name=os.path.basename(result),
                            mime="text/markdown",
                            type="primary"
                        )
                else:
                    st.error(f"❌ Error: {result}")

st.markdown("---")
st.caption("Optimized for NotebookLM training. | Built with ❤️ for Substack Authors")
