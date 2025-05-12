import os
import pytube
from pytube import YouTube
from typing import Callable, Optional, Dict, List, Tuple

class YouTubeDownloader:
    def __init__(self):
        self.video = None
        self.stream = None
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
    
    def set_url(self, url: str) -> Tuple[bool, str, Optional[str]]:
        """
        Set the YouTube URL and fetch video information
        Returns: (success, message, thumbnail_url)
        """
        try:
            self.video = YouTube(url)
            # Set up progress callback
            self.video.register_on_progress_callback(self.on_progress_callback)
            self.video.register_on_complete_callback(self.on_complete_callback)
            return True, f"Video found: {self.video.title}", self.video.thumbnail_url
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    def get_available_streams(self) -> Dict[str, pytube.Stream]:
        """Get available video streams with resolutions"""
        if not self.video:
            return {}
        
        # Get progressive streams (with video and audio)
        streams = self.video.streams.filter(progressive=True).order_by('resolution')
        
        # Create a dictionary of resolution -> stream
        stream_dict = {}
        for stream in streams:
            if stream.resolution:
                stream_dict[f"{stream.resolution} ({stream.mime_type})"] = stream
        
        # Add audio-only options
        audio_streams = self.video.streams.filter(only_audio=True).order_by('abr')
        for stream in audio_streams:
            if stream.abr:
                stream_dict[f"Audio {stream.abr} ({stream.mime_type})"] = stream
        
        return stream_dict
    
    def set_download_path(self, path: str):
        """Set the download destination path"""
        self.download_path = path
    
    def download_video(self, stream_key: str, streams: Dict[str, pytube.Stream]) -> Tuple[bool, str]:
        """Download the selected video stream"""
        if not self.video:
            return False, "No video selected"
        
        if stream_key not in streams:
            return False, "Invalid stream selected"
        
        self.stream = streams[stream_key]
        
        try:
            # Create download directory if it doesn't exist
            os.makedirs(self.download_path, exist_ok=True)
            
            # Start download
            self.stream.download(output_path=self.download_path)
            return True, "Download started"
        except Exception as e:
            return False, f"Download error: {str(e)}"
    
    # Callback functions for progress tracking
    def on_progress_callback(self, stream, chunk, bytes_remaining):
        """Called when download progress changes"""
        self.progress_callback(stream, chunk, bytes_remaining)
    
    def on_complete_callback(self, stream, file_path):
        """Called when download completes"""
        self.complete_callback(stream, file_path)
    
    # These will be set from the GUI
    progress_callback = lambda *args: None
    complete_callback = lambda *args: None