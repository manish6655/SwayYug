import os
import time
from googleapiclient.discovery import build
from apify_client import ApifyClient

# YouTube API Setup
YOUTUBE_API_KEY = "AIzaSyBNhed45KURnjGK_MAhndqayc4mKYEm3VM"
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Apify (Reddit) Setup
APIFY_API_TOKEN = "apify_api_hIc2crbdqoTsUlszDwbNKcKhb1VNoy3IB7z8"
apify_client = ApifyClient(APIFY_API_TOKEN)

# Function to scrape YouTube data
def scrape_youtube(query, max_results=10):
    try:
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results
        )
        response = request.execute()
        return response["items"]
    except Exception as e:
        print(f"YouTube API Error: {e}")
        return []

# Function to scrape Reddit data using Apify
def scrape_reddit(query, max_results=10):
    try:
        run_input = {
            "query": query,
            "proxyConfiguration": {
                "useApifyProxy": True,
                "apifyProxyGroups": [],
            },
            "maxResults": max_results,
        }
        run = apify_client.actor("hIHt2e63CUiKjs2mw").call(run_input=run_input)
        dataset = apify_client.dataset(run["defaultDatasetId"]).iterate_items()
        return list(dataset)[:max_results]
    except Exception as e:
        print(f"Apify (Reddit) Error: {e}")
        return []

# Main function to scrape data from YouTube and Reddit
def scrape_all_platforms(query):
    print(f"Scraping data for query: {query}")

    # Scrape YouTube
    print("\nScraping YouTube...")
    youtube_data = scrape_youtube(query)
    print(f"Found {len(youtube_data)} YouTube results:")
    for item in youtube_data:
        print(f"- Title: {item['snippet']['title']}")
        print(f"  URL: https://www.youtube.com/watch?v={item['id']['videoId']}")

    # Scrape Reddit
    print("\nScraping Reddit...")
    reddit_data = scrape_reddit(query)
    print(f"Found {len(reddit_data)} Reddit results:")
    for item in reddit_data:
        print(f"- Title: {item.get('title', 'No Title')}")
        print(f"  URL: {item.get('url', 'No URL')}")

# Run the scraper
if __name__ == "__main__":
    query = "cybersecurity"  # Replace with your query
    scrape_all_platforms(query)