# News Scraper & Publisher

An automated news scraping and publishing tool that collects articles from Deccan Herald, processes them using AI, and can publish them to a WordPress site.

## Features

- Scrapes local (Karnataka) and national (India) news articles
- Async operation for efficient scraping
- AI-powered article summarization using Hugging Face API
- AI image generation for articles
- MongoDB integration for data storage
- WordPress publishing capability via REST API


## Project Structure

- `main.py`: News scraping script with NewsAgent class
- `process.py`: Article processing with AI summarization and image generation, and SEO keys (those are stored in MONGO_DB data but for some reason we couldn't upload it in local website)
- `publish.py`: WordPress publishing functionality
- `.env`: Environment variables (not tracked in git)

## Usage

## Quick Setup Guide

### 1. Set Up Local Server
1. Install XAMPP (Windows) or MAMP (Mac)
2. Start Apache and MySQL services
3. Keep note of your local server port (usually 8888 for MAMP or 80 for XAMPP)

### 2. Install WordPress
1. Import the provided .wpress file:
   - Install WordPress on your local server
   to download wpress, install it from the given google_drive- https://drive.google.com/drive/folders/1pQxGpVHfCdBZJ9S0iMkeXMj7h0whsQTv?usp=sharing
   - Install "All-in-One WP Migration" plugin
   - Go to All-in-One WP Migration > Import
   - Import the provided .wpress file
   - Click "Save Permalinks" when prompted
   
  2. Wodepress account username and password:
    - username : saarthakAS
    - password : Sah*shA#Saa&jaT@123
  
### 3. Scraping News
Run the main script:

```
pip install -r requirments.txt
```

```bash
python main.py
```

Choose from:
1. Local News (Karnataka/Bengaluru)
2. Global News (India)
3. Exit

### 4. Access the Website
- Open your browser and go to:
  - MAMP: http://localhost:8888/wordpress
  - XAMPP: http://localhost/wordpress

## Features Explained

### News Scraping
- Asynchronous scraping for better performance
- Smart rate limiting to avoid server overload
- Automatic error handling and retries

### Article Processing
- AI-powered article summarization
- Image generation based on article titles
- Category classification
- MongoDB storage with status tracking

### Publishing
- WordPress REST API integration
- Automatic image uploads
- Category mapping
- Status updates in MongoDB

## Dependencies

All dependencies are automatically installed by Replit:
- aiohttp
- beautifulsoup4
- pymongo
- python-dotenv
- requests
- urllib3

## License

MIT