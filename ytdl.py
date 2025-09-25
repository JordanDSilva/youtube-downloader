import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading, os, subprocess
from yt_dlp import YoutubeDL

# ----------------- Worker Functions -----------------
#def fetch_formats(url, format_box, formats_var, status_label):
#    try:
#        status_label.config(text="Fetching formats...")
#        ydl_opts = {'quiet': True, 'no_warnings': True}
#
#        with YoutubeDL(ydl_opts) as ydl:
#            info = ydl.extract_info(url, download=False)
#            formats = info.get('formats', [])
#            choices = []
#            for f in formats:
#                fmt_id = f['format_id']
#                ext = f.get('ext')
#                res = f.get('format_note') or f.get('height') or "unknown"
#                vcodec = f.get('vcodec')
#                acodec = f.get('acodec')
#
#                # Label progressive vs video-only vs audio-only
#                if vcodec != "none" and acodec != "none":
#                    kind = "video+audio"
#                elif vcodec != "none":
#                    kind = "video-only"
#                elif acodec != "none":
#                    kind = "audio-only"
#                else:
#                    kind = "unknown"
#
#                choices.append(f"{fmt_id} - {res} ({ext}, {kind})")
#
#            if not choices:
#                messagebox.showwarning("No formats", "No formats found.")
#                status_label.config(text="No formats found")
#                return
#
#            format_box['values'] = choices
#            format_box.current(0)
#            formats_var.set(choices[0])
#            status_label.config(text="Formats fetched ✅")
#    except Exception as e:
#        messagebox.showerror("Error", f"Could not fetch formats:\n{e}")
#        status_label.config(text="Fetch failed ❌")

#def convert_to_mp4(input_file, status_label):
#    base, ext = os.path.splitext(input_file)
#    if ext.lower() == ".mp4":
#        return input_file  # already mp4
#
#    output_file = base + ".mp4"
#    status_label.config(text=f"Converting {ext} → mp4...")
#    
#    subprocess.run([
#        "ffmpeg",
#        "-i", input_file,
#        "-c:v", "copy",   # copy video
#        "-c:a", "aac",    # convert audio
#        output_file
#    ])
#    
#    # Delete original file after conversion
#    try:
#        os.remove(input_file)
#        status_label.config(text=f"Converted to MP4 and deleted {ext}")
#    except Exception as e:
#        status_label.config(text=f"Converted but failed to delete {ext}: {e}")
#    
#    return output_file

#def download_video(url, save_path, fmt_code, log_widget, status_label):
def download_video(url, save_path, log_widget, status_label):
    try:
        status_label.config(text="Downloading...")
        ydl_opts = {
            #'format': fmt_code,
            'format': "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            'merge_output_format': 'mp4',
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

        # Convert if needed
        #final_file = convert_to_mp4(downloaded_file, status_label)

        log_widget.insert(tk.END, f"Download finished! Saved as:\n{downloaded_file}\n")
        log_widget.see(tk.END)
        status_label.config(text="Done ✅")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        status_label.config(text="Download failed ")

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
    #if not fmt_choice:
    #    messagebox.showwarning("Select format", "Please fetch formats first.")
    #    return
    #
    #fmt_code = fmt_choice.split(" - ")[0]
    #if "video-only" in fmt_choice:
    #    fmt_code += "+bestaudio"

    #log_box.insert(tk.END, f"Starting download: {url} ({fmt_code})\n")
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

#def fetch_resolutions():
#    url = url_entry.get().strip()
#    if not url:
#        messagebox.showwarning("Input required", "Please enter a YouTube URL")
#        return
#    threading.Thread(
#        target=fetch_formats,
#        args=(url, format_box, formats_var, status_label),
#        daemon=True
#    ).start()

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

#tk.Label(root, text="Resolution / Format:").grid(row=2, column=0, sticky="w")
#formats_var = tk.StringVar()
#format_box = ttk.Combobox(root, textvariable=formats_var, state="readonly")
#format_box.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
#tk.Button(root, text="Fetch", command=fetch_resolutions).grid(row=2, column=2, padx=5, pady=5)

tk.Button(root, text="Download", command=start_download).grid(row=3, column=1, pady=10)
status_label = tk.Label(root, text="Idle", fg="blue")
status_label.grid(row=3, column=0, sticky="w", padx=5)

log_box = tk.Text(root, wrap="word")
log_box.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

root.mainloop()

