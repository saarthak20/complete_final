import requests
import os
import time
import base64
from publish import upload_to_wordpress,fetch_pending_posts

def process_single_article(title, content, category,news_type,client):
    """Process and store a single article in MongoDB"""
    try:
        db = client["agent"]
        collection = db["news"]

        summary = generate_summary(content)
        
        image_url = generate_image(title)

        category_id = 6 if news_type == 'local' else 5
        
        document = {
            "title": title,
            "content": summary,
            "image_url": image_url,
            "category_id": category_id,
            "seo_keywords": category,
            "status": "pending"
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = collection.insert_one(document)
                print(f"Successfully stored article: {title}")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Failed to store article after {max_retries} attempts: {str(e)}")
                    return None
                print(f"Retry attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2 ** attempt) 
        print("successfully inserted in mongodb")
        posts = fetch_pending_posts(collection)
        for post in posts:
            upload_to_wordpress(post,collection)
    except Exception as e:
        print(f"Error processing article: {str(e)}")
        return None

def generate_summary(content):
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {os.getenv('API_KEY')}"}

    chunks = [content[i:i + 1024] for i in range(0, len(content), 1024)]
    summaries = []

    for chunk in chunks:
        payload = {
            "inputs": chunk,
            "parameters": {"max_length": 100, "min_length": 50, "do_sample": False},
            "options": {"wait_for_model": True}
        }
        response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code == 200:
            summaries.append(response.json()[0]['summary_text'])
        else:
            return f"Summary generation failed: {response.text}"

    final_summary = " ".join(summaries)
    while len(final_summary.split()) > 100:
        payload["inputs"] = final_summary
        response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code == 200:
            final_summary = response.json()[0]['summary_text']
        else:
            return f"Summary generation failed: {response.text}"

    return final_summary


def generate_summary(content):
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {os.getenv('API_KEY')}"}

    paragraphs = content.split('\n\n')
    important_content = '\n'.join(paragraphs[:3])

    cleaned_content = ' '.join(important_content.split())
    if len(cleaned_content) > 2048:
        cleaned_content = cleaned_content[:2048]

    payload = {
        "inputs": cleaned_content,
        "parameters": {
            "max_length": 130,
            "min_length": 80,
            "length_penalty": 2.0,
            "num_beams": 4,
            "temperature": 0.7,
            "no_repeat_ngram_size": 3,
            "early_stopping": True
        },
        "options": {"wait_for_model": True}
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            summary = response.json()[0]['summary_text']

            summary = summary.strip()
            summary = summary.rstrip('.')
            summary = summary + "."

            return summary
        else:
            print(f"API Error: {response.status_code}")
            return ' '.join(cleaned_content.split()[:100]) + '...'
    except Exception as e:
        print(f"Summary generation error: {str(e)}")
        return cleaned_content[:300] + '...'
    

def generate_image(title):
    hf_api_url = "https://api-inference.huggingface.co/models/CompVis/stable-diffusion-v1-4"
    hf_headers = {"Authorization": f"Bearer {os.getenv('API_KEY')}"}
    hf_payload = {
            "inputs": title,
            "options": {"wait_for_model": True}
    }
    hf_response = requests.post(hf_api_url, headers=hf_headers, json=hf_payload)
        
    if hf_response.status_code == 200:
        try:
            image_data = base64.b64encode(hf_response.content).decode('utf-8')
            return image_data
        except Exception as e:
            print(f"Error processing Hugging Face image: {e}")
    else:
        print(f"Stable Diffusion API request failed with status code {hf_response.status_code}: {hf_response.text}")

    return ""