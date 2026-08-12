import os
import sys
import json
import time
import base64
import subprocess
from pathlib import Path

import requests
from openai import OpenAI


# ============================================================
# CONFIGURATION
# ============================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
META_PAGE_ID = os.getenv("META_PAGE_ID")
META_PAGE_ACCESS_TOKEN = os.getenv("META_PAGE_ACCESS_TOKEN")

OPENAI_TEXT_MODEL = "gpt-4.1-mini"
OPENAI_IMAGE_MODEL = "gpt-image-1"
OPENAI_TTS_MODEL = "gpt-4o-mini-tts"

GRAPH_API_VERSION = "v26.0"

VIDEO_DURATION = 20
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_FILE = OUTPUT_DIR / "gita_reel.png"
AUDIO_FILE = OUTPUT_DIR / "gita_voice.mp3"
VIDEO_FILE = OUTPUT_DIR / "gita_reel.mp4"

CURRENT_CONTENT = {}


# ============================================================
# OPENAI CLIENT
# ============================================================

client = None


# ============================================================
# VALIDATE ENVIRONMENT
# ============================================================

def validate_environment():

    print()
    print("=" * 70)
    print("Checking environment...")
    print("=" * 70)

    missing = []

    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")

    if not META_PAGE_ID:
        missing.append("META_PAGE_ID")

    if not META_PAGE_ACCESS_TOKEN:
        missing.append("META_PAGE_ACCESS_TOKEN")

    if missing:

        print("\nERROR: Missing GitHub Actions secrets:")

        for item in missing:
            print(f"  - {item}")

        print(
            "\nGo to GitHub → Settings → "
            "Secrets and variables → Actions"
        )

        sys.exit(1)

    print("OPENAI_API_KEY: OK")
    print(f"META_PAGE_ID: {META_PAGE_ID}")
    print("META_PAGE_ACCESS_TOKEN: OK")


# ============================================================
# GENERATE ODIA CONTENT
# ============================================================

def generate_content():

    print()
    print("=" * 70)
    print("Generating Odia Bhagavad Gita Reel content...")
    print("=" * 70)

    prompt = """
Create content for a 20-second Facebook Reel for an Odia
Bhagavad Gita spiritual page.

The content must be written in natural, grammatically correct Odia.

Return ONLY valid JSON using this exact structure:

{
  "title": "...",
  "message": "...",
  "voice_text": "...",
  "caption": "...",
  "hashtags": ["...", "...", "..."]
}

Requirements:

TITLE:
- Short and attractive.
- Written in Odia.

MESSAGE:
- One concise Bhagavad Gita-inspired life teaching.
- Positive and devotional.
- Natural Odia.

VOICE_TEXT:
- Approximately 35-50 Odia words.
- Suitable for approximately 15-20 seconds of narration.
- Easy to pronounce.
- Calm and devotional.
- Do not use emojis in the narration.
- Do not use English words unnecessarily.

CAPTION:
- Short Facebook caption.
- Natural Odia.
- Suitable for the Srimad Bhagabat Gita page.

HASHTAGS:
- 5-8 relevant hashtags.
- Use Odia hashtags where appropriate.

IMPORTANT:
- Do not invent a direct quotation from Lord Krishna.
- Do not claim an invented sentence is an exact Bhagavad Gita verse.
- Do not make political or controversial claims.
- Keep the content respectful and devotional.
"""

    try:

        response = client.chat.completions.create(
            model=OPENAI_TEXT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert Odia spiritual content writer "
                        "specializing in respectful Bhagavad Gita content."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8
        )

    except Exception as error:

        print("\nERROR generating content:")
        print(str(error))

        sys.exit(1)

    text = response.choices[0].message.content.strip()

    # Remove Markdown JSON fences if returned
    if text.startswith("```"):

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        text = text.strip()

    try:

        content = json.loads(text)

    except json.JSONDecodeError:

        print("\nERROR: OpenAI returned invalid JSON:")
        print(text)

        sys.exit(1)

    required_fields = [
        "title",
        "message",
        "voice_text",
        "caption",
        "hashtags"
    ]

    for field in required_fields:

        if field not in content:

            print(
                f"\nERROR: Missing content field: {field}"
            )

            sys.exit(1)

    print()
    print("Title:")
    print(content["title"])

    print()
    print("Message:")
    print(content["message"])

    print()
    print("Voice narration:")
    print(content["voice_text"])

    print()
    print("Caption:")
    print(content["caption"])

    print()
    print("Hashtags:")
    print(" ".join(content["hashtags"]))

    return content


# ============================================================
# GENERATE VERTICAL IMAGE
# ============================================================

def generate_image(content):

    print()
    print("=" * 70)
    print("Generating vertical devotional image...")
    print("=" * 70)

    image_prompt = f"""
Create a beautiful cinematic devotional image for a
20-second Facebook Reel for an Odia Bhagavad Gita page.

Title:
{content["title"]}

Theme:
{content["message"]}

Scene:

Lord Krishna in a majestic Kurukshetra-inspired environment,
with a peaceful divine expression.

Include:

- Lord Krishna
- Traditional Indian clothing
- Beautiful spiritual atmosphere
- Golden sunrise
- Soft divine light
- Ancient Indian environment
- Subtle Kurukshetra battlefield atmosphere
- Cinematic depth
- Premium devotional artwork
- Realistic detailed visual quality

Composition:

- Vertical 9:16
- Designed for Facebook Reels
- Main subject centered
- Leave some visual breathing space
- Cinematic camera perspective

IMPORTANT:

- No text
- No letters
- No captions
- No subtitles
- No watermark
- No logo
- No Facebook interface
- No modern objects
- Respectful depiction of Lord Krishna
"""

    try:

        result = client.images.generate(
            model=OPENAI_IMAGE_MODEL,
            prompt=image_prompt,
            size="1024x1536"
        )

    except Exception as error:

        print()
        print("ERROR: OpenAI image generation failed:")
        print(str(error))

        sys.exit(1)

    if not result.data:

        print(
            "\nERROR: OpenAI returned no image data."
        )

        sys.exit(1)

    image_data = result.data[0]

    # ========================================================
    # IMPORTANT:
    #
    # GPT Image models return Base64 image data.
    #
    # DO NOT USE:
    #
    # image_data.url
    #
    # ========================================================

    image_b64 = getattr(
        image_data,
        "b64_json",
        None
    )

    if not image_b64:

        print(
            "\nERROR: OpenAI did not return b64_json."
        )

        print(
            "\nReturned image object:"
        )

        print(image_data)

        sys.exit(1)

    try:

        image_bytes = base64.b64decode(
            image_b64
        )

    except Exception as error:

        print(
            "\nERROR decoding Base64 image:"
        )

        print(str(error))

        sys.exit(1)

    if not image_bytes:

        print(
            "\nERROR: Decoded image is empty."
        )

        sys.exit(1)

    try:

        with open(
            IMAGE_FILE,
            "wb"
        ) as image_file:

            image_file.write(
                image_bytes
            )

    except Exception as error:

        print(
            "\nERROR saving image:"
        )

        print(str(error))

        sys.exit(1)

    print()
    print("Image generated successfully.")
    print(f"Image file: {IMAGE_FILE}")
    print(
        f"Image size: "
        f"{len(image_bytes) / 1024:.2f} KB"
    )


# ============================================================
# GENERATE ODIA VOICE
# ============================================================

def generate_voice(content):

    print()
    print("=" * 70)
    print("Generating Odia voice narration...")
    print("=" * 70)

    voice_text = content["voice_text"].strip()

    if not voice_text:

        print(
            "ERROR: voice_text is empty."
        )

        sys.exit(1)

    print()
    print("Voice text:")
    print(voice_text)

    try:

        speech_response = client.audio.speech.create(
            model=OPENAI_TTS_MODEL,
            voice="coral",
            input=voice_text,
            instructions=(
                "Speak clearly and naturally in Odia. "
                "Use a calm, peaceful, devotional and respectful tone. "
                "This is narration for a Bhagavad Gita spiritual Reel. "
                "Speak at a comfortable pace and pronounce the Odia "
                "words clearly. Avoid sounding rushed."
            ),
            response_format="mp3",
            speed=0.95
        )

        speech_response.write_to_file(
            str(AUDIO_FILE)
        )

    except Exception as error:

        print()
        print(
            "ERROR generating Odia voice:"
        )

        print(str(error))

        sys.exit(1)

    if not AUDIO_FILE.exists():

        print(
            "\nERROR: Voice file was not created."
        )

        sys.exit(1)

    audio_size = AUDIO_FILE.stat().st_size

    if audio_size == 0:

        print(
            "\nERROR: Voice file is empty."
        )

        sys.exit(1)

    print()
    print("Voice generated successfully.")
    print(f"Audio file: {AUDIO_FILE}")
    print(
        f"Audio size: "
        f"{audio_size / 1024:.2f} KB"
    )


# ============================================================
# CHECK FFMPEG
# ============================================================

def check_ffmpeg():

    print()
    print("=" * 70)
    print("Checking FFmpeg...")
    print("=" * 70)

    try:

        result = subprocess.run(
            [
                "ffmpeg",
                "-version"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    except FileNotFoundError:

        print(
            "\nERROR: FFmpeg is not installed."
        )

        sys.exit(1)

    if result.returncode != 0:

        print(
            "\nERROR: FFmpeg is not working."
        )

        print(result.stderr)

        sys.exit(1)

    version_line = (
        result.stdout.splitlines()[0]
        if result.stdout
        else "FFmpeg detected"
    )

    print(version_line)


# ============================================================
# CREATE 20-SECOND VIDEO WITH VOICE
# ============================================================

def create_video():

    print()
    print("=" * 70)
    print("Creating 20-second Reel with voice...")
    print("=" * 70)

    if not IMAGE_FILE.exists():

        print(
            "ERROR: Image file does not exist."
        )

        sys.exit(1)

    if not AUDIO_FILE.exists():

        print(
            "ERROR: Audio file does not exist."
        )

        sys.exit(1)

    command = [

        "ffmpeg",

        "-y",

        # ----------------------------------------------------
        # Image input
        # ----------------------------------------------------

        "-loop",
        "1",

        "-i",
        str(IMAGE_FILE),

        # ----------------------------------------------------
        # Audio input
        # ----------------------------------------------------

        "-i",
        str(AUDIO_FILE),

        # ----------------------------------------------------
        # Video duration
        # ----------------------------------------------------

        "-t",
        str(VIDEO_DURATION),

        # ----------------------------------------------------
        # Vertical 1080x1920
        # ----------------------------------------------------

        "-vf",
        (
            "scale=1080:1920:"
            "force_original_aspect_ratio=increase,"
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

        # ----------------------------------------------------
        # Explicitly select video stream
        # ----------------------------------------------------

        "-map",
        "0:v:0",

        # ----------------------------------------------------
        # Explicitly select audio stream
        # ----------------------------------------------------

        "-map",
        "1:a:0",

        # ----------------------------------------------------
        # Video codec
        # ----------------------------------------------------

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-pix_fmt",
        "yuv420p",

        # ----------------------------------------------------
        # Audio codec
        # ----------------------------------------------------

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-ar",
        "44100",

        # ----------------------------------------------------
        # Ensure video doesn't exceed 20 seconds
        # ----------------------------------------------------

        "-shortest",

        # ----------------------------------------------------
        # Streaming compatibility
        # ----------------------------------------------------

        "-movflags",
        "+faststart",

        str(VIDEO_FILE)
    ]

    print()
    print("Running FFmpeg...")

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:

        print(
            "\nERROR: FFmpeg failed."
        )

        sys.exit(1)

    if not VIDEO_FILE.exists():

        print(
            "\nERROR: Video file was not created."
        )

        sys.exit(1)

    video_size = VIDEO_FILE.stat().st_size

    if video_size == 0:

        print(
            "\nERROR: Video file is empty."
        )

        sys.exit(1)

    print()
    print("20-second video created successfully.")
    print(f"Video file: {VIDEO_FILE}")
    print(
        f"Video size: "
        f"{video_size / 1024:.2f} KB"
    )


# ============================================================
# VERIFY VIDEO HAS AUDIO
# ============================================================

def verify_video_audio():

    print()
    print("=" * 70)
    print("Checking video audio stream...")
    print("=" * 70)

    command = [

        "ffprobe",

        "-v",
        "error",

        "-select_streams",
        "a:0",

        "-show_entries",
        "stream=codec_name",

        "-of",
        "default=noprint_wrappers=1:nokey=1",

        str(VIDEO_FILE)
    ]

    try:

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    except FileNotFoundError:

        print(
            "ERROR: ffprobe is not installed."
        )

        sys.exit(1)

    audio_codec = result.stdout.strip()

    if not audio_codec:

        print()
        print(
            "ERROR: NO AUDIO STREAM FOUND."
        )

        print(
            "The MP4 was created without audio."
        )

        sys.exit(1)

    print(
        f"Audio codec detected: "
        f"{audio_codec}"
    )

    print(
        "Audio verification: OK"
    )


# ============================================================
# FACEBOOK REEL - START
# ============================================================

def facebook_start_upload():

    print()
    print("=" * 70)
    print("Starting Facebook Reel upload...")
    print("=" * 70)

    graph_url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_API_VERSION}/"
        f"{META_PAGE_ID}/video_reels"
    )

    data = {

        "upload_phase": "start",

        "access_token":
            META_PAGE_ACCESS_TOKEN
    }

    response = requests.post(
        graph_url,
        data=data,
        timeout=120
    )

    print(
        f"Facebook HTTP status: "
        f"{response.status_code}"
    )

    try:

        result = response.json()

    except Exception:

        print(response.text)

        sys.exit(1)

    if response.status_code >= 400:

        print()
        print("Facebook START error:")

        print(
            json.dumps(
                result,
                indent=2
            )
        )

        sys.exit(1)

    video_id = result.get(
        "video_id"
    )

    if not video_id:

        print()
        print(
            "ERROR: Facebook did not return video_id."
        )

        print(
            json.dumps(
                result,
                indent=2
            )
        )

        sys.exit(1)

    print(
        f"Facebook Video ID: {video_id}"
    )

    return video_id


# ============================================================
# FACEBOOK REEL - TRANSFER
# ============================================================

def facebook_transfer_video(video_id):

    print()
    print("=" * 70)
    print("Uploading MP4 to Facebook...")
    print("=" * 70)

    file_size = VIDEO_FILE.stat().st_size

    upload_url = (
        f"https://rupload.facebook.com/"
        f"video-upload/"
        f"{GRAPH_API_VERSION}/"
        f"{video_id}"
    )

    headers = {

        "Authorization":
            f"OAuth {META_PAGE_ACCESS_TOKEN}",

        "offset":
            "0",

        "file_size":
            str(file_size)
    }

    print(
        f"Video size: "
        f"{file_size / 1024:.2f} KB"
    )

    try:

        with open(
            VIDEO_FILE,
            "rb"
        ) as video_file:

            response = requests.post(
                upload_url,
                headers=headers,
                data=video_file,
                timeout=300
            )

    except Exception as error:

        print()
        print(
            "ERROR uploading video:"
        )

        print(str(error))

        sys.exit(1)

    print(
        f"Facebook upload HTTP status: "
        f"{response.status_code}"
    )

    print(
        response.text
    )

    if response.status_code >= 400:

        print()
        print(
            "ERROR: Facebook video transfer failed."
        )

        sys.exit(1)

    print(
        "\nVideo transfer completed."
    )


# ============================================================
# FACEBOOK REEL - PUBLISH
# ============================================================

def facebook_publish_reel(
    video_id,
    content
):

    print()
    print("=" * 70)
    print("Publishing Facebook Reel...")
    print("=" * 70)

    graph_url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_API_VERSION}/"
        f"{META_PAGE_ID}/video_reels"
    )

    caption = (
        content["caption"].strip()
    )

    hashtags = content.get(
        "hashtags",
        []
    )

    if hashtags:

        caption += (
            "\n\n"
            + " ".join(hashtags)
        )

    data = {

        "upload_phase":
            "finish",

        "video_id":
            video_id,

        "video_state":
            "PUBLISHED",

        "description":
            caption,

        "access_token":
            META_PAGE_ACCESS_TOKEN
    }

    response = requests.post(
        graph_url,
        data=data,
        timeout=120
    )

    print(
        f"Facebook publish HTTP status: "
        f"{response.status_code}"
    )

    try:

        result = response.json()

    except Exception:

        print(response.text)

        sys.exit(1)

    if response.status_code >= 400:

        print()
        print(
            "Facebook PUBLISH error:"
        )

        print(
            json.dumps(
                result,
                indent=2
            )
        )

        sys.exit(1)

    print()
    print(
        "Facebook response:"
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )

    print()
    print("=" * 70)
    print("FACEBOOK REEL PUBLISHED SUCCESSFULLY")
    print("=" * 70)

    print(
        f"Video ID: {video_id}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("ODIA BHAGABATA GITA - AUTOMATIC FACEBOOK REEL")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Environment
    # --------------------------------------------------------

    validate_environment()

    # --------------------------------------------------------
    # 2. OpenAI
    # --------------------------------------------------------

    global client

    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

    # --------------------------------------------------------
    # 3. Generate Odia content
    # --------------------------------------------------------

    content = generate_content()

    global CURRENT_CONTENT

    CURRENT_CONTENT = content

    # --------------------------------------------------------
    # 4. Generate image
    # --------------------------------------------------------

    generate_image(
        content
    )

    # --------------------------------------------------------
    # 5. Generate Odia voice
    # --------------------------------------------------------

    generate_voice(
        content
    )

    # --------------------------------------------------------
    # 6. Check FFmpeg
    # --------------------------------------------------------

    check_ffmpeg()

    # --------------------------------------------------------
    # 7. Create video
    # --------------------------------------------------------

    create_video()

    # --------------------------------------------------------
    # 8. Verify audio
    # --------------------------------------------------------

    verify_video_audio()

    # --------------------------------------------------------
    # 9. Upload to Facebook
    # --------------------------------------------------------

    video_id = facebook_start_upload()

    # --------------------------------------------------------
    # 10. Transfer MP4
    # --------------------------------------------------------

    facebook_transfer_video(
        video_id
    )

    # --------------------------------------------------------
    # 11. Give Facebook a moment
    # --------------------------------------------------------

    print()
    print(
        "Waiting for Facebook processing..."
    )

    time.sleep(5)

    # --------------------------------------------------------
    # 12. Publish
    # --------------------------------------------------------

    facebook_publish_reel(
        video_id,
        content
    )

    # --------------------------------------------------------
    # DONE
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("ALL TASKS COMPLETED SUCCESSFULLY")
    print("=" * 70)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\nProcess interrupted."
        )

        sys.exit(1)

    except Exception as error:

        print()
        print("=" * 70)
        print("UNEXPECTED ERROR")
        print("=" * 70)

        print(
            str(error)
        )

        sys.exit(1)
