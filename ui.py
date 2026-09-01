import streamlit as st
import tempfile
import os
from main import ollama_run, get_system_specs
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
    if st.button("Generate Summary"):
        with st.spinner("Transcribing Media"):
            file_extension=os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_file_path=temp_file.name
            try:

                st.write(f"Running extraction with `{specs['Precision']}` on `{specs['Device']}`...")
                summary=ollama_run(temp_file_path)
                st.subheader("Result")
                st.write(summary)
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
#For Github