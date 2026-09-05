import streamlit as st
import tempfile
import os
from main import ollama_run, get_system_specs


def get_recommended_models(vram):
    if vram < 6.0:
        return "qwen2.5:1.5b", "base", "Low Spec (< 6 GB VRAM)"
    elif 6.0 <= vram < 11.0:
        return "dolphin-llama3:latest", "small", "Mid Spec (6–10 GB VRAM)"
    elif 11.0 <= vram < 18.0:
        return "qwen2.5:14b", "medium", "High Spec (11–16 GB VRAM)"
    else:
        return "qwen2.5:32b", "large-v3", "Enthusiast Spec (18+ GB VRAM)"
st.set_page_config(page_title="Multimedia Analyzer", layout="wide")

st.sidebar.header("System & Debug Info")

specs = get_system_specs()
for key, value in specs.items():
    st.sidebar.text(f"{key}: {value}")

with st.sidebar.expander("View Raw Hardware Dict"):
    st.json(specs)
st.title("DocScannerLLM")
st.write("Upload a document, audio, or video file to get the summary")
uploaded_file = st.file_uploader(
    "Choose a file",
type=[
        "txt", "pdf", "docx", "xlsx", "csv", "html",
        "mp3", "wav", "flac", "m4a", "aac", "ogg", "wma", "alac", "aiff", "amr", "opus",
        "mp4", "avi", "mkv", "mov", "webm", "wmv", "flv", "m4v", "mpeg", "mpg", "3gp", "ts", "vob"
    ]
)
if uploaded_file is not None:
    rec_llm, rec_whisper, tier_name = get_recommended_models(specs["VRAM_GB"])
    st.info(f"Hardware Tier Detected: **{tier_name}** | GPU: {specs['GPU']} ({specs['VRAM_GB']} GB VRAM)")
    advanced_mode = st.toggle("Advanced Mode (Manual Model Selection)")
    if advanced_mode:
        llm_options = [
            "llama3.2:1b", "llama3.2:3b", "qwen2.5:1.5b", "qwen2.5:3b",
            "dolphin-llama3:latest", "llama3.1:8b", "qwen2.5:7b",
            "qwen2.5:14b", "qwen2.5:32b"
        ]
        whisper_options = ["tiny", "base", "small", "medium", "large-v3"]
        col1, col2 = st.columns(2)
        with col1:
            default_llm_index = llm_options.index(rec_llm) if rec_llm in llm_options else 0
            selected_llm = st.selectbox("Select LLM:", llm_options, index=default_llm_index)
        with col2:
            default_whisper_index = whisper_options.index(rec_whisper)
            selected_whisper = st.selectbox("Select Whisper Engine:", whisper_options, index=default_whisper_index)
    else:
        selected_llm = rec_llm
        selected_whisper = rec_whisper
        st.caption(f"Active Models: `{selected_llm}` and `Whisper {selected_whisper}`")


    if st.button("Generate Summary"):
        with st.spinner("Transcribing Media"):
            file_extension=os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_file_path=temp_file.name
            try:

                st.write(f"Running extraction with `{specs['Precision']}` on `{specs['Device']}`...")
                summary=ollama_run(temp_file_path, selected_llm, selected_whisper)
                st.subheader("Result")
                st.write(summary)
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
