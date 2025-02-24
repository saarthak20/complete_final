import base64

import requests
import os
from dotenv import load_dotenv

import ssl

dotenv_loaded = load_dotenv()
if not dotenv_loaded:
    raise ValueError("❌ .env file not found or not loaded!")

WP_USERNAME = os.getenv("WP_USERNAME", "").strip()
WP_PASSWORD = os.getenv("WP_PASSWORD", "").strip()

auth = base64.b64encode(f"{WP_USERNAME}:{WP_PASSWORD}".encode()).decode()

def fetch_pending_posts(collection):
    """Fetch AI-generated posts that are marked as 'pending'."""
    return collection.find({"status": "pending"})

def fix_base64_padding(base64_string):
    """Fixes incorrect padding in a Base64 string."""
    missing_padding = len(base64_string) % 4
    if missing_padding:
        base64_string += "=" * (4 - missing_padding)
    return base64_string

def upload_image_from_base64(base64_image, filename="image.jpg"):
    """Uploads an image to WordPress using base64 data and returns the media ID."""
    
    url = f"http://localhost:8888/wordpress/wp-json/wp/v2/media"
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "image/jpeg"
    }

    try:
        base64_image = fix_base64_padding(base64_image)
        image_data = base64.b64decode(base64_image)
        response = requests.post(url, headers=headers, data=image_data)
        
        if response.status_code == 201:  # Success
            media_id = response.json().get("id")
            print(f"✅ Image uploaded successfully! Media ID: {media_id}")
            return media_id
        else:
            print(f"❌ Failed to upload image: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Error uploading image: {e}")
        return None

def upload_to_wordpress(post,collection):
    """Upload a single post to WordPress via REST API."""
    url = f"http://localhost:8888/wordpress/wp-json/wp/v2/posts"
    WP_SITE_URL = os.getenv("WP_SITE_URL", "").strip()
    WP_USERNAME = os.getenv("WP_USERNAME", "").strip()
    WP_PASSWORD = os.getenv("WP_PASSWORD", "").strip()

    auth = base64.b64encode(f"{WP_USERNAME}:{WP_PASSWORD}".encode()).decode()
    ssl._create_default_https_context = ssl._create_unverified_context
    print(f"✅ WP_SITE_URL: {WP_SITE_URL}")
    print(f"✅ DATABASE_NAME: Agent")
    print(f"✅ COLLECTION_NAME: news")

    category_id = post.get("category_id", 5)
    if isinstance(category_id, dict) and "$numberInt" in category_id:
        category_id = int(category_id["$numberInt"])
    else:
        category_id = int(category_id)  

    categories = [category_id] 

    print(f"Debug - Category ID being used: {categories}")
    
    featured_media_id = None
    if "image_url" in post and post["image_url"]:  
        print("Uploading Image...")
        featured_media_id = upload_image_from_base64(post["image_url"])

    post_data = {
        "title": post["title"],
        "content": post["content"],
        "status": "publish",
        "categories": categories,  
        "featured_media": featured_media_id 
    }

    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=post_data, headers=headers)

    if response.status_code == 201:
        print(f"✅ Successfully posted: {post['title']}")
        collection.update_one({"_id": post["_id"]}, {"$set": {"status": "published"}})
    else:
        print(f"❌ Failed to post: {post['title']}")
        print(response.json())

