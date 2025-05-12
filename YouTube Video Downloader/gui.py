import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import urllib.request
from typing import Dict, Optional

from downloader import YouTubeDownloader

class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Downloader")
        self.root.geometry("800x600")
        self.root.minsize(600, 500)
        
        self.downloader = YouTubeDownloader()
        self.streams = {}
        self.is_dark_mode = False
        self.thumbnail_image = None
        self.download_thread = None
        
        # Set up callbacks
        self.downloader.progress_callback = self.update_progress
        self.downloader.complete_callback = self.download_complete
        
        self.create_widgets()
        self.apply_theme()
        
        # Try to get URL from clipboard on startup
        self.root.after(500, self.check_clipboard)
    
    def create_widgets(self):
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # URL input section
        url_frame = ttk.Frame(self.main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(url_frame, text="YouTube URL:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=50)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.fetch_btn = ttk.Button(url_frame, text="Fetch Video", command=self.fetch_video)
        self.fetch_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Thumbnail and video info section
        self.info_frame = ttk.Frame(self.main_frame)
        self.info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Thumbnail on the left
        self.thumbnail_frame = ttk.LabelFrame(self.info_frame, text="Thumbnail")
        self.thumbnail_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.thumbnail_label = ttk.Label(self.thumbnail_frame)
        self.thumbnail_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Video details and options on the right
        options_frame = ttk.Frame(self.info_frame)
        options_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Video title
        self.title_frame = ttk.LabelFrame(options_frame, text="Video Title")
        self.title_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.title_label = ttk.Label(self.title_frame, text="No video selected", wraplength=300)
        self.title_label.pack(fill=tk.X, padx=10, pady=10)
        
        # Resolution selection
        resolution_frame = ttk.LabelFrame(options_frame, text="Select Quality")
        resolution_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.resolution_var = tk.StringVar()
        self.resolution_combo = ttk.Combobox(resolution_frame, textvariable=self.resolution_var, state="readonly")
        self.resolution_combo.pack(fill=tk.X, padx=10, pady=10)
        
        # Download location
        location_frame = ttk.LabelFrame(options_frame, text="Download Location")
        location_frame.pack(fill=tk.X, pady=(0, 10))
        
        location_inner = ttk.Frame(location_frame)
        location_inner.pack(fill=tk.X, padx=10, pady=10)
        
        self.location_var = tk.StringVar(value=self.downloader.download_path)
        ttk.Label(location_inner, textvariable=self.location_var, wraplength=300).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(location_inner, text="Browse", command=self.select_download_path).pack(side=tk.RIGHT)
        
        # Download button and progress section
        download_frame = ttk.Frame(self.main_frame)
        download_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(download_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        button_frame = ttk.Frame(download_frame)
        button_frame.pack(fill=tk.X)
        
        self.download_btn = ttk.Button(button_frame, text="Download", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(button_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=10)
        
        # Dark mode toggle
        self.theme_btn = ttk.Button(button_frame, text="Toggle Dark Mode", command=self.toggle_theme)
        self.theme_btn.pack(side=tk.RIGHT)
        
        # Initially disable some widgets
        self.resolution_combo.config(state="disabled")
        self.download_btn.config(state="disabled")
    
    def fetch_video(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        
        self.status_var.set("Fetching video information...")
        self.fetch_btn.config(state="disabled")
        
        # Run in a separate thread to avoid freezing the GUI
        threading.Thread(target=self._fetch_video_thread, args=(url,), daemon=True).start()
    
    def _fetch_video_thread(self, url):
        success, message, thumbnail_url = self.downloader.set_url(url)
        
        # Update UI in the main thread
        self.root.after(0, lambda: self._update_after_fetch(success, message, thumbnail_url))
    
    def _update_after_fetch(self, success, message, thumbnail_url):
        self.fetch_btn.config(state="normal")
        self.status_var.set(message)
        
        if success:
            # Update video title
            self.title_label.config(text=self.downloader.video.title)
            
            # Load thumbnail
            if thumbnail_url:
                self.load_thumbnail(thumbnail_url)
            
            # Update resolution dropdown
            self.streams = self.downloader.get_available_streams()
            self.resolution_combo.config(values=list(self.streams.keys()))
            if self.streams:
                self.resolution_combo.current(0)
                self.resolution_combo.config(state="readonly")
                self.download_btn.config(state="normal")
        else:
            self.resolution_combo.config(state="disabled")
            self.download_btn.config(state="disabled")
            messagebox.showerror("Error", message)
    
    def load_thumbnail(self, url):
        try:
            # Download thumbnail image
            response = requests.get(url)
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            
            # Resize to fit in the frame (maintaining aspect ratio)
            img.thumbnail((300, 200))
            
            # Convert to PhotoImage for tkinter
            self.thumbnail_image = ImageTk.PhotoImage(img)
            self.thumbnail_label.config(image=self.thumbnail_image)
        except Exception as e:
            print(f"Error loading thumbnail: {e}")
    
    def select_download_path(self):
        path = filedialog.askdirectory(initialdir=self.downloader.download_path)
        if path:
            self.downloader.set_download_path(path)
            self.location_var.set(path)
    
    def start_download(self):
        if not self.streams:
            messagebox.showerror("Error", "No video selected")
            return
        
        selected = self.resolution_var.get()
        if not selected:
            messagebox.showerror("Error", "Please select a quality option")
            return
        
        # Disable download button to prevent multiple clicks
        self.download_btn.config(state="disabled")
        self.fetch_btn.config(state="disabled")
        self.progress_var.set(0)
        self.status_var.set("Starting download...")
        
        # Start download in a separate thread
        self.download_thread = threading.Thread(
            target=self._download_thread,
            args=(selected,),
            daemon=True
        )
        self.download_thread.start()
    
    def _download_thread(self, selected):
        success, message = self.downloader.download_video(selected, self.streams)
        
        # Update UI in the main thread
        if not success:
            self.root.after(0, lambda: self._handle_download_error(message))
    
    def _handle_download_error(self, message):
        self.status_var.set("Download failed")
        self.download_btn.config(state="normal")
        self.fetch_btn.config(state="normal")
        messagebox.showerror("Download Error", message)
    
    def update_progress(self, stream, chunk, bytes_remaining):
        # Calculate progress percentage
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        
        # Update progress bar and status
        self.progress_var.set(percentage)
        self.status_var.set(f"Downloading: {percentage:.1f}%")
    
    def download_complete(self, stream, file_path):
        self.root.after(0, self._handle_download_complete, file_path)
    
    def _handle_download_complete(self, file_path):
        self.progress_var.set(100)
        self.status_var.set("Download complete!")
        self.download_btn.config(state="normal")
        self.fetch_btn.config(state="normal")
        
        # Show success message with file path
        messagebox.showinfo("Download Complete", 
                           f"Video downloaded successfully to:\n{file_path}")
    
    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
    
    def apply_theme(self):
        style = ttk.Style()
        
        if self.is_dark_mode:
            # Dark theme
            self.root.configure(bg="#2d2d2d")
            style.configure("TFrame", background="#2d2d2d")
            style.configure("TLabel", background="#2d2d2d", foreground="#ffffff")
            style.configure("TLabelframe", background="#2d2d2d", foreground="#ffffff")
            style.configure("TLabelframe.Label", background="#2d2d2d", foreground="#ffffff")
            style.configure("TButton", background="#444444", foreground="#ffffff")
            self.theme_btn.config(text="Toggle Light Mode")
        else:
            # Light theme
            self.root.configure(bg="#f0f0f0")
            style.configure("TFrame", background="#f0f0f0")
            style.configure("TLabel", background="#f0f0f0", foreground="#000000")
            style.configure("TLabelframe", background="#f0f0f0", foreground="#000000")
            style.configure("TLabelframe.Label", background="#f0f0f0", foreground="#000000")
            style.configure("TButton", background="#e0e0e0", foreground="#000000")
            self.theme_btn.config(text="Toggle Dark Mode")
    
    def check_clipboard(self):
        """Check if clipboard contains a YouTube URL and auto-paste it"""
        try:
            clipboard = self.root.clipboard_get()
            if clipboard and ("youtube.com" in clipboard or "youtu.be" in clipboard):
                if not self.url_var.get():  # Only if URL field is empty
                    self.url_var.set(clipboard)
                    messagebox.showinfo("URL Detected", "YouTube URL detected in clipboard and pasted automatically.")
        except:
            pass  # Ignore clipboard errors