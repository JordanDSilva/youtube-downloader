import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading, os, subprocess, requests
import sys
import webbrowser
from yt_dlp import YoutubeDL

# ----------------- Worker Functions -----------------
CURRENT_VERSION = "1.0.0"
REPO = "JordanDSilva/youtube-downloader"

def get_ffmpeg_path():
    if hasattr(sys, "_MEIPASS"):  # Running from PyInstaller bundle
        # Windows bundle
        return os.path.join(sys._MEIPASS, "ffmpeg.exe")
    return "/usr/bin/ffmpeg"  # fallback: system-installed ffmpeg

def check_for_update():
    try:
        url = f"https://api.github.com/repos/{REPO}/releases/latest"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        latest = response.json()["tag_name"].lstrip("v")

        release_url = response.json()["html_url"]

        if latest != CURRENT_VERSION:
            ans = messagebox.askyesno(
                "Update Available",
                f"A new version {latest} is available!\n"
                f"You have {CURRENT_VERSION}.\n\n"
                "Do you want to open GitHub to download it?"
            )
            if ans:
                webbrowser.open(release_url)
            return ""
        else:
            return f"Up to date (version {CURRENT_VERSION})"
    except Exception as e:
        return f"Update check failed:\n{e}"

def download_video(url, save_path, log_widget, status_label):
    try:
        status_label.config(text="Downloading...")
        ydl_opts = {
            'format': "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            'merge_output_format': 'mp4',
            'ffmpeg_location': os.path.dirname(get_ffmpeg_path()),
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'progress_hooks': [lambda d: progress_hook(d, log_widget, status_label)],
            'quiet': True,
            'no_warnings': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Get the downloaded filename
        info = ydl.extract_info(url, download=False)
        ext = info.get('ext', 'mp4')
        downloaded_file = os.path.join(save_path, f"{info['title']}.{ext}")

        log_widget.insert(tk.END, f"Download finished! Saved as:\n{downloaded_file}\n")
        log_widget.see(tk.END)
        status_label.config(text="Done!")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        status_label.config(text="Download failed :(")

def progress_hook(d, log_widget, status_label):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)
        pct = downloaded * 100 / total if total else 0
        log_widget.insert(tk.END, f"Downloading... {pct:.1f}%\n")
        log_widget.see(tk.END)
        status_label.config(text=f"Downloading... {pct:.1f}%")
    elif d['status'] == 'finished':
        log_widget.insert(tk.END, "Download complete. Processing...\n")
        log_widget.see(tk.END)
        status_label.config(text="Processing...")

# ----------------- GUI Functions -----------------
def start_download():
    url = url_entry.get().strip()
    save_path = path_var.get()
    #fmt_choice = formats_var.get()
    if not url:
        messagebox.showwarning("Input required", "Please enter a YouTube URL")
        return
    if not save_path:
        messagebox.showwarning("Input required", "Please choose a save folder")
        return
    
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
root.title("YouTube Downloader")
root.resizable(True, True)

for i in range(3):
    root.grid_columnconfigure(i, weight=1)
for i in range(5):
    root.grid_rowconfigure(i, weight=0)
root.grid_rowconfigure(4, weight=1)  # log box expands

tk.Label(root, text="YouTube URL:").grid(row=0, column=0, sticky="w")
url_entry = tk.Entry(root)
url_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

tk.Label(root, text="Save to:").grid(row=1, column=0, sticky="w")
path_var = tk.StringVar()
tk.Entry(root, textvariable=path_var).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
tk.Button(root, text="Browse", command=choose_folder).grid(row=1, column=2, padx=5, pady=5)

tk.Button(root, text="Download", command=start_download).grid(row=3, column=1, pady=10)
status_label = tk.Label(root, text="Idle", fg="blue")
status_label.grid(row=3, column=0, sticky="w", padx=5)

log_box = tk.Text(root, wrap="word")
log_box.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

root.after(500, on_startup)  # run after window loads

root.mainloop()

