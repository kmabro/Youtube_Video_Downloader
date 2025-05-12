import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import re
from PIL import Image, ImageTk
import requests
from io import BytesIO
import time
import subprocess
import sys
import json
import platform

class YouTubeDownloaderApp(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master, padding=20)
        self.master = master
        self.pack(fill=tk.BOTH, expand=True)
        
        # Colors
        self.bg_color = "#f5f0ff"  # Light purple background
        self.accent_color = "#8a4fff"  # Purple accent
        self.text_color = "#333333"  # Dark text
        
        # State variables
        self.video_info = None
        self.thumbnail_image = None
        self.formats = []
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # Configure the master window
        self.master.title("YouTube Video Downloader")
        self.master.geometry("800x600")
        self.master.minsize(600, 500)
        self.master.configure(bg=self.bg_color)
        self.configure(style="Main.TFrame")
        
        # Check for yt-dlp installation
        self.check_ytdlp()
        
        # Create custom styles
        self.create_styles()
        
        # Create the UI elements
        self.create_widgets()
    
    def check_ytdlp(self):
        """Check if yt-dlp is installed and install it if not"""
        try:
            # Try to run yt-dlp --version
            if platform.system() == "Windows":
                subprocess.run(["yt-dlp", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            else:
                subprocess.run(["yt-dlp", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            # yt-dlp is not installed, try to install it
            try:
                messagebox.showinfo("Installing yt-dlp", "yt-dlp is not installed. Installing now...")
                subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"], check=True)
                messagebox.showinfo("Success", "yt-dlp installed successfully!")
            except subprocess.SubprocessError:
                messagebox.showerror("Error", "Failed to install yt-dlp. Please install it manually using: pip install yt-dlp")
                sys.exit(1)
    
    def create_styles(self):
        style = ttk.Style()
        
        # Configure the main frame style
        style.configure("Main.TFrame", background=self.bg_color)
        
        # Configure label styles
        style.configure("Title.TLabel", 
                        font=("Helvetica", 24, "bold"), 
                        foreground="#7030a0",  # Purple
                        background=self.bg_color,
                        anchor="center")
        
        style.configure("Subtitle.TLabel", 
                        font=("Helvetica", 14), 
                        foreground="#666666", 
                        background=self.bg_color,
                        anchor="center")
        
        style.configure("Normal.TLabel", 
                        font=("Helvetica", 12), 
                        foreground=self.text_color, 
                        background=self.bg_color)
        
        # Configure button styles
        style.configure("Accent.TButton", 
                        font=("Helvetica", 12, "bold"))
        
        style.configure("Secondary.TButton", 
                        font=("Helvetica", 12))
        
        # Configure entry style
        style.configure("URL.TEntry", 
                        font=("Helvetica", 12))
    
    def create_widgets(self):
        # Main container for centered content
        main_container = ttk.Frame(self, style="Main.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title and subtitle (centered)
        title_label = ttk.Label(main_container, text="YouTube Video Downloader", style="Title.TLabel")
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_container, 
                                  text="Download any public video from YouTube", 
                                  style="Subtitle.TLabel")
        subtitle_label.pack(pady=(0, 30))
        
        # URL input container (centered)
        url_container = ttk.Frame(main_container, style="Main.TFrame")
        url_container.pack(pady=(0, 20))
        
        # URL entry with icon
        url_frame = ttk.Frame(url_container, style="Main.TFrame")
        url_frame.pack()
        
        # Link icon (using text as placeholder)
        link_icon = ttk.Label(url_frame, text="🔗", font=("Helvetica", 14), background="white")
        link_icon.pack(side=tk.LEFT, padx=(10, 0), pady=10)
        
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=50, font=("Helvetica", 12))
        self.url_entry.pack(side=tk.LEFT, padx=(5, 10), pady=10)
        self.url_entry.insert(0, "Paste a Youtube video URL here")
        self.url_entry.bind("<FocusIn>", self.clear_placeholder)
        self.url_entry.bind("<FocusOut>", self.restore_placeholder)
        
        # Search button (centered below URL input)
        search_button = ttk.Button(main_container, text="Search", style="Accent.TButton", 
                                  command=self.search_video)
        search_button.pack(pady=(0, 20))
        
        # Video info container (initially hidden)
        self.video_container = ttk.Frame(main_container, style="Main.TFrame")
        self.video_container.pack(fill=tk.BOTH, expand=True)
        self.video_container.pack_forget()  # Hide initially
        
        # Thumbnail (centered)
        self.thumbnail_label = ttk.Label(self.video_container, background=self.bg_color)
        self.thumbnail_label.pack(pady=(0, 15))
        
        # Video title
        self.title_var = tk.StringVar()
        self.title_label = ttk.Label(self.video_container, textvariable=self.title_var, 
                                    wraplength=500, justify="center", style="Normal.TLabel")
        self.title_label.pack(pady=(0, 15))
        
        # Format selection
        format_frame = ttk.Frame(self.video_container, style="Main.TFrame")
        format_frame.pack(pady=(0, 15))
        
        format_label = ttk.Label(format_frame, text="Select Quality:", style="Normal.TLabel")
        format_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.format_var = tk.StringVar()
        self.format_combo = ttk.Combobox(format_frame, textvariable=self.format_var, 
                                        state="readonly", width=30)
        self.format_combo.pack(side=tk.LEFT)
        
        # Download and reset buttons
        button_frame = ttk.Frame(self.video_container, style="Main.TFrame")
        button_frame.pack(pady=(0, 15))
        
        self.download_button = ttk.Button(button_frame, text="Download", style="Accent.TButton",
                                         command=self.download_video)
        self.download_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.reset_button = ttk.Button(button_frame, text="Reset", style="Secondary.TButton",
                                      command=self.reset_form)
        self.reset_button.pack(side=tk.LEFT)
        
        # Progress bar (initially hidden)
        self.progress_frame = ttk.Frame(main_container, style="Main.TFrame")
        self.progress_frame.pack(fill=tk.X, pady=(0, 15))
        self.progress_frame.pack_forget()  # Hide initially
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.pack(pady=(0, 5))
        
        # Status message
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(main_container, textvariable=self.status_var, 
                                     foreground="#666666", background=self.bg_color)
        self.status_label.pack(pady=(0, 15))
        
        # Footer
        footer_label = ttk.Label(main_container, 
                                text="By downloading this YouTube video, you agree to the Usage Guidelines.", 
                                foreground="#666666", background=self.bg_color)
        footer_label.pack(side=tk.BOTTOM, pady=(15, 0))
    
    def clear_placeholder(self, event):
        if self.url_entry.get() == "Paste a Youtube video URL here":
            self.url_entry.delete(0, tk.END)
    
    def restore_placeholder(self, event):
        if not self.url_entry.get():
            self.url_entry.insert(0, "Paste a Youtube video URL here")
    
    def is_valid_youtube_url(self, url):
        # More comprehensive regex pattern to match YouTube URLs
        youtube_regex = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)[\w-]+'
        return re.match(youtube_regex, url) is not None
    
    def clean_youtube_url(self, url):
        """Remove unnecessary parameters from YouTube URL"""
        video_id = None
        
        # Extract video ID based on URL format
        if "youtube.com/watch" in url:
            query = url.split("?")[1]
            params = query.split("&")
            for param in params:
                if param.startswith("v="):
                    video_id = param[2:]
                    break
        elif "youtu.be/" in url:
            path = url.split("youtu.be/")[1]
            video_id = path.split("?")[0]
        elif "youtube.com/shorts/" in url:
            path = url.split("youtube.com/shorts/")[1]
            video_id = path.split("?")[0]
        
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
        return url
    
    def search_video(self):
        url = self.url_var.get().strip()
        if url == "Paste a Youtube video URL here" or not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        
        if not self.is_valid_youtube_url(url):
            messagebox.showerror("Error", "Invalid YouTube URL")
            return
        
        # Clean the URL
        clean_url = self.clean_youtube_url(url)
        
        # Show status and hide previous results
        self.status_var.set("Fetching video information...")
        self.video_container.pack_forget()
        self.progress_frame.pack_forget()
        self.update_idletasks()
        
        # Fetch video in a separate thread to avoid freezing the UI
        threading.Thread(target=self._fetch_video_info, args=(clean_url,), daemon=True).start()
    
    def _fetch_video_info(self, url):
        try:
            # Use yt-dlp to get video info
            cmd = ["yt-dlp", "-J", url]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            video_info = json.loads(result.stdout)
            
            # Extract formats
            formats = []
            
            # Add video+audio formats
            for fmt in video_info.get('formats', []):
                if fmt.get('vcodec', 'none') != 'none' and fmt.get('acodec', 'none') != 'none':
                    resolution = fmt.get('height', 'unknown')
                    fps = fmt.get('fps', 'unknown')
                    ext = fmt.get('ext', 'unknown')
                    format_id = fmt.get('format_id', '')
                    
                    format_name = f"{resolution}p"
                    if fps:
                        format_name += f", {fps}fps"
                    format_name += f" ({ext.upper()})"
                    
                    formats.append({
                        'name': format_name,
                        'format_id': format_id,
                        'resolution': resolution,
                        'fps': fps,
                        'ext': ext,
                        'type': 'video'
                    })
            
            # Add audio-only formats
            for fmt in video_info.get('formats', []):
                if fmt.get('vcodec', 'none') == 'none' and fmt.get('acodec', 'none') != 'none':
                    abr = fmt.get('abr', 'unknown')
                    ext = fmt.get('ext', 'unknown')
                    format_id = fmt.get('format_id', '')
                    
                    format_name = f"Audio {abr}kbps ({ext.upper()})"
                    
                    formats.append({
                        'name': format_name,
                        'format_id': format_id,
                        'abr': abr,
                        'ext': ext,
                        'type': 'audio'
                    })
            
            # Sort formats by resolution (for video) or bitrate (for audio)
            video_formats = sorted([f for f in formats if f['type'] == 'video'], 
                                  key=lambda x: (x['resolution'] if isinstance(x['resolution'], int) else 0), 
                                  reverse=True)
            audio_formats = sorted([f for f in formats if f['type'] == 'audio'], 
                                  key=lambda x: (x['abr'] if isinstance(x['abr'], (int, float)) else 0), 
                                  reverse=True)
            
            # Combine sorted formats
            sorted_formats = video_formats + audio_formats
            
            # Update UI in the main thread
            self.master.after(0, lambda: self._update_video_info(video_info, sorted_formats))
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else "Failed to fetch video information"
            if "This video is unavailable" in error_msg:
                error_msg = "This video is unavailable. It might be private, age-restricted, or removed."
            elif "HTTP Error 429" in error_msg:
                error_msg = "HTTP Error 429: Too Many Requests. Please try again later."
            
            self.master.after(0, lambda: self._show_error(error_msg))
        except Exception as e:
            self.master.after(0, lambda: self._show_error(str(e)))
    
    def _update_video_info(self, video_info, formats):
        # Store video info and formats
        self.video_info = video_info
        self.formats = formats
        
        # Update video title
        title = video_info.get('title', 'Unknown Title')
        self.title_var.set(title)
        
        # Update format dropdown
        format_names = [fmt['name'] for fmt in formats]
        self.format_combo.config(values=format_names)
        if format_names:
            self.format_combo.current(0)
        
        # Load and display thumbnail
        thumbnail_url = video_info.get('thumbnail')
        if thumbnail_url:
            threading.Thread(target=self._load_thumbnail, args=(thumbnail_url,), daemon=True).start()
        
        # Show video container and update status
        self.video_container.pack()
        self.status_var.set("Video found. Select format and click Download.")
    
    def _load_thumbnail(self, url):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img_data = BytesIO(response.content)
                img = Image.open(img_data)
                
                # Resize to fit in the UI (maintain aspect ratio)
                img.thumbnail((320, 180))
                
                # Convert to PhotoImage for tkinter
                photo = ImageTk.PhotoImage(img)
                
                # Update thumbnail in main thread
                self.master.after(0, lambda: self._set_thumbnail(photo))
            else:
                raise Exception(f"Failed to load thumbnail: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"Error loading thumbnail: {e}")
            # Use a placeholder image instead
            self.master.after(0, self._use_placeholder_thumbnail)
    
    def _set_thumbnail(self, photo):
        # Store reference to prevent garbage collection
        self.thumbnail_image = photo
        self.thumbnail_label.config(image=photo)
    
    def _use_placeholder_thumbnail(self):
        # Create a placeholder image (gray rectangle)
        placeholder = Image.new('RGB', (320, 180), color=(200, 200, 200))
        photo = ImageTk.PhotoImage(placeholder)
        self._set_thumbnail(photo)
    
    def _show_error(self, message):
        self.status_var.set(f"Error: {message}")
        messagebox.showerror("Error", message)
    
    def download_video(self):
        if not self.formats:
            messagebox.showerror("Error", "No video selected")
            return
        
        selected_index = self.format_combo.current()
        if selected_index < 0 or selected_index >= len(self.formats):
            messagebox.showerror("Error", "Please select a format")
            return
        
        selected_format = self.formats[selected_index]
        
        # Ask for download location
        download_dir = filedialog.askdirectory(initialdir=self.download_path)
        if not download_dir:
            return  # User cancelled
        
        self.download_path = download_dir
        
        # Show progress bar and update status
        self.progress_frame.pack()
        self.progress_var.set(0)
        self.status_var.set("Starting download...")
        self.download_button.config(state="disabled")
        self.reset_button.config(state="disabled")
        
        # Start download in a separate thread
        threading.Thread(
            target=self._download_thread,
            args=(selected_format,),
            daemon=True
        ).start()
    
    def _download_thread(self, format_info):
        try:
            # Prepare filename template
            output_template = os.path.join(self.download_path, "%(title)s.%(ext)s")
            
            # Prepare command
            cmd = [
                "yt-dlp",
                "-f", format_info['format_id'],
                "-o", output_template,
                "--newline",  # Important for progress parsing
                self.video_info['webpage_url']
            ]
            
            # Start the download process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Track progress
            for line in process.stdout:
                if "[download]" in line and "%" in line:
                    try:
                        # Extract percentage
                        percent_str = line.split("%")[0].split()[-1]
                        percent = float(percent_str)
                        self.master.after(0, lambda p=percent: self._update_progress(p))
                    except (ValueError, IndexError):
                        pass
            
            # Wait for process to complete
            process.wait()
            
            # Check if download was successful
            if process.returncode == 0:
                self.master.after(0, self._handle_download_complete)
            else:
                raise Exception(f"Download failed with exit code {process.returncode}")
            
        except Exception as e:
            self.master.after(0, lambda: self._handle_download_error(str(e)))
    
    def _update_progress(self, percentage):
        self.progress_var.set(percentage)
        self.status_var.set(f"Downloading: {percentage:.1f}%")
    
    def _handle_download_error(self, message):
        self.status_var.set("Download failed")
        self.download_button.config(state="normal")
        self.reset_button.config(state="normal")
        messagebox.showerror("Download Error", message)
    
    def _handle_download_complete(self):
        self.progress_var.set(100)
        self.status_var.set("Download complete!")
        self.download_button.config(state="normal")
        self.reset_button.config(state="normal")
        
        messagebox.showinfo("Success", f"Video downloaded successfully to:\n{self.download_path}")
    
    def reset_form(self):
        # Clear form and hide video info
        self.url_var.set("Paste a Youtube video URL here")
        self.video_container.pack_forget()
        self.progress_frame.pack_forget()
        self.status_var.set("")
        
        # Reset state variables
        self.video_info = None
        self.thumbnail_image = None
        self.formats = []

def main():
    root = tk.Tk()
    root.configure(bg="#f5f0ff")  # Set background color
    app = YouTubeDownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()