import os
import sys
import time
import base64
import subprocess
from pathlib import Path

import requests
from openai import OpenAI


# ============================================================
# CONFIGURATION
# ============================================================

META_PAGE_ID = os.environ.get("META_PAGE_ID")
META_PAGE_ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

GRAPH_VERSION = "v26.0"

OUTPUT_DIR = Path("generated_reel")
OUTPUT_DIR.mkdir(exist_ok=True)

IMAGE_FILE = OUTPUT_DIR / "gita_reel.jpg"
VIDEO_FILE = OUTPUT_DIR / "gita_reel.mp4"


# ============================================================
# VALIDATE ENVIRONMENT
# ============================================================

def check_environment():
    missing = []

    if not META_PAGE_ID:
        missing.append("META_PAGE_ID")

    if not META_PAGE_ACCESS_TOKEN:
        missing.append("META_PAGE_ACCESS_TOKEN")

    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")

    if missing:
        print("ERROR: Missing GitHub Secrets:")
        for item in missing:
            print(f"  - {item}")
        sys.exit(1)

    print("Environment variables OK")
    print(f"Facebook Page ID: {META_PAGE_ID}")


# ============================================================
# GENERATE ODIA CONTENT
# ============================================================

def generate_content():
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = """
Create content for a 20-second Facebook Reel for an Odia
Bhagavad Gita spiritual page.

Return ONLY valid JSON in this format:

{
  "title": "...",
  "voice_text": "...",
  "caption": "...",
  "hashtags": "..."
}

Requirements:

- Language: Odia
- Spiritual and positive
- Based on Bhagavad Gita teachings
- Do not invent a direct quotation from Krishna
- Keep voice_text suitable for approximately 20 seconds
- Caption should be engaging but not clickbait
- Hashtags should include relevant Odia and Bhagavad Gita hashtags
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You create accurate, respectful Odia Bhagavad Gita social-media content."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.8
    )

    content = response.choices[0].message.content.strip()

    # Remove markdown JSON fences if the model adds them
    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    import json

    try:
        data = json.loads(content)
    except Exception as e:
        print("Could not parse OpenAI JSON response:")
        print(content)
        raise e

    print("\nGenerated Reel content:")
    print("Title:", data["title"])
    print("Voice:", data["voice_text"])
    print("Caption:", data["caption"])
    print("Hashtags:", data["hashtags"])

    return data


# ============================================================
# GENERATE VERTICAL IMAGE
# ============================================================

def generate_image(content):
    client = OpenAI(api_key=OPENAI_API_KEY)

    image_prompt = f"""
Create a beautiful cinematic vertical 9:16 devotional image
for an Odia Bhagavad Gita Facebook Reel.

Theme:
{content["title"]}

Visual concept:
Lord Krishna and Arjuna in a majestic Kurukshetra setting,
golden sunrise, divine atmosphere, traditional Indian
spiritual art, realistic cinematic lighting, peaceful and
inspiring mood.

Composition:
- Vertical 9:16
- Krishna clearly visible
- Arjuna and chariot visible
- Kurukshetra battlefield in the background
- Rich devotional atmosphere
- No modern objects
- No logos
- No watermark
- NO TEXT anywhere in the image
"""

    print("\nGenerating vertical image...")

    result = client.images.generate(
        model="gpt-image-1",
        prompt=image_prompt,
        size="1024x1536"
    )

    image_base64 = result.data[0].b64_json

    if not image_base64:
        raise RuntimeError("OpenAI did not return image data.")

    image_bytes = base64.b64decode(image_base64)

    IMAGE_FILE.write_bytes(image_bytes)

    print(f"Image created: {IMAGE_FILE}")
    print(f"Image size: {len(image_bytes)} bytes")


# ============================================================
# CREATE 20 SECOND VIDEO
# ============================================================

def create_video():
    print("\nCreating 20-second Reel with FFmpeg...")

    if not IMAGE_FILE.exists():
        raise RuntimeError("Generated image does not exist.")

    command = [
        "ffmpeg",
        "-y",

        "-loop",
        "1",

        "-i",
        str(IMAGE_FILE),

        "-t",
        "20",

        "-vf",
        (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "zoompan="
            "z='min(zoom+0.0005,1.08)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=1:"
            "s=1080x1920:"
            "fps=30"
        ),

        "-r",
        "30",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        "-an",

        str(VIDEO_FILE)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        raise RuntimeError("FFmpeg failed to create the Reel.")

    if not VIDEO_FILE.exists():
        raise RuntimeError("Video file was not created.")

    size = VIDEO_FILE.stat().st_size

    print(f"Video created: {VIDEO_FILE}")
    print(f"Video size: {size} bytes")


# ============================================================
# FACEBOOK REEL - START UPLOAD
# ============================================================

def start_reel_upload():

    url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_VERSION}/"
        f"{META_PAGE_ID}/video_reels"
    )

    params = {
        "access_token": META_PAGE_ACCESS_TOKEN,
        "upload_phase": "start",
        "file_size": str(VIDEO_FILE.stat().st_size)
    }

    print("\nStarting Facebook Reel upload...")

    response = requests.post(
        url,
        params=params,
        timeout=60
    )

    print("Facebook start response:", response.status_code)
    print(response.text)

    if response.status_code != 200:
        raise RuntimeError(
            f"Facebook Reel start failed: "
            f"{response.status_code} {response.text}"
        )

    data = response.json()

    video_id = data.get("video_id")
    upload_url = data.get("upload_url")

    if not video_id:
        raise RuntimeError("Facebook did not return video_id.")

    if not upload_url:
        raise RuntimeError("Facebook did not return upload_url.")

    return video_id, upload_url


# ============================================================
# FACEBOOK REEL - TRANSFER VIDEO
# ============================================================

def transfer_video(video_id, upload_url):

    print("\nUploading MP4 to Facebook...")

    file_size = VIDEO_FILE.stat().st_size

    headers = {
        "Authorization": f"OAuth {META_PAGE_ACCESS_TOKEN}",
        "offset": "0",
        "file_size": str(file_size)
    }

    with open(VIDEO_FILE, "rb") as video_file:

        response = requests.post(
            upload_url,
            headers=headers,
            data=video_file,
            timeout=300
        )

    print("Facebook transfer response:", response.status_code)
    print(response.text)

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Facebook video transfer failed: "
            f"{response.status_code} {response.text}"
        )

    return True


# ============================================================
# FACEBOOK REEL - PUBLISH
# ============================================================

def publish_reel(video_id, content):

    url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_VERSION}/"
        f"{META_PAGE_ID}/video_reels"
    )

    description = (
        content["caption"]
        + "\n\n"
        + content["hashtags"]
    )

    params = {
        "access_token": META_PAGE_ACCESS_TOKEN,
        "upload_phase": "finish",
        "video_id": video_id,
        "video_state": "PUBLISHED",
        "description": description
    }

    print("\nPublishing Facebook Reel...")

    response = requests.post(
        url,
        params=params,
        timeout=120
    )

    print("Facebook publish response:", response.status_code)
    print(response.text)

    if response.status_code != 200:
        raise RuntimeError(
            f"Facebook Reel publish failed: "
            f"{response.status_code} {response.text}"
        )

    data = response.json()

    print("\n==========================================")
    print("SUCCESS: Facebook Reel published")
    print("Video ID:", video_id)
    print("==========================================")

    return data


# ============================================================
# MAIN
# ============================================================

def main():

    print("==========================================")
    print(" ODISHA BHAGABAT GITA - AUTO REEL")
    print("==========================================")

    check_environment()

    # 1. Generate Odia content
    content = generate_content()

    # 2. Generate devotional vertical image
    generate_image(content)

    # 3. Convert image into 20-second MP4
    create_video()

    # 4. Start Meta Reel upload
    video_id, upload_url = start_reel_upload()

    # 5. Transfer MP4
    transfer_video(video_id, upload_url)

    # Small delay before publishing
    print("\nWaiting for Facebook processing...")
    time.sleep(5)

    # 6. Publish Reel
    publish_reel(video_id, content)


if __name__ == "__main__":
    main()
