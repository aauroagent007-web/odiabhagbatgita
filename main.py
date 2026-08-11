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

OPENAI_TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")

META_GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v26.0")


# ============================================================
# VALIDATE ENVIRONMENT VARIABLES
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
        print("ERROR: Missing GitHub Secrets:")
        for item in missing:
            print(f"  - {item}")

        sys.exit(1)

    print("==========================================")
    print("Environment validation successful")
    print("==========================================")
    print(f"Facebook Page ID: {META_PAGE_ID}")
    print(f"OpenAI Text Model: {OPENAI_TEXT_MODEL}")
    print(f"OpenAI Image Model: {OPENAI_IMAGE_MODEL}")


# ============================================================
# OPENAI CLIENT
# ============================================================

def create_openai_client():

    return OpenAI(
        api_key=OPENAI_API_KEY
    )


# ============================================================
# GENERATE ODIA BHAGAVAD GITA FACEBOOK POST
# ============================================================

def generate_odia_post(client):

    print()
    print("Generating Odia Bhagavad Gita Facebook post...")

    prompt = """
Create one original Facebook post inspired by the Bhagavad Gita.

The Facebook page is:

Srimad Bhagabat Gita

Requirements:

- Write the post in natural Odia.
- Use Odia script.
- The content should be spiritual, positive and inspirational.
- Explain one practical life lesson inspired by the Bhagavad Gita.
- Do not invent a Bhagavad Gita verse.
- Do not falsely attribute a quotation to Krishna or the Bhagavad Gita.
- If mentioning a verse, clearly mention the chapter and verse only when confident.
- Avoid political content.
- Avoid controversial claims.
- Make the post suitable for a general Facebook audience.
- Use a short attractive heading.
- Use 2-4 short paragraphs.
- End with a devotional thought.
- Add 5-8 relevant hashtags.

Return ONLY the final Facebook post.

Do not explain what you did.
"""

    response = client.responses.create(
        model=OPENAI_TEXT_MODEL,
        input=prompt
    )

    post_text = response.output_text.strip()

    if not post_text:
        raise RuntimeError(
            "OpenAI returned an empty Facebook post."
        )

    print("------------------------------------------")
    print(post_text)
    print("------------------------------------------")

    return post_text


# ============================================================
# CREATE IMAGE PROMPT
# ============================================================

def create_image_prompt(client, post_text):

    print()
    print("Creating image prompt...")

    prompt = f"""
Create a professional image-generation prompt for a Facebook
devotional post based on this content:

{post_text}

Image requirements:

- Indian spiritual atmosphere.
- Lord Krishna and Arjuna may appear respectfully.
- Kurukshetra-inspired environment where appropriate.
- Beautiful golden sunrise or divine light.
- Cinematic devotional atmosphere.
- Traditional Indian visual aesthetics.
- Highly detailed.
- Peaceful and inspirational.
- Premium Facebook social-media artwork.
- Square 1:1 composition.
- No written text.
- No letters.
- No captions.
- No watermark.
- No logo.
- No Facebook interface.
- Do not copy existing artwork.

Return ONLY the image-generation prompt.
"""

    response = client.responses.create(
        model=OPENAI_TEXT_MODEL,
        input=prompt
    )

    image_prompt = response.output_text.strip()

    if not image_prompt:
        raise RuntimeError(
            "OpenAI returned an empty image prompt."
        )

    print("Image prompt created successfully.")

    return image_prompt


# ============================================================
# GENERATE IMAGE
# ============================================================

def generate_image(client, image_prompt):

    print()
    print("Generating image with OpenAI...")
    print(f"Image model: {OPENAI_IMAGE_MODEL}")

    response = client.images.generate(
        model=OPENAI_IMAGE_MODEL,
        prompt=image_prompt,
        size="1024x1024",
        quality="medium"
    )

    if not response.data:
        raise RuntimeError(
            "OpenAI returned no image data."
        )

    image_data = response.data[0]

    # --------------------------------------------------------
    # GPT Image models return Base64 image data.
    # Do NOT try to download response.data[0].url.
    # --------------------------------------------------------

    image_b64 = getattr(
        image_data,
        "b64_json",
        None
    )

    if not image_b64:
        raise RuntimeError(
            "OpenAI did not return b64_json image data."
        )

    try:

        image_bytes = base64.b64decode(
            image_b64
        )

    except Exception as error:

        raise RuntimeError(
            f"Could not decode Base64 image: {error}"
        )

    if not image_bytes:

        raise RuntimeError(
            "Decoded image is empty."
        )

    print(
        f"Image generated successfully: "
        f"{len(image_bytes) / 1024:.2f} KB"
    )

    return image_bytes


# ============================================================
# FACEBOOK IMAGE POST
# ============================================================

def publish_to_facebook(
    post_text,
    image_bytes
):

    print()
    print("Publishing to Facebook...")

    facebook_url = (
        f"https://graph.facebook.com/"
        f"{META_GRAPH_VERSION}/"
        f"{META_PAGE_ID}/photos"
    )

    files = {

        "source": (
            "gita_post.png",
            image_bytes,
            "image/png"
        )

    }

    data = {

        "message": post_text,

        "access_token":
            META_PAGE_ACCESS_TOKEN

    }

    try:

        response = requests.post(
            facebook_url,
            data=data,
            files=files,
            timeout=120
        )

    except requests.RequestException as error:

        raise RuntimeError(
            f"Facebook connection failed: {error}"
        )

    print(
        f"Facebook HTTP status: "
        f"{response.status_code}"
    )

    try:

        result = response.json()

    except ValueError:

        raise RuntimeError(
            "Facebook returned invalid JSON:\n"
            + response.text[:1000]
        )

    # --------------------------------------------------------
    # Facebook API error
    # --------------------------------------------------------

    if not response.ok:

        print()
        print("Facebook API ERROR:")
        print(result)

        error_data = result.get(
            "error",
            {}
        )

        error_message = error_data.get(
            "message",
            "Unknown Facebook error"
        )

        error_code = error_data.get(
            "code",
            "Unknown"
        )

        error_subcode = error_data.get(
            "error_subcode",
            "Unknown"
        )

        raise RuntimeError(
            f"Facebook API Error: "
            f"{error_message} "
            f"(code={error_code}, "
            f"subcode={error_subcode})"
        )

    print()
    print("==========================================")
    print("FACEBOOK POST SUCCESSFUL")
    print("==========================================")

    print(result)

    return result


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print()
    print("==========================================")
    print("ODIA BHAGABAT GITA AUTO POSTER")
    print("==========================================")

    # --------------------------------------------------------
    # 1. Validate secrets
    # --------------------------------------------------------

    validate_environment()

    # --------------------------------------------------------
    # 2. Create OpenAI client
    # --------------------------------------------------------

    client = create_openai_client()

    # --------------------------------------------------------
    # 3. Generate Odia Facebook content
    # --------------------------------------------------------

    post_text = generate_odia_post(
        client
    )

    # --------------------------------------------------------
    # 4. Generate image prompt
    # --------------------------------------------------------

    image_prompt = create_image_prompt(
        client,
        post_text
    )

    # --------------------------------------------------------
    # 5. Generate image
    # --------------------------------------------------------

    image_bytes = generate_image(
        client,
        image_prompt
    )

    # --------------------------------------------------------
    # 6. Publish image + text to Facebook
    # --------------------------------------------------------

    result = publish_to_facebook(
        post_text,
        image_bytes
    )

    # --------------------------------------------------------
    # 7. Display result
    # --------------------------------------------------------

    post_id = None

    if isinstance(result, dict):

        post_id = result.get(
            "post_id"
        )

        if not post_id:

            post_id = result.get(
                "id"
            )

    print()
    print("==========================================")
    print("AUTOMATION COMPLETED")
    print("==========================================")

    if post_id:

        print(
            f"Facebook Post ID: {post_id}"
        )

    print(
        "Odia Bhagabat Gita post "
        "published successfully."
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\nProcess stopped."
        )

        sys.exit(130)

    except Exception as error:

        print()
        print("==========================================")
        print("AUTOMATION FAILED")
        print("==========================================")
        print(str(error))
        print("==========================================")

        sys.exit(1)
