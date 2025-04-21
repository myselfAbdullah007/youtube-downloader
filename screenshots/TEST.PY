import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import os
import time
import sys
import re

# Check for required packages at the start and install if needed
required_packages = ["pillow", "requests"]
missing_packages = []

for package in required_packages:
    try:
        if package == "pillow":
            __import__("PIL")
        else:
            __import__(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print(f"Installing missing packages: {', '.join(missing_packages)}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("Required packages installed. Restarting application...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        print(f"Failed to install packages: {e}")
        messagebox.showerror("Installation Error", 
                             f"Could not install required packages: {', '.join(missing_packages)}.\n"
                             f"Please install them manually using:\n"
                             f"pip install {' '.join(missing_packages)}")
        sys.exit(1)

# Now import the packages after ensuring they're installed
from PIL import Image, ImageTk
import requests
from io import BytesIO

class YoutubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube video Downloader")
        self.root.geometry("1000x900")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)

        # Set minimum window size
        self.root.minsize(700, 650)
        
        # Variables
        self.link = tk.StringVar()
        self.download_type = tk.StringVar(value="video")
        self.custom_filename = tk.StringVar()
        self.open_folder = tk.BooleanVar(value=True)
        self.download_quality = tk.StringVar(value="highest")
        self.status = tk.StringVar()
        self.thumbnail_url = ""
        self.video_title = ""
        self.video_duration = ""
        self.video_author = ""
        self.default_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        self.selected_folder = tk.StringVar(value=self.default_download_dir)
        self.playlist_mode = tk.BooleanVar(value=False)
        self.thumbnail_image = None  # Keep reference to prevent garbage collection
        
        # Create a style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure styles
        self.style.configure("TButton", 
                            font=("Helvetica", 12),
                            background="#2d2d42", 
                            foreground="#ffffff")
        
        self.style.configure("TCheckbutton", 
                            font=("Helvetica", 11),
                            background="#1e1e2e", 
                            foreground="#ffffff")
        
        self.style.configure("TLabel", 
                            font=("Helvetica", 12),
                            background="#1e1e2e", 
                            foreground="#ffffff")
        
        self.style.configure("TEntry", 
                            font=("Helvetica", 12),
                            fieldbackground="#2d2d42",
                            foreground="#ffffff")
        
        self.style.configure("TFrame", 
                            background="#1e1e2e")
        
        self.style.configure("Horizontal.TProgressbar", 
                            background="#5294e2",
                            troughcolor="#2d2d42")
        
        # Main frame
        self.main_frame = ttk.Frame(root, style="TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(self.main_frame, 
                              text="YOUTUBE DOWNLOADER", 
                              font=("Arial", 22, "bold"),
                              bg="#1e1e2e",
                              fg="#5294e2")
        title_label.pack(pady=10)
        
        # Input frame
        input_frame = ttk.Frame(self.main_frame, style="TFrame")
        input_frame.pack(fill=tk.X, pady=10)
        
        # URL input
        url_label = ttk.Label(input_frame, text="Video URL:", style="TLabel")
        url_label.pack(anchor="w")
        
        url_entry_frame = ttk.Frame(input_frame, style="TFrame")
        url_entry_frame.pack(fill=tk.X, pady=5)
        
        self.url_entry = ttk.Entry(url_entry_frame, textvariable=self.link, font=("Helvetica", 12), width=60)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        parse_button = ttk.Button(url_entry_frame, text="Parse", command=self.parse_video_info)
        parse_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Thumbnail and info frame
        self.info_frame = ttk.Frame(self.main_frame, style="TFrame")
        self.info_frame.pack(fill=tk.X, pady=10)
        
        # Placeholder for thumbnail
        self.thumbnail_frame = ttk.Frame(self.info_frame, style="TFrame", width=240, height=135)
        self.thumbnail_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # Placeholder thumbnail
        self.thumbnail_canvas = tk.Canvas(self.thumbnail_frame, width=240, height=135, bg="#2d2d42", highlightthickness=0)
        self.thumbnail_canvas.pack()
        self.thumbnail_canvas.create_text(120, 67, text="Thumbnail Preview", fill="#ffffff", font=("Helvetica", 12))
        
        # Video info frame
        self.video_info_frame = ttk.Frame(self.info_frame, style="TFrame")
        self.video_info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.title_label = ttk.Label(self.video_info_frame, text="Title: Not available", style="TLabel", wraplength=400)
        self.title_label.pack(anchor="w", pady=2)
        
        self.author_label = ttk.Label(self.video_info_frame, text="Channel: Not available", style="TLabel")
        self.author_label.pack(anchor="w", pady=2)
        
        self.duration_label = ttk.Label(self.video_info_frame, text="Duration: Not available", style="TLabel")
        self.duration_label.pack(anchor="w", pady=2)
        
        # Options frame
        options_frame = ttk.Frame(self.main_frame, style="TFrame")
        options_frame.pack(fill=tk.X, pady=10)
        
        # Left options
        left_options = ttk.Frame(options_frame, style="TFrame")
        left_options.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Download type
        ttk.Label(left_options, text="Download Type:", style="TLabel").pack(anchor="w", pady=2)
        type_frame = ttk.Frame(left_options, style="TFrame")
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(type_frame, text="Video", variable=self.download_type, value="video").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(type_frame, text="Audio Only", variable=self.download_type, value="audio").pack(side=tk.LEFT)
        
        # Quality selection
        ttk.Label(left_options, text="Quality:", style="TLabel").pack(anchor="w", pady=2)
        quality_frame = ttk.Frame(left_options, style="TFrame")
        quality_frame.pack(fill=tk.X, pady=5)
        
        quality_values = ["highest", "1080p", "720p", "480p", "360p", "lowest"]
        quality_combo = ttk.Combobox(quality_frame, textvariable=self.download_quality, values=quality_values, state="readonly", width=12)
        quality_combo.pack(side=tk.LEFT)
        
        # Right options
        right_options = ttk.Frame(options_frame, style="TFrame")
        right_options.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Custom filename
        ttk.Label(right_options, text="Custom Filename (optional):", style="TLabel").pack(anchor="w", pady=2)
        self.filename_entry = ttk.Entry(right_options, textvariable=self.custom_filename, width=30)
        self.filename_entry.pack(fill=tk.X, pady=5)
        
        # Playlist option
        playlist_check = ttk.Checkbutton(right_options, text="Playlist Mode", variable=self.playlist_mode)
        playlist_check.pack(anchor="w", pady=5)
        
        # Open folder option
        open_folder_check = ttk.Checkbutton(right_options, text="Open folder after download", variable=self.open_folder)
        open_folder_check.pack(anchor="w", pady=5)
        
        # Download location frame
        location_frame = ttk.Frame(self.main_frame, style="TFrame")
        location_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(location_frame, text="Download Location:", style="TLabel").pack(anchor="w")
        
        location_entry_frame = ttk.Frame(location_frame, style="TFrame")
        location_entry_frame.pack(fill=tk.X, pady=5)
        
        self.location_entry = ttk.Entry(location_entry_frame, textvariable=self.selected_folder, width=60)
        self.location_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_button = ttk.Button(location_entry_frame, text="Browse", command=self.browse_folder)
        browse_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Download button
        self.download_button = ttk.Button(
            self.main_frame, 
            text="DOWNLOAD", 
            command=self.download_video,
            style="TButton",
        )
        self.download_button.pack(fill=tk.X, pady=15)
        
        # Progress frame
        progress_frame = ttk.Frame(self.main_frame, style="TFrame")
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            orient="horizontal", 
            mode="determinate",
            style="Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X)
        
        # Status labels
        status_frame = ttk.Frame(self.main_frame, style="TFrame")
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(
            status_frame, 
            textvariable=self.status, 
            style="TLabel",
            font=("Helvetica", 12, "italic")
        )
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_label = ttk.Label(
            status_frame, 
            text="", 
            style="TLabel",
            font=("Helvetica", 12)
        )
        self.progress_label.pack(side=tk.RIGHT)
        
        # Stats frame
        self.stats_frame = ttk.Frame(self.main_frame, style="TFrame")
        self.stats_frame.pack(fill=tk.X, pady=10)
        
        self.download_stats = ttk.Label(self.stats_frame, text="", style="TLabel")
        self.download_stats.pack(anchor="w")
        
        # Add separator before footer
        ttk.Separator(self.main_frame, orient="horizontal").pack(fill=tk.X, pady=10)
        
        # Footer with background
        footer_frame = ttk.Frame(self.main_frame, style="Footer.TFrame")
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        # Configure footer style
        self.style.configure("Footer.TFrame", 
                           background="#2d2d42",  # Darker background for footer
                           relief="raised")
        
                
        footer_center = ttk.Label(
            footer_frame,
            text="© 2025 All Rights Reserved",
            style="Footer.TLabel",
            font=("Helvetica", 10)
        )
        footer_center.pack(expand=True, pady=5)
        
        footer_right = ttk.Label(
            footer_frame,
            text="Made by github@myselfabdullah007",
            style="Footer.TLabel",
            font=("Helvetica", 14)
        )
        footer_right.pack(expand=True, padx=10, pady=5)
        
        # Configure footer label style
        self.style.configure("Footer.TLabel",
                           background="#2d2d42",  # Match footer background
                           foreground="#ffffff")  # White text
        
        # Check for yt-dlp installation
        self.check_yt_dlp()
        
        # Bind events
        self.root.bind("<Return>", lambda event: self.parse_video_info())
        
    def check_yt_dlp(self):
        """Check if yt-dlp is installed and install it if necessary"""
        try:
            result = subprocess.run(["yt-dlp", "--version"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
            if result.returncode == 0:
                version = result.stdout.decode().strip()
                self.status.set(f"Ready (yt-dlp {version})")
            else:
                self.install_yt_dlp()
        except FileNotFoundError:
            self.install_yt_dlp()
    
    def install_yt_dlp(self):
        """Install yt-dlp using pip"""
        self.status.set("Installing yt-dlp...")
        
        def install():
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
                self.root.after(0, lambda: self.status.set(" Ready!"))
            except Exception as e:
                self.root.after(0, lambda: self.status.set("Error installing yt-dlp"))
                self.root.after(0, lambda: messagebox.showerror(
                    "Installation Error", 
                    f"Failed to install yt-dlp: {e}\n\n"
                    "Please install it manually using:\n"
                    "pip install yt-dlp"
                ))
        
        threading.Thread(target=install).start()
    
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.selected_folder.get())
        if folder:
            self.selected_folder.set(folder)
    
    def parse_video_info(self):
        url = self.link.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        
        self.status.set("Fetching video information...")
        self.progress_label.config(text="⏳ Please wait...")
        
        def fetch_info():
            try:
                # Determine the correct path for yt-dlp (either system-wide or python module)
                try:
                    # First try system-wide yt-dlp
                    process = subprocess.run(["yt-dlp", "--version"], 
                                            stdout=subprocess.PIPE, 
                                            stderr=subprocess.PIPE,
                                            check=True)
                    yt_dlp_cmd = ["yt-dlp"]
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Fall back to module version
                    yt_dlp_cmd = [sys.executable, "-m", "yt_dlp"]
                
                command = yt_dlp_cmd + [
                    "--dump-json",
                    "--no-playlist",
                    url
                ]
                
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                video_info = json.loads(result.stdout)
                
                # Get video details
                self.video_title = video_info.get('title', 'Unknown Title')
                self.video_author = video_info.get('uploader', 'Unknown Channel')
                
                # Format duration
                duration_seconds = video_info.get('duration', 0)
                minutes, seconds = divmod(int(duration_seconds), 60)
                hours, minutes = divmod(minutes, 60)
                
                if hours > 0:
                    self.video_duration = f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    self.video_duration = f"{minutes}:{seconds:02d}"
                
                # Get thumbnail
                thumbnails = video_info.get('thumbnails', [])
                if thumbnails:
                    # Try to get a medium-resolution thumbnail
                    for thumb in thumbnails:
                        if thumb.get('height', 0) >= 180 and thumb.get('height', 0) <= 360:
                            self.thumbnail_url = thumb.get('url')
                            break
                    
                    # If no medium thumbnail found, use the first one
                    if not self.thumbnail_url and thumbnails:
                        self.thumbnail_url = thumbnails[-1].get('url')
                
                # Update UI
                self.root.after(0, self.update_video_info)
                
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Could not parse video info:\n{e}"))
                self.root.after(0, lambda: self.status.set("Failed to fetch video information"))
                self.root.after(0, lambda: self.progress_label.config(text=""))
            except json.JSONDecodeError:
                self.root.after(0, lambda: messagebox.showerror("Error", "Failed to parse video information. Invalid response format."))
                self.root.after(0, lambda: self.status.set("Failed to parse video information"))
                self.root.after(0, lambda: self.progress_label.config(text=""))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred:\n{e}"))
                self.root.after(0, lambda: self.status.set("Error processing video information"))
                self.root.after(0, lambda: self.progress_label.config(text=""))
        
        threading.Thread(target=fetch_info).start()
    
    def update_video_info(self):
        # Update labels
        self.title_label.config(text=f"Title: {self.video_title}")
        self.author_label.config(text=f"Channel: {self.video_author}")
        self.duration_label.config(text=f"Duration: {self.video_duration}")
        
        # Update thumbnail if available
        if self.thumbnail_url:
            try:
                response = requests.get(self.thumbnail_url)
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img = img.resize((240, 135), Image.LANCZOS)
                self.thumbnail_image = ImageTk.PhotoImage(img)
                
                # Update canvas with new image
                self.thumbnail_canvas.delete("all")
                self.thumbnail_canvas.create_image(0, 0, anchor=tk.NW, image=self.thumbnail_image)
            except Exception as e:
                print(f"Error loading thumbnail: {e}")
                # If thumbnail fails to load, display error text
                self.thumbnail_canvas.delete("all")
                self.thumbnail_canvas.create_text(120, 67, text="Thumbnail Unavailable", fill="#ffffff", font=("Helvetica", 12))
        
        # Suggest filename based on video title
        if not self.custom_filename.get() and self.video_title:
            # Replace invalid filename characters
            safe_title = re.sub(r'[\\/*?:"<>|]', "", self.video_title)
            self.custom_filename.set(safe_title)
        
        self.status.set("Video information loaded successfully")
        self.progress_label.config(text="✅")
    
    def download_video(self):
        url = self.link.get().strip()
        filename_input = self.custom_filename.get().strip()
        folder = self.selected_folder.get()
        
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
            
        if not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid download folder")
            return
        
        # Reset progress
        self.progress_bar["value"] = 0
        self.status.set("Preparing download...")
        self.progress_label.config(text="⏳")
        
        # Prepare command
        output_template = "%(title)s.%(ext)s"
        if filename_input:
            output_template = filename_input + ".%(ext)s"
        
        # Determine the correct path for yt-dlp (either system-wide or python module)
        try:
            subprocess.run(["yt-dlp", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            command = ["yt-dlp"]
        except (subprocess.CalledProcessError, FileNotFoundError):
            command = [sys.executable, "-m", "yt_dlp"]
        
        # Add progress hooks for UI updates
        command.extend([
            "--newline",
            "--progress",
            "-o", os.path.join(folder, output_template),
        ])
        
        # Handle playlist mode
        if self.playlist_mode.get():
            if "playlist" in url.lower() or "list=" in url:
                command.append("--yes-playlist")
            else:
                messagebox.showwarning("Warning", "URL doesn't appear to be a playlist but playlist mode is selected")
        else:
            command.append("--no-playlist")
        
        # Format selection based on type and quality
        if self.download_type.get() == "video":
            quality = self.download_quality.get()
            
            if quality == "highest":
                command.extend([
                    "-f", "bv*+ba/best",
                    "--merge-output-format", "mp4",
                ])
            elif quality == "lowest":
                command.extend([
                    "-f", "worstvideo+worstaudio/worst",
                    "--merge-output-format", "mp4",
                ])
            else:
                # Extract numeric value from quality string (e.g., "720p" -> 720)
                height = "".join(filter(str.isdigit, quality))
                command.extend([
                    "-f", f"bv*[height<={height}]+ba/best[height<={height}]",
                    "--merge-output-format", "mp4",
                ])
        elif self.download_type.get() == "audio":
            command.extend([
                "-f", "bestaudio",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",
            ])
        
        # Add URL
        command.append(url)
        
        # Download stats
        self.start_time = time.time()
        self.download_size = 0
        self.downloaded_bytes = 0
        
        def run_command():
            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                downloading = False
                eta_found = False
                file_size_found = False
                speed_info = ""
                eta_info = ""
                
                for line in process.stdout:
                    line = line.strip()
                    
                    # Check if download has started
                    if "[download]" in line and "Destination:" in line:
                        downloading = True
                        self.root.after(0, lambda: self.status.set("Downloading..."))
                    
                    # Look for progress information
                    if downloading and "[download]" in line and "%" in line:
                        try:
                            # Parse progress percentage
                            percent_str = line.split("%")[0].split()[-1].strip()
                            percent = float(percent_str)
                            
                            # Update progress bar
                            self.root.after(0, lambda p=percent: self.progress_bar.configure(value=p))
                            
                            # Parse download speed if available
                            if "at" in line and "/s" in line:
                                speed_section = line.split("at")[1].split(",")[0].strip()
                                speed_info = speed_section
                            
                            # Parse ETA if available
                            if "ETA" in line:
                                eta_section = line.split("ETA")[1].strip()
                                eta_info = f"ETA: {eta_section}"
                                eta_found = True
                            
                            # Parse file size if available and not yet found
                            if not file_size_found and "of" in line and ("MiB" in line or "KiB" in line):
                                size_section = line.split("of")[1].split(",")[0].strip()
                                self.download_size = size_section
                                file_size_found = True
                            
                            # Update status with speed and ETA
                            progress_text = f"{speed_info}"
                            if eta_found:
                                progress_text += f" | {eta_info}"
                            
                            self.root.after(0, lambda t=progress_text: self.progress_label.config(text=t))
                            
                        except Exception as e:
                            print(f"Error parsing progress: {e}")
                
                process.wait()
                
                if process.returncode == 0:
                    elapsed_time = time.time() - self.start_time
                    minutes, seconds = divmod(int(elapsed_time), 60)
                    time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
                    
                    success_message = "✅ Download completed!"
                    self.root.after(0, lambda: self.status.set(success_message))
                    self.root.after(0, lambda: self.progress_label.config(text=""))
                    self.root.after(0, lambda: self.progress_bar.configure(value=100))
                    self.root.after(0, lambda: self.download_stats.config(
                        text=f"Download completed in {time_str} | Size: {self.download_size}"
                    ))
                    
                    if self.open_folder.get():
                        if os.name == 'nt':  # Windows
                            os.startfile(folder)
                        elif os.name == 'posix':  # Linux, macOS
                            os.system(f'xdg-open "{folder}"')
                    
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Download completed!"))
                else:
                    self.root.after(0, lambda: self.status.set("❌ Download failed."))
                    self.root.after(0, lambda: self.progress_label.config(text=""))
                    self.root.after(0, lambda: messagebox.showerror("Error", "Download failed. Check terminal for details."))
            
            except Exception as e:
                self.root.after(0, lambda: self.status.set("❌ Download failed."))
                self.root.after(0, lambda: self.progress_label.config(text=""))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Download failed:\n{e}"))
        
        threading.Thread(target=run_command).start()

if __name__ == "__main__":
    try:
        # This import will either work after the packages are installed
        # or will trigger the installation process at the start
        import json
        
        root = tk.Tk()
        app = YoutubeDownloader(root)
        root.mainloop()
    except Exception as e:
        print(f"Startup error: {e}")
        messagebox.showerror("Startup Error", f"An error occurred during startup:\n{e}")