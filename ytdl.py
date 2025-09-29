from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadCancelled
import imageio_ffmpeg

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import requests
from packaging import version

import threading
import os
import subprocess
import time
import glob
import sys
import webbrowser
import re

# ----------------- Worker Functions -----------------
CURRENT_VERSION = "1.4.2"
REPO = "JordanDSilva/youtube-downloader"

ffmpeg_process = None
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
cancel_event = threading.Event()

def check_for_update():
    try:
        url = f"https://api.github.com/repos/{REPO}/releases/latest"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        latest = response.json()["tag_name"].lstrip("v")

        release_url = response.json()["html_url"]

        if version.parse(latest) > version.parse(CURRENT_VERSION):
            ans = messagebox.askyesno(
                "Update Available",
                f"A new version {latest} is available!\n"
                f"You have {CURRENT_VERSION}.\n\n"
                "Do you want to open GitHub to download it?"
            )
            if ans:
                webbrowser.open(release_url)
            return ""
        elif version.parse(latest) == version.parse(CURRENT_VERSION):
            return f"Up to date (version {CURRENT_VERSION})"
        else:
            return "You are ahead (dev build)"
    except Exception as e:

        return f"Update check failed:\n{e}"

def paste_clipboard(root, url_entry):
    try:
        url = root.clipboard_get().strip()
        url_entry.delete(0, tk.END)   # clear any existing text
        url_entry.insert(0, url)      # insert clipboard content
    except tk.TclError:
        messagebox.showwarning("Clipboard empty", "No text found in clipboard")

def make_safe_filename(name):
    name = name.replace("&", "and")
    name = re.sub(r'[\\/:*?"<>|]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def convert_to_mp4(input_file: str) -> str:
    global ffmpeg_process
    base, _ = os.path.splitext(input_file)
    output_file = base + ".mp4"
    safe_input = input_file
    safe_output  = output_file

    cmd = [
        ffmpeg_path, "-y", "-i", safe_input,
        "-c:v", "copy", 
        "-c:a", "aac",
        safe_output
    ]
    
    ffmpeg_process = subprocess.Popen(cmd) 
 
    try:
        while True:
            # check if process finished
            if ffmpeg_process.poll() is not None:
                break
            # check cancel flag
            if cancel_event.is_set():
                ffmpeg_process.terminate()  # stop ffmpeg
                ffmpeg_process.wait()
                raise Exception("Conversion cancelled by user")
            time.sleep(0.1)

        if ffmpeg_process.returncode != 0:
            _, stderr = ffmpeg_process.communicate(timeout=1)
            raise Exception(f"ffmpeg failed :(")

    finally:
        ffmpeg_process = None
        # optionally delete input_file if needed
        if os.path.exists(safe_input):
            os.remove(safe_input)

    return safe_output

def download_video(url, save_path, log_widget, status_label):
    try:
        status_label.config(text="Downloading...")

        ydl_opts = {
            'format': "bestvideo[height<=1080]+bestaudio/best" 
                        if not extract_audio_var.get() else "bestaudio/best",
            'ffmpeg_location': ffmpeg_path,
            'outtmpl': os.path.join(save_path, '%(playlist_index)s - %(title)s.%(ext)s')
                        if playlist_var.get() else os.path.join(save_path, '%(title)s.%(ext)s'),
            'noplaylist': not playlist_var.get(),
            'ignoreerrors': True,
            'postprocessors': [{            
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '320',
                                }] if extract_audio_var.get() else [],
            'progress_hooks': [lambda d: progress_hook(d, log_widget, status_label)],
            'quiet': True,
            'no_warnings': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if "entries" in info:
                entries = info["entries"]  # full playlist
            else:
                entries = [info]  # single video
            
        if not extract_audio_var.get():
            for video in entries:
                if not video:
                    continue

                if cancel_event.is_set():
                    log_widget.insert(tk.END, "Cancelled before conversion.\n")
                    break
                in_file = ydl.prepare_filename(video)

                log_widget.insert(tk.END, f"Converting {video['title']}...\n")
                log_widget.see(tk.END)
                try:
                    out_file = convert_to_mp4(in_file)
                    log_widget.insert(tk.END, f"Saved as {out_file}\n")
                except Exception as conv_err:
                    log_widget.insert(tk.END, f"Conversion failed: {conv_err}\n")
        
        status_label.config(text="Done!")
        log_widget.insert(tk.END, "All downloads finished.\n")
        log_widget.see(tk.END)

    except Exception as e:
        if str(e) == "Download cancelled by user":
            status_label.config(text="Cancelled")
            log_widget.insert(tk.END, "Download cancelled.\n")
            for f in glob.glob(os.path.join(save_path, "*.part")):
                try: os.remove(f)
                except: pass
        else:
            messagebox.showerror("Error", str(e))
            status_label.config(text="Download failed :(")

def progress_hook(d, log_widget, status_label):
    if cancel_event.is_set():
        log_widget.insert("end", "Cancelled by user\n")
        log_widget.see("end")
        status_label.config(text="Cancelled")
        raise DownloadCancelled("Download cancelled by user")

    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)
        pct = downloaded * 100 / total if total else 0
        status_label.config(text=f"Downloading... {pct:.1f}%")
    elif d['status'] == 'finished':
        log_widget.insert(tk.END, "Download complete. Processing...\n")
        log_widget.see(tk.END)
        status_label.config(text="Processing...")

# ----------------- GUI Functions -----------------
def start_download():
    url = url_entry.get().strip()
    save_path = path_var.get()
    
    if not url:
        messagebox.showwarning("Input required", "Please enter a YouTube URL")
        return
    if not save_path:
        messagebox.showwarning("Input required", "Please choose a save folder")
        return
    
    cancel_event.clear()
    log_box.insert(tk.END, f"Starting download: {url} \n")
    log_box.see(tk.END)
    
    threading.Thread(
        target=download_video,
        args=(url, save_path, log_box, status_label),
        daemon=True
    ).start()

def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        path_var.set(folder)

def on_startup():
    msg = check_for_update()
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)

# ----------------- GUI Layout -----------------
root = tk.Tk()
playlist_var = tk.BooleanVar(value=False)
extract_audio_var = tk.BooleanVar(value=False)

root.title("YouTube Downloader")
root.resizable(True, True)

for i in range(3):
    root.grid_columnconfigure(i, weight=1)
for i in range(5):
    root.grid_rowconfigure(i, weight=0)
root.grid_rowconfigure(4, weight=1)  # log box expands

url_entry = tk.Entry(root)
url_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
tk.Button(root, text="Paste YouTube URL: ", command=lambda: paste_clipboard(root, url_entry), bg="red", fg="white", activebackground="darkred", activeforeground="white").grid(row=0, column=0, padx=5, pady=5)

tk.Label(root, text="Save to:").grid(row=1, column=0, sticky="w")
path_var = tk.StringVar()
tk.Entry(root, textvariable=path_var).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
tk.Button(root, text="Browse", command=choose_folder).grid(row=1, column=2, padx=5, pady=5)

tk.Button(root, text="Download", command=start_download).grid(row=3, column=1, pady=10)
status_label = tk.Label(root, text="Idle", fg="blue")
status_label.grid(row=3, column=0, sticky="w", padx=5)

tk.Button(root, text="Cancel", command=lambda: cancel_event.set()).grid(row = 3, column=2, pady=10)

playlist_check = tk.Checkbutton(root, text="Download entire playlist", variable=playlist_var)
playlist_check.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=5)

extract_audio_check = tk.Checkbutton(root, text="Extract audio", variable=extract_audio_var)
extract_audio_check.grid(row=2, column=1, columnspan=3, sticky="w", padx=5, pady=5)

log_box = tk.Text(root, wrap="word")
log_box.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

root.after(500, on_startup)  # run after window loads

root.mainloop()

