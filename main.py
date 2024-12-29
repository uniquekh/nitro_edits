import os
import re
import string
import time
import pickle
import moviepy.video.fx.all as vfx
import moviepy.config as mpy_config
from instaloader import Instaloader, Post
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from pyrogram import Client

# Configure ImageMagick binary
mpy_config.IMAGEMAGICK_BINARY = "/usr/bin/convert"  # Update this path accordingly for Linux

# Scopes for YouTube API
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
L = Instaloader()

# Telegram bot details
API_ID = 24271143
API_HASH = '27be842cb506de9b5520146dfd0ba299'
BOT_TOKEN = '7462696027:AAGXCFukbzCQB7pRD-1L2TPo9-BY05QT6sQ'
CHAT_ID = 5702090016

# Initialize Telegram client
app = Client("youtube_uploader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# -------- Helper Functions --------

def sanitize_filename(filename):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in filename if c in valid_chars).strip()

def linkdownload(link):
    id_pattern = r"(/p/|/reel/)([a-zA-Z0-9_-]+)/"
    match = re.search(id_pattern, link)

    if match:
        id = match.group(2)
        post = Post.from_shortcode(L.context, id)
        print(f"{post} downloading...")

        caption = post.caption or "No caption available"
        print(f"Post caption: {caption}")

        first_line = caption.split('\n')[0]
        limited_caption = ' '.join(first_line.split()[:8])
        sanitized_caption = sanitize_filename(limited_caption)
        
        download_folder = "downloads"
        os.makedirs(download_folder, exist_ok=True)

        L.download_post(post, target=download_folder)
        
        video_files = [file for file in os.listdir(download_folder) if file.endswith('.mp4')]

        if video_files:
            video_path = os.path.join(download_folder, video_files[0])
            new_video_name = f"{sanitized_caption}.mp4"
            new_video_path = os.path.join(download_folder, new_video_name)

            os.rename(video_path, new_video_path)
            print(f"Downloaded video saved at: {new_video_path}")
            return new_video_path, sanitized_caption
        else:
            return "", "Error: No video file found."
    else:
        return "", "Invalid link!"

def add_watermark(video_path, watermark_image="e-removebg-preview.png", transparency=0.8, width=600, height=180, position=('center', 50)):
    watermarked_folder = "watermarked"
    os.makedirs(watermarked_folder, exist_ok=True)
    output_path = os.path.join(watermarked_folder, f"watermarked_{os.path.basename(video_path)}")

    try:
        video = VideoFileClip(video_path).fx(vfx.lum_contrast, lum=0.1, contrast=0.2)
        watermark = ImageClip(watermark_image).resize(width=width, height=height).set_opacity(transparency)
        watermark = watermark.set_position((position[0], video.h - height - position[1])).set_duration(video.duration)
        final_video = CompositeVideoClip([video, watermark]).set_audio(video.audio)
        final_video = final_video.fx(vfx.fadeout, 1)

        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        print(f"Watermarked video saved to: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error adding watermark: {e}")
        return None

def authenticate_youtube():
    creds = None
    if os.path.exists("nitro_token.pickle"):
        with open("nitro_token.pickle", "rb") as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("Token is invalid or expired. Please refresh the token.")
    
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(file_path, title, description, tags, category_id="2", privacy_status="public"):
    youtube = authenticate_youtube()
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {"privacyStatus": privacy_status}
    }
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    try:
        response = request.execute()
        print(f"Video uploaded successfully! Video ID: {response['id']}")
        send_telegram_message(f"Video uploaded successfully! Video ID: {response['id']}")
    except HttpError as error:
        print(f"An error occurred: {error}")
        send_telegram_message(f"An error occurred while uploading video: {error}")

def send_telegram_message(message):
    with app:
        app.send_message(chat_id=CHAT_ID, text=message)

def cleanup_downloads():
    download_folder = "downloads"
    if os.path.exists(download_folder):
        for file in os.listdir(download_folder):
            file_path = os.path.join(download_folder, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")

# -------- Main Function --------
if __name__ == "__main__":
    print("Instagram Video Downloader -> Watermark Adder -> YouTube Uploader")

    with open("links.txt", "r") as file:
        links = file.readlines()

    while True:
        for link in links:
            link = link.strip()
            if link:
                video_path, video_title = linkdownload(link)

                if video_path.endswith(".mp4"):
                    watermarked_path = add_watermark(video_path)
                    if watermarked_path:
                        upload_to_youtube(
                            file_path=watermarked_path,
                            title=video_title,
                            description='''🔥 The thrill of speed. 🏁 Stunning car edits. ✨ Automotive passion.
🚘 Supercars | 🛠️ Custom builds | 🌟 Epic rides
🌟 Your gateway to the world of horsepower. 🏎️ Stay driven!

Follow for breathtaking car content and adrenaline-fueled videos! 🚀''',
                            tags = ["shorts", "car edits", "supercars", "cars", "car videos", "modified cars", "luxury cars", "fast cars", "ytshorts", "reels", "reel", "trendingshorts", "trending", "viral", "car passion", "auto lovers", "car trends", "hypercars", "nitroedits", "speed"],
                            category_id="2",
                            privacy_status="public"
                        )
                        cleanup_downloads()
                    else:
                        print("Failed to add watermark.")
                else:
                    print(f"Download error: {video_title}")

        print("Waiting for 4 hours before uploading the next video...")
        time.sleep(4 * 3600)  # Wait for 4 hours
