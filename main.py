import ollama
import os
import docx
import pymupdf as pdf
import pandas as pd
from bs4 import BeautifulSoup
import whisper
import time
import torch
import cpuinfo
import shutil
import platform
import webbrowser
import subprocess
import urllib.request
from urllib.error import URLError
import socket


def check_os():
    if shutil.which("ollama") is None:
        os_name=platform.system()
        print("Ollama is not installed. Initiating setup to install Ollama....")
        if os_name=="Windows":
            installer_path="OllamaSetup.exe"
            urllib.request.urlretrieve("https://ollama.com/download/OllamaSetup.exe", installer_path)
            os.startfile(installer_path)
        elif os_name=="Darwin":
            print("Opening the official Ollama Mac download page...")
            webbrowser.open("https://ollama.com/download/Ollama.dmg")
        elif os_name=="Linux":
            print("Running official Ollama install script for Linux")
            subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True)
        print("Please complete the Ollama setup, then run this script again.")
check_os()
def ollama_status_check():
    try:
        urllib.request.urlopen("http://localhost:11434/", timeout=2)
        return True
    except (URLError, socket.timeout,TimeoutError):
        return False
if not ollama_status_check():
    print("Starting Ollama background service...")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(5)
ollama_status_check()



LLM="dolphin-llama3:latest"

def get_system_specs():
    cpu_name = cpuinfo.get_cpu_info()["brand_raw"]
    device = "cpu"
    use_fp16 = False
    gpu_name = "None"
    arch_name = "N/A"

    nvidia_map = {
        1: "Tesla", 2: "Fermi", 3: "Kepler", 5: "Maxwell",
        6: "Pascal", 7: "Turing/Volta", 8: "Ampere/Ada", 9: "Hopper", 10: "Blackwell"
    }

    vram_gb=0
    if torch.cuda.is_available():
        device = "cuda"
        gpu_name = torch.cuda.get_device_name(0)
        compute_major = torch.cuda.get_device_capability()[0]
        arch_name = nvidia_map.get(compute_major, "Unknown Architecture")
        use_fp16 = compute_major >= 7
        vram_gb=round(torch.cuda.get_device_properties(0).total_memory/(1024**3), 1)

    return {
        "CPU": cpu_name,
        "GPU": gpu_name,
        "VRAM_GB": vram_gb,
        "Architecture": arch_name,
        "Device": device,
        "Precision": "FP16" if use_fp16 else "FP32",
        "Ollama Status": "Running" if ollama_status_check() else "Offline"
    }



specs = get_system_specs()
device = specs["Device"]
use_fp16 = specs["Precision"] == "FP16"



def extraction(file_path, whisper_size):
    _, extension=os.path.splitext(file_path) #_ is throwaway var
    ext_low=extension.lower()
    text=""
    if ext_low==".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text=f.read()
    elif ext_low==".pdf":
        doc=pdf.open(file_path)
        for page in doc:
            text=text+page.get_text()
    elif ext_low== ".docx":
        doc=docx.Document(file_path)
        for para in doc.paragraphs:
            text=text+para.text+"\n"
    elif ext_low in [".xlsx", ".csv"]:
        df=pd.read_excel(file_path) if ext_low==".xlsx" else pd.read_csv(file_path)
        text=df.to_markdown()
    elif ext_low==".html":
        with open(file_path, "r", encoding="utf-8") as f:
            soup=BeautifulSoup(f.read(), "html.parser")
            text=soup.get_text(separator="\n", strip=True)
    elif ext_low in [
        # Audio
        ".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma",
        ".alac", ".aiff", ".amr", ".opus",
        # Video
        ".mp4", ".avi", ".mkv", ".mov", ".webm", ".wmv", ".flv",
        ".m4v", ".mpeg", ".mpg", ".3gp", ".ts", ".vob"
    ]:

        print(f"Transcribing Media using Whisper {whisper_size}...")
        model=whisper.load_model(whisper_size).to(device)
        text=model.transcribe(file_path, fp16=use_fp16)["text"]
    else:
        print(f"Unsupported file type: {ext_low}")
        time.sleep(5)
        exit()
    return text
def check_ollama_model(model_name):
    try:
        res=ollama.list()
        installed=[m.model for m in res.models] if hasattr(res, "models") else [m["name"] for m in res.get("models", [])]
    except Exception:
        installed=[]
    if model_name not in installed:
        print(f"Downloading {model_name}...")
        ollama.pull(model_name)


def ollama_run(file_path, llm_name, whisper_size):
    check_ollama_model(llm_name)
    document_text = extraction(file_path, whisper_size)


    if not document_text or not document_text.strip():
        return "Extraction Error: No text could be extracted from the file. If this is a scanned PDF/image, OCR is required."

    system_instruction = (
        "You are an objective document and media analyst. "
        "Analyze ONLY the provided source material. "
        "Never use first-person ('I', 'me', 'my') or second-person ('you', 'your') pronouns. "
        "Never state your model identity, name, or persona. "
        "Provide zero conversational filler(including anything sexual, political, violent or otherwise controversial) or greetings. "
        "Output strictly following the required headers."
    )

    user_content = f"""Analyze the source material enclosed within the <source_material> tags.

Required Output Structure:
**Core Thesis / Subject**
(1-3 sentence objective summary of the core thesis, allegations, or main subject)

**Chronological Breakdown & Key Details**
* (Bullet points detailing key events, facts, visual/audio details, or timeline in sequential order)

<source_material>
{document_text}
</source_material>"""

    response = ollama.chat(
        model=llm_name,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ],
        options={
            "temperature": 0.1,
            "top_p": 0.9
        }
    )

    return response["message"]["content"]

