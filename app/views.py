import os
import http.client
import json
import requests
from urllib.parse import quote
from datetime import datetime
from django.shortcuts import render

# Constants (hardcoded for now)
API_KEY = "RDPycn2DkoMo8a7aHjFzRY98kzfDjBPn"
LANGFLOW_URL = "https://api.langflow.astra.datastax.com/lf/33924fc4-c206-4c8b-9d46-36917ef56de0/api/v1/run/930ed97c-43f8-4a49-bdce-2d757858e3b0?stream=False"
LANGFLOW_TOKEN = "AstraCS:smRcHcXNOwdhzyZTeZpZvFqY:e05ba8a87acaee2f62b4986957ff139271c6b443dabc7437ff264dd2e3cc8d00"

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
        print(f"An error occurred while fetching search results: {e}")
        return None
    finally:
        conn.close()

def prepare_langflow_input(results):
    combined_input = ""
    for result in results[:10]:  # Limit to top 10 results
        title = result.get("title", "No Title")
        description = result.get("description", "No Description")
        source = result.get("display_link", "No Source Found")
        combined_input += f"Title: {title}\nDescription: {description}\nSource: {source}\n------\n"
    return combined_input

def call_langflow_api(data):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LANGFLOW_TOKEN}'
    }
    payload = {
        "input_value": data,
        "output_type": "chat",
        "input_type": "chat",
    }
    try:
        response = requests.post(LANGFLOW_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error while calling LangFlow API: {e}")
        return {"error": "LangFlow API request failed."}

# Index view
def index(request):
    if request.method == "POST":
        query = request.POST.get("query", "")
        
        # Fetch the search results
        response = fetch_search_results(query)
        if not response or "organic" not in response:
            return render(request, "index.html", {"error": "No search results found."})
        
        # Prepare LangFlow input from the search results
        langflow_input = prepare_langflow_input(response["organic"])
        
        # Call LangFlow API with the input
        langflow_output = call_langflow_api(langflow_input)
        if "error" in langflow_output:
            return render(request, "index.html", {"error": langflow_output["error"]})
        
        # Extract the final result from LangFlow output
        main_output = langflow_output.get("outputs", [])[0].get("outputs", [])[0].get("results", {}).get("message", {}).get("text", "")
        
        return render(request, "index.html", {
            "query": query,
            "scraped_results": langflow_input, 
            "langflow_output": main_output,
        })
    return render(request, "index.html")
