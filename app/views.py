from django.shortcuts import render
import http.client
import json
import requests
from urllib.parse import quote

# Constants
API_KEY = "RDPycn2DkoMo8a7aHjFzRY98kzfDjBPn"
LANGFLOW_URL = "https://api.langflow.astra.datastax.com/lf/33924fc4-c206-4c8b-9d46-36917ef56de0/api/v1/run/930ed97c-43f8-4a49-bdce-2d757858e3b0?stream=false"

# Fetch search results from SerpAPI
def fetch_search_results(query):
    encoded_query = quote(query)
    params = f"engine=google&api_key={API_KEY}&q={encoded_query}"
    conn = http.client.HTTPSConnection("serpapi.webscrapingapi.com")
    try:
        conn.request("GET", f"/v2?{params}")
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        conn.close()

# Assign rating based on description length
def assign_rating(description):
    if not description or description == "No Description":
        return "No Rating Found"
    words = description.split()
    if len(words) < 10:
        return "Low (1/5)"
    elif len(words) < 20:
        return "Medium (3/5)"
    else:
        return "High (5/5)"

# Combine scraped results into a single string (including rating)
def prepare_langflow_input(results):
    combined_input = ""
    for result in results[:10]:  # Limit to top 10 results
        title = result.get("title", "No Title")
        description = result.get("description", "No Description")
        source = result.get("display_link", "No Source Found")
        rating = assign_rating(description)  # Add rating
        combined_input += f"Ads: {title}\nDescription: {description}\nSource: {source}\nRating: {rating}\n------\n"
    return combined_input

# Call LangFlow API
def call_langflow_api(data):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LANGFLOW_TOKEN}'
    }
    payload = {
        "input_value": data,
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": {
            "ChatInput-URl3a": {},
            "Prompt-QKyAE": {},
            "ChatOutput-uI7hu": {},
            "GroqModel-MLvep": {}
        }
    }
    response = requests.post(LANGFLOW_URL, headers=headers, json=payload)
    return response.json()
def index(request):
    if request.method == "POST":
        # Step 1: Get user input
        query = request.POST.get("query", "")
        print(f"Fetching results for '{query}'...")

        # Step 2: Fetch results from SerpAPI
        response = fetch_search_results(query)
        if not response or "organic" not in response:
            return render(request, "index.html", {"error": "No results found."})

        # Step 3: Prepare input for LangFlow (including rating)
        langflow_input = prepare_langflow_input(response["organic"])
        print("\nScraped Results (Input to LangFlow):")
        print(langflow_input)

        # Step 4: Call LangFlow API
        print("\nCalling LangFlow API...")
        langflow_output = call_langflow_api(langflow_input)

        # Step 5: Pass results to the template
        return render(request, "index.html", {
            "query": query,
            "scraped_results": langflow_input,
            "langflow_output": langflow_output  # Only the output text
        })

    # Render the form for GET requests
    return render(request, "index.html")