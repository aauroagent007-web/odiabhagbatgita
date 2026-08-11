import os
import sys
import base64
import requests
from openai import OpenAI


# ============================================================
# CONFIGURATION
# ============================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
META_PAGE_ID = os.getenv("META_PAGE_ID")
META_PAGE_ACCESS_TOKEN = os.getenv("META_PAGE_ACCESS_TOKEN")

# You can change these in GitHub Secrets/Variables if required.
OPENAI_TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")

META_GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v26.0")

# Facebook API endpoint
FACEBOOK_PHOTO_URL = (
    f"https://graph.facebook.com/{META_GRAPH_VERSION}/"
    f"{META_PAGE_ID}/photos"
)


# ============================================================
# VALIDATE ENVIRONMENT
# ============================================================

def validate_environment():
    missing = []

    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")

    if not META_PAGE_ID:
        missing.append("META_PAGE_ID")

    if not META_PAGE_ACCESS_TOKEN:
        missing.append("META_PAGE_ACCESS_TOKEN")

    if missing:
        print("ERROR: Missing required environment variables:")
        for item in missing:
            print(f"  - {item}")
        sys.exit(1)

    print("Environment variables loaded successfully.")
    print(f"Facebook Page ID: {META_PAGE_ID}")
    print(f"OpenAI text model: {OPENAI_TEXT_MODEL}")
    print(f"OpenAI image model: {OPENAI_IMAGE_MODEL}")


# ============================================================
# OPENAI CLIENT
# ============================================================

def create_openai_client():
    return OpenAI(api_key=OPENAI_API_KEY)


# ============================================================
# GENERATE ODIA FACEBOOK POST
# ============================================================

def generate_odia_post(client):
    print("\nGenerating Odia Bhagavad Gita post...")

    prompt = """
Create one original Facebook post inspired by the Bhagavad Gita.

Language:
- Odia only.
- Use natural, easy-to-read Odia.
- Do not use English except where absolutely necessary.

Content:
- Spiritual and positive.
- Suitable for the Facebook page "Srimad Bhagabat Gita".
- Explain one practical life lesson inspired by the Bhagavad Gita.
- Do not invent a fake Bhagavad Gita verse.
- If mentioning a verse, clearly identify it as an inspiration rather than claiming an exact quotation.
- Avoid political content.
- Avoid controversial religious claims.

Format:
- Start with a short attractive Odia heading.
- Then 2-4 short paragraphs.
- End with a short devotional thought.
- Add 5-8 relevant hashtags.
- Keep the total post reasonably short for Facebook.

Return ONLY the final Facebook post.
"""

    response = client.responses.create(
        model=OPENAI_TEXT_MODEL,
        input=prompt
    )

    post_text = response.output_text.strip()

    if not post_text:
        raise RuntimeError("OpenAI returned an empty Facebook post.")

    print("\nGenerated Facebook post:")
    print("-" * 60)
    print(post_text)
    print("-" * 60)

    return post_text


# ============================================================
# GENERATE IMAGE PROMPT
# ============================================================

def create_image_prompt(client, post_text):
    print("\nCreating image prompt...")

    prompt = f"""
Create a concise image-generation prompt for a Facebook devotional
image based on the following Odia Bhagavad Gita post.

Facebook post:
{post_text}

Requirements:
- Indian spiritual aesthetic.
- Lord Krishna and Arjuna may be depicted respectfully.
- Kurukshetra-inspired environment where appropriate.
- Cinematic devotional atmosphere.
- Golden sunrise/light.
- Highly detailed traditional Indian visual style.
- Peaceful, inspirational and premium-looking.
- 1:1 square Facebook post composition.
- No text.
- No letters.
- No watermark.
- No logo.
- No social-media UI.
- Do not attempt to reproduce copyrighted artwork.

Return ONLY the image prompt.
"""

    response = client.responses.create(
        model=OPENAI_TEXT_MODEL,
        input=prompt
    )

    image_prompt = response.output_text.strip()

    if not image_prompt:
        raise RuntimeError("OpenAI returned an empty image prompt.")

    print("\nImage prompt created successfully.")

    return image_prompt


# ============================================================
# GENERATE IMAGE
# ============================================================

def generate_image(client, image_prompt):
    print("\nGenerating devotional image with OpenAI...")

    response = client.images.generate(
        model=OPENAI_IMAGE_MODEL,
        prompt=image_prompt,
        size="1024x1024",
        quality="medium"
    )

    if not response.data:
        raise RuntimeError("OpenAI image generation returned no image data.")

    image_data = response.data[0]

    # GPT Image models return Base64 image data.
    image_b64 = getattr(image_data, "b64_json", None)

    if not image_b64:
        raise RuntimeError(
            "OpenAI image generation did not return b64_json image data."
        )

    try:
        image_bytes = base64.b64decode(image_b64)
    except Exception as exc:
        raise RuntimeError(
            f"Unable to decode OpenAI image Base64 data: {exc}"
        ) from exc

    if not image_bytes:
        raise RuntimeError("Decoded image is empty.")

    print(
        f"Image generated successfully "
        f"({len(image_bytes) / 1024:.1f} KB)."
    )

    return image_bytes


# ============================================================
# POST IMAGE TO FACEBOOK PAGE
# ============================================================

def post_image_to_facebook(post_text, image_bytes):
    print("\nUploading image to Facebook...")

    files = {
        "source": (
            "srimad_bhagabat_gita.png",
            image_bytes,
            "image/png"
        )
    }

    data = {
        "message": post_text,
        "access_token": META_PAGE_ACCESS_TOKEN
    }

    try:
        response = requests.post(
            FACEBOOK_PHOTO_URL,
            data=data,
            files=files,
            timeout=120
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Facebook request failed: {exc}"
        ) from exc

    print(f"Facebook HTTP status: {response.status_code}")

    try:
        result = response.json()
    except ValueError:
        raise RuntimeError(
            "Facebook returned a non-JSON response:\n"
            + response.text[:1000]
        )

    if not response.ok:
        print("\nFacebook API error:")
        print(result)

        error = result.get("error", {})

        message = error.get(
            "message",
            "Unknown Facebook API error"
        )

        code = error.get("code")
        subcode = error.get("error_subcode")

        raise RuntimeError(
            f"Facebook API error: {message} "
            f"(code={code}, subcode={subcode})"
        )

    print("\nFacebook upload successful.")
    print(result)

    return result


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("ODIA BHAGABAT GITA - FACEBOOK AUTO POSTER")
    print("=" * 60)

    validate_environment()

    client = create_openai_client()

    # --------------------------------------------------------
    # 1. Generate Odia post
    # --------------------------------------------------------
    post_text = generate_odia_post(client)

    # --------------------------------------------------------
    # 2. Generate image prompt
    # --------------------------------------------------------
    image_prompt = create_image_prompt(
        client,
        post_text
    )

    # --------------------------------------------------------
    # 3. Generate image
    # --------------------------------------------------------
    image_bytes = generate_image(
        client,
        image_prompt
    )

    # --------------------------------------------------------
    # 4. Upload to Facebook
    # --------------------------------------------------------
    facebook_result = post_image_to_facebook(
        post_text,
        image_bytes
    )

    # --------------------------------------------------------
    # 5. Success
    # --------------------------------------------------------
    print("\n" + "=" * 60)
    print("SUCCESS")
    print("=" * 60)

    if isinstance(facebook_result, dict):
        post_id = (
            facebook_result.get("post_id")
            or facebook_result.get("id")
        )

        if post_id:
            print(f"Facebook Post ID: {post_id}")

    print("Your Odia Bhagavad Gita image post has been published.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\nProcess cancelled by user.")
        sys.exit(130)

    except Exception as exc:
        print("\n" + "=" * 60)
        print("FAILED")
        print("=" * 60)
        print(str(exc))
        print("=" * 60)
        sys.exit(1)
