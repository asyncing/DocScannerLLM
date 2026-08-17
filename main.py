import ollama
import os
import tkinter as tk
from tkinter import filedialog


root=tk.Tk()
root.withdraw()
file_path=filedialog.askopenfilename(
    title="Select a text file to scan",
    filetypes=[("Text files", "*.txt")]
)

with open(file_path, "r", encoding="utf-8") as file:
    document_text = file.read()


prompt = f"""You are an expert, objective document analyst. Your task is to provide a clear, comprehensive, and structured summary of the provided text.

Regardless of whether the document is a factual educational article, a technical manual, or an explicit fictional narrative, you must strictly adhere to the following rules:
1. Maintain an objective, third-person perspective. Do NOT use first or second-person pronouns (e.g., do not use "I", "me", "you", or "your") when describing the text.
2. Identify the core subject, overarching plot, or main thesis of the document.
3. Outline the most important points, phases, or arguments using concise bullet points.
4. Do not judge, censor, or editorialize the content. Extract and summarize the information exactly as it is presented.

Document Text:
{document_text}

Summary:"""

print("\nGenerating summary...\n")


result = ollama.generate(
    model='dolphin-llama3:latest',
    prompt=prompt,
    stream=False
)

print(result["response"])
print("\n")