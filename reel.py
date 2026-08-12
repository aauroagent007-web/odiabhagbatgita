import os
import sys
import json
import time
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


# ============================================================
# VALIDATE ENVIRONMENT
# ============================================================

def validate_environment():

    print("\nChecking environment...")

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

        print("\nPlease check:")
        print("GitHub → Settings → Secrets and variables → Actions")

        sys.exit(1)

    print("OPENAI_API_KEY: OK")
    print(f"META_PAGE_ID: {META_PAGE_ID}")
    print("META_PAGE_ACCESS_TOKEN: OK")


# ============================================================
# OPENAI CLIENT
# ============================================================

client = OpenAI(
    api_key=OPENAI_API_KEY
)


# ============================================================
# GENERATE ODIA CONTENT
# ============================================================

def generate_content():

    print("\n" + "=" * 60)
    print("Generating Odia Bhagavad Gita Reel content...")
    print("=" * 60)

    prompt = """
Create content for a 20-second Facebook Reel for an Odia
Bhagavad Gita spiritual page.

The content must be in natural, grammatically correct Odia.

Create:

1. A short title.
2. A short devotional message.
3. A voice narration suitable for approximately 15-20 seconds.
4. A short Facebook caption.
5. 5-8 relevant hashtags.

The narration should be approximately 35-50 Odia words.
It must be peaceful, devotional and easy to speak.

Do NOT invent a Bhagavad Gita quotation and attribute it directly
to Lord Krishna.

If mentioning a teaching from the Bhagavad Gita, clearly describe
it as a teaching or message rather than presenting an invented
quotation as a scripture verse.

Return ONLY valid JSON in this format:

{
  "title": "...",
  "message": "...",
  "voice_text": "...",
  "caption": "...",
  "hashtags": ["...", "..."]
}
"""

    response = client.chat.completions.create(
        model=OPENAI_TEXT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert Odia spiritual content writer. "
                    "Write natural, respectful Odia."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.8
    )

    text = response.choices[0].message.content.strip()

    # Remove markdown JSON fences if the model adds them
    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    try:
        content = json.loads(text)
    except json.JSONDecodeError:
        print("\nERROR: OpenAI did not return valid JSON.")
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
            print(f"ERROR: Missing field: {field}")
            sys.exit(1)

    print("\nTitle:")
    print(content["title"])

    print("\nMessage:")
    print(content["message"])

    print("\nVoice narration:")
    print(content["voice_text"])

    print("\nCaption:")
    print(content["caption"])

    print("\nHashtags:")
    print(" ".join(content["hashtags"]))

    return content


# ============================================================
# GENERATE IMAGE
# ============================================================

def generate_image(content):

    print("\n" + "=" * 60)
    print("Generating vertical devotional image...")
    print("=" * 60)

    image_prompt = f"""
Create a highly beautiful cinematic devotional image for an
Odia Bhagavad Gita Facebook Reel.

Vertical 9:16 composition.

Scene:
Lord Krishna standing peacefully in a majestic spiritual
environment inspired by the Kurukshetra battlefield, with
soft golden sunrise light, subtle divine aura, traditional
Indian atmosphere, elegant clothing, peaceful expression,
cinematic lighting, realistic devotional artwork.

The visual should communicate:
{content["message"]}

Important:
- Vertical composition
- 9:16
- Suitable for a Facebook Reel
- High quality
- Cinematic
- Spiritual
- Respectful
- No modern objects
- No watermark
- No logo
- No text
- No captions
"""

    try:
        result = client.images.generate(
            model=OPENAI_IMAGE_MODEL,
            prompt=image_prompt,
            size="1024x1536"
        )

    except Exception as e:
        print("\nImage generation failed:")
        print(str(e))
        sys.exit(1)

    image_url = None

    if result.data:
        image_url = result.data[0].url

    if not image_url:
        print("\nERROR: OpenAI did not return an image URL.")
        print(result)
        sys.exit(1)

    print("Image URL received.")

    try:
        image_response = requests.get(
            image_url,
            timeout=120
        )

        image_response.raise_for_status()

    except Exception as e:
        print("\nERROR downloading generated image:")
        print(str(e))
        sys.exit(1)

    with open(IMAGE_FILE, "wb") as f:
        f.write(image_response.content)

    print(f"Image saved: {IMAGE_FILE}")
    print(f"Image size: {IMAGE_FILE.stat().st_size} bytes")


# ============================================================
# GENERATE ODIA VOICE
# ============================================================

def generate_voice(content):

    print("\n" + "=" * 60)
    print("Generating Odia voice narration...")
    print("=" * 60)

    voice_text = content["voice_text"].strip()

    if not voice_text:
        print("ERROR: voice_text is empty.")
        sys.exit(1)

    print("\nVoice text:")
    print(voice_text)

    try:

        speech_response = client.audio.speech.create(
            model=OPENAI_TTS_MODEL,
            voice="coral",
            input=voice_text,
            instructions=(
                "Speak clearly and naturally in Odia. "
                "Use a calm, peaceful and devotional tone. "
                "This is narration for a Bhagavad Gita spiritual "
                "Facebook Reel. Speak slowly enough to be understood, "
                "but keep the narration concise."
            ),
            response_format="mp3",
            speed=0.95
        )

        speech_response.write_to_file(
            str(AUDIO_FILE)
        )

    except Exception as e:

        print("\nERROR generating voice:")
        print(str(e))

        sys.exit(1)

    if not AUDIO_FILE.exists():
        print("\nERROR: Voice file was not created.")
        sys.exit(1)

    if AUDIO_FILE.stat().st_size == 0:
        print("\nERROR: Voice file is empty.")
        sys.exit(1)

    print(f"\nVoice created successfully:")
    print(AUDIO_FILE)
    print(f"Voice size: {AUDIO_FILE.stat().st_size} bytes")


# ============================================================
# CHECK FFMPEG
# ============================================================

def check_ffmpeg():

    print("\nChecking FFmpeg...")

    try:

        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError("FFmpeg is not available.")

        first_line = result.stdout.splitlines()[0]

        print(first_line)

    except Exception as e:

        print("\nERROR: FFmpeg is not installed.")
        print(str(e))

        print(
            "\nAdd the following step to reel.yml:\n"
            "sudo apt-get update && sudo apt-get install -y ffmpeg"
        )

        sys.exit(1)


# ============================================================
# CREATE 20 SECOND VIDEO
# ============================================================

def create_video():

    print("\n" + "=" * 60)
    print("Creating 20-second video with voice...")
    print("=" * 60)

    if not IMAGE_FILE.exists():
        print("ERROR: Image file does not exist.")
        sys.exit(1)

    if not AUDIO_FILE.exists():
        print("ERROR: Audio file does not exist.")
        sys.exit(1)

    command = [
        "ffmpeg",
        "-y",

        # IMAGE
        "-loop",
        "1",

        "-i",
        str(IMAGE_FILE),

        # AUDIO
        "-i",
        str(AUDIO_FILE),

        # Duration
        "-t",
        str(VIDEO_DURATION),

        # Vertical video
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

        # Explicitly map video
        "-map",
        "0:v:0",

        # Explicitly map audio
        "-map",
        "1:a:0",

        # Video encoding
        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-pix_fmt",
        "yuv420p",

        # Audio encoding
        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-ar",
        "44100",

        # Stop after video duration
        "-shortest",

        # Better streaming compatibility
        "-movflags",
        "+faststart",

        str(VIDEO_FILE)
    ]

    print("\nRunning FFmpeg...")

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:

        print("\nERROR: FFmpeg failed.")
        sys.exit(1)

    if not VIDEO_FILE.exists():

        print("\nERROR: Video was not created.")
        sys.exit(1)

    size = VIDEO_FILE.stat().st_size

    if size == 0:

        print("\nERROR: Video file is empty.")
        sys.exit(1)

    print("\nVideo created successfully.")
    print(f"File: {VIDEO_FILE}")
    print(f"Size: {size} bytes")


# ============================================================
# VERIFY VIDEO HAS AUDIO
# ============================================================

def verify_video_audio():

    print("\nChecking video audio stream...")

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

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    audio_codec = result.stdout.strip()

    if not audio_codec:

        print("\nERROR: No audio stream detected in video.")
        sys.exit(1)

    print(f"Audio codec detected: {audio_codec}")
    print("Audio verification: OK")


# ============================================================
# FACEBOOK REEL UPLOAD
# ============================================================

def publish_reel():

    print("\n" + "=" * 60)
    print("Publishing Reel to Facebook...")
    print("=" * 60)

    if not VIDEO_FILE.exists():
        print("ERROR: Video does not exist.")
        sys.exit(1)

    graph_url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_API_VERSION}/"
        f"{META_PAGE_ID}/video_reels"
    )

    print(f"\nFacebook endpoint:")
    print(graph_url)

    # --------------------------------------------------------
    # STEP 1: START UPLOAD
    # --------------------------------------------------------

    print("\nStarting Facebook Reel upload...")

    start_data = {
        "upload_phase": "start",
        "access_token": META_PAGE_ACCESS_TOKEN
    }

    start_response = requests.post(
        graph_url,
        data=start_data,
        timeout=120
    )

    print(
        f"Start upload HTTP status: "
        f"{start_response.status_code}"
    )

    try:
        start_json = start_response.json()
    except Exception:
        print(start_response.text)
        sys.exit(1)

    if start_response.status_code >= 400:

        print("\nFacebook start upload error:")
        print(json.dumps(start_json, indent=2))

        sys.exit(1)

    video_id = start_json.get("video_id")

    if not video_id:

        print("\nERROR: Facebook did not return video_id.")
        print(json.dumps(start_json, indent=2))

        sys.exit(1)

    print(f"Facebook video ID: {video_id}")

    # --------------------------------------------------------
    # STEP 2: UPLOAD LOCAL VIDEO
    # --------------------------------------------------------

    print("\nUploading MP4 to Facebook...")

    file_size = VIDEO_FILE.stat().st_size

    upload_url = (
        f"https://graph-video.facebook.com/"
        f"{GRAPH_API_VERSION}/"
        f"{video_id}"
    )

    headers = {
        "Authorization": f"OAuth {META_PAGE_ACCESS_TOKEN}",
        "offset": "0",
        "file_size": str(file_size)
    }

    with open(VIDEO_FILE, "rb") as video_file:

        upload_response = requests.post(
            upload_url,
            headers=headers,
            data=video_file,
            timeout=300
        )

    print(
        f"Upload HTTP status: "
        f"{upload_response.status_code}"
    )

    try:
        upload_json = upload_response.json()
    except Exception:
        upload_json = {
            "raw_response": upload_response.text
        }

    if upload_response.status_code >= 400:

        print("\nFacebook video upload error:")
        print(json.dumps(upload_json, indent=2))

        sys.exit(1)

    print("\nVideo uploaded successfully.")

    # --------------------------------------------------------
    # STEP 3: FINISH / PUBLISH REEL
    # --------------------------------------------------------

    print("\nPublishing Reel...")

    caption = CURRENT_CONTENT.get("caption", "")

    hashtags = CURRENT_CONTENT.get("hashtags", [])

    if hashtags:
        caption += "\n\n" + " ".join(hashtags)

    finish_data = {
        "upload_phase": "finish",
        "video_id": video_id,
        "video_state": "PUBLISHED",
        "description": caption,
        "access_token": META_PAGE_ACCESS_TOKEN
    }

    finish_response = requests.post(
        graph_url,
        data=finish_data,
        timeout=120
    )

    print(
        f"Finish HTTP status: "
        f"{finish_response.status_code}"
    )

    try:
        finish_json = finish_response.json()
    except Exception:
        finish_json = {
            "raw_response": finish_response.text
        }

    if finish_response.status_code >= 400:

        print("\nFacebook publish error:")
        print(json.dumps(finish_json, indent=2))

        sys.exit(1)

    print("\nFacebook response:")
    print(json.dumps(finish_json, indent=2))

    print("\n" + "=" * 60)
    print("FACEBOOK REEL PUBLISHED SUCCESSFULLY")
    print("=" * 60)

    print(f"Video ID: {video_id}")


# ============================================================
# MAIN
# ============================================================

CURRENT_CONTENT = {}


def main():

    print("\n")
    print("=" * 70)
    print("ODIA BHAGABATA GITA - AUTOMATIC FACEBOOK REEL")
    print("=" * 70)

    validate_environment()

    # 1. Generate Odia content
    content = generate_content()

    global CURRENT_CONTENT
    CURRENT_CONTENT = content

    # 2. Generate devotional image
    generate_image(content)

    # 3. Generate Odia voice
    generate_voice(content)

    # 4. Check FFmpeg
    check_ffmpeg()

    # 5. Create MP4 with image + voice
    create_video()

    # 6. Verify audio exists inside MP4
    verify_video_audio()

    # 7. Publish Facebook Reel
    publish_reel()

    print("\nAll tasks completed successfully.")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:

        print("\nProcess interrupted.")
        sys.exit(1)

    except Exception as e:

        print("\n" + "=" * 70)
        print("UNEXPECTED ERROR")
        print("=" * 70)

        print(str(e))

        sys.exit(1)
