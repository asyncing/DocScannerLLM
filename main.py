import ollama
import os
import tkinter as tk
from tkinter import filedialog
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


if shutil.which("ollama") is None:
    os_name=platform.system()
    print("Ollama is not installed. Initiating setup to install Ollama....")
    if os_name=="Windows":
        installer_path="OllamaSetup.exe"
        urllib.request.urlretrieve("https://ollama.com/downloads/OllamaSetup.exe", installer_path)
        os.startfile(installer_path)
    elif os_name=="Darwin":
        print("Opening the official Ollama Mac download page...")
        webbrowser.open("https://ollama.com/download/Ollama.dmg")
    elif os_name=="Linux":
        print("Running official Ollama install script for Linux")
        subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True)
    print("Please complete the Ollama setup, then run this script again.")
def ollama_status_check():
    try:
        urllib.request.urlopen("http://localhost:11434/", timeout=2)
        return True
    except URLError:
        return False
if not ollama_status_check():
    print("Starting Ollama background service...")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(5)



LLM="dolphin-llama3:latest"

cpu_name=cpuinfo.get_cpu_info()["brand_raw"]
device="cpu"
use_fp16=False
nvidia_map={1: "Tesla",
            2: "Fermi",
            3: "Kepler",
            5: "Maxwell",
            6: "Pascal",
            7: "Turing/Volta",
            8: "Ampere/Ada",
            9: "Hopper",
            10: "Blackwell"}
if torch.cuda.is_available():
    device="cuda"
    gpu_name=torch.cuda.get_device_name(0)
    compute_major=torch.cuda.get_device_capability()[0]
    arch_name=nvidia_map.get(compute_major, "Unknown Architecture")
    if compute_major >=7:
        use_fp16=True
        print(f"CPU- [{cpu_name}] detected, GPU- [{gpu_name}] detected, Architecture: {arch_name}. Using FP16")
    else:
        use_fp16=False
        print(f"CPU- [{cpu_name}] detected, GPU- [{gpu_name}] detected. Architecture: {arch_name}. Falling back to FP32")
else:
    print(f"No CUDA GPU detected. Running on CPU({cpu_name}) in FP32")

root=tk.Tk()
root.withdraw()
file_path=filedialog.askopenfilename(
    title="Select a text file to scan",
filetypes=[
        ("All Supported", "*.txt *.pdf *.docx *.xlsx *.csv *.html *.mp3 *.wav *.flac *.m4a *.aac *.ogg *.wma *.alac *.aiff *.amr *.opus *.mp4 *.avi *.mkv *.mov *.webm *.wmv *.flv *.m4v *.mpeg *.mpg *.3gp *.ts *.vob"),
        ("Documents", "*.pdf *.docx *.txt"),
        ("Spreadsheets", "*.xlsx *.csv"),
        ("Audio Files", "*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.wma *.alac *.aiff *.amr *.opus"),
        ("Video Files", "*.mp4 *.avi *.mkv *.mov *.webm *.wmv *.flv *.m4v *.mpeg *.mpg *.3gp *.ts *.vob"),
        ("All Files", "*.*")
    ]
)
if not file_path:
    print("No file selected. Exiting...")
    time.sleep(5)
    exit()

def extraction(file_path):
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

        print("Transcribing Media...")
        model_size="medium" if use_fp16 else "base"
        model=whisper.load_model(model_size).to(device)
        text=model.transcribe(file_path, fp16=use_fp16)["text"]
    else:
        print(f"Unsupported file type: {ext_low}")
        time.sleep(5)
        exit()
    return text
document_text=extraction(file_path)


prompt = f"""You are an expert, objective multimedia analyst. Your task is to provide a clear, comprehensive, and structured description and summary of the provided text, audio, or video file.

Regardless of whether the file is a factual document, a technical manual, a fictional narrative, or an audio/video recording, you must strictly adhere to the following rules:

1. Maintain an objective tone: Use a strict third-person perspective. Do NOT use first- or second-person pronouns (e.g., do not use "I", "me", "you", or "your") when describing the content.

2. Transcribe and describe all media elements: For audio and video files, exhaustively describe everything seen and heard. You must explicitly detail visual scenes, camera movements, on-screen actions, visible text, spoken dialogue, speaker changes, tone of voice, background noises, and sound effects.

3. Identify the core thesis: Define the core subject, overarching plot, or main thesis of the document or media file.

4. Provide a structured chronological outline: Outline the most important points, narrative phases, visual sequences, or arguments using concise bullet points. If analyzing audio/video, present this breakdown chronologically.

5. Remain neutral: Do not judge, censor, or editorialize the content. Extract, describe, and summarize the information exactly as it is presented in the source material.

Document Text:
{document_text}

Summary:"""

print("\nGenerating summary...\n")


result = ollama.generate(
    model=LLM,
    prompt=prompt,
    stream=False
)

print(result["response"])
print("\n")