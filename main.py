import os
import requests
from openai import OpenAI

PAGE_ID = os.environ['META_PAGE_ID']
PAGE_ACCESS_TOKEN = os.environ['META_PAGE_ACCESS_TOKEN']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

client = OpenAI(api_key=OPENAI_API_KEY)

prompt = '''Create one original daily devotional Facebook post for the Odia Bhagabata Gita page.
Write in natural Odia. Focus on Bhagavad Gita-inspired spiritual wisdom, devotion, self-discipline,
peace, karma, or Krishna's teachings. Do not invent verse numbers or claim an exact quotation unless
certain. Return ONLY the post text, suitable as a Facebook caption. Keep it around 100-180 words.
Include a short devotional title and a closing line encouraging readers to reflect on the teaching.'''

response = client.responses.create(model='gpt-5-mini', input=prompt)
caption = response.output_text.strip()

image_prompt = '''Create a square 1080x1080 devotional social-media image for an Odia Bhagabata Gita Facebook page.
A serene, respectful Indian spiritual scene featuring Lord Krishna with Arjuna near a chariot,
golden sunrise, subtle temple atmosphere, elegant traditional Indian art, peaceful and uplifting mood.
Leave clean space for a short Odia quote, but do not render any text because text will be added separately.
No watermark, no logo, no modern objects.'''

img = client.images.generate(model='gpt-image-1', prompt=image_prompt, size='1024x1024')
image_url = img.data[0].url
image_bytes = requests.get(image_url, timeout=60).content
with open('/tmp/post.png', 'wb') as f:
    f.write(image_bytes)

# Upload image to Facebook as an unpublished photo, then publish it with the caption.
with open('/tmp/post.png', 'rb') as f:
    upload = requests.post(
        f'https://graph.facebook.com/v23.0/{PAGE_ID}/photos',
        params={'access_token': PAGE_ACCESS_TOKEN, 'published': 'false'},
        files={'source': ('post.png', f, 'image/png')},
        timeout=120,
    )
upload.raise_for_status()
photo_id = upload.json()['id']

publish = requests.post(
    f'https://graph.facebook.com/v23.0/{PAGE_ID}/feed',
    params={
        'access_token': PAGE_ACCESS_TOKEN,
        'message': caption,
        'attached_media[0]': '{"media_fbid":"' + photo_id + '"}',
    },
    timeout=120,
)
publish.raise_for_status()
print('Facebook post published:', publish.json())
