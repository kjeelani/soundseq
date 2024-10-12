import base64
import requests
from dotenv import load_dotenv
import os

load_dotenv()
# OpenAI API Key
api_key = os.getenv("OPENAI_API_KEY")

SEMANTIC_IMAGE_PROMPT = """
Analyze the following 2x2 grid of frames as a comic version of a video scene. 
Describe the main actions, the subject(s) involved, and the environment in one concise sentence. 
Focus on identifying key physical actions and contextual details, 
including the type of location or setting.

Examples:
Man throws ball to a dog in a grassy park.
Girl slap boy with a fan in a dojo.
A car speeds down a rainy street.
Two kids chase each other around a tree in a playground.
"""

# Function to encode the image
def encode_image(img_path):
  with open(img_path, "rb") as img_file:
    return base64.b64encode(img_file.read()).decode('utf-8')

def get_semantic_image_desc(img_path):
    base64_img = encode_image(img_path)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": SEMANTIC_IMAGE_PROMPT
                },
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_img}"
                }
                }
            ]
            }
        ]
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response_json = response.json()
    return response_json["choices"][0]["message"]["content"]