import os
import http.client
import json
import requests
from urllib.parse import quote
from uuid import uuid4
from datetime import datetime
from django.shortcuts import render
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# Get the current directory of the script
current_directory = os.path.dirname(os.path.abspath(__file__))

# Astra DB credentials
CLIENT_ID = "TfwYhGSOuQRRPnbmpJBqKogu"
CLIENT_SECRET = "g+XOc+zl-sMDKf6bRLo_ZZxoKqeLOppmdqdY3h6a9jv2K4D9Ho_a5Dncb-8inioJT.iPROUR+i+dHfo7XybjZUQlXt.rZNmMnPPS6HPpasw1eD1qQdW5_Yub._leS0za"
SECURE_CONNECT_BUNDLE_PATH = os.path.join(current_directory, "secure-connect-swayyug.zip")
KEYSPACE = "default_keyspace"

# Constants (hardcoded for now)
API_KEY = "RDPycn2DkoMo8a7aHjFzRY98kzfDjBPn"
LANGFLOW_URL = "https://api.langflow.astra.datastax.com/lf/33924fc4-c206-4c8b-9d46-36917ef56de0/api/v1/run/930ed97c-43f8-4a49-bdce-2d757858e3b0?stream=False"
LANGFLOW_TOKEN = "AstraCS:smRcHcXNOwdhzyZTeZpZvFqY:e05ba8a87acaee2f62b4986957ff139271c6b443dabc7437ff264dd2e3cc8d00"

# Create Astra client
def get_astra_client():
    try:
        auth_provider = PlainTextAuthProvider(CLIENT_ID, CLIENT_SECRET)
        cluster = Cluster(
            cloud={"secure_connect_bundle": SECURE_CONNECT_BUNDLE_PATH},
            auth_provider=auth_provider
        )
        session = cluster.connect(KEYSPACE)
        return session, cluster
    except Exception as e:
        print(f"Error connecting to Astra DB: {e}")
        return None, None

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

def insert_query_result(user_id, query, scraped_results, langflow_output):
    session, cluster = get_astra_client()
    if not session:
        return

    try:
        session.execute("""
            INSERT INTO user_queries (id, user_id, query, scraped_results, langflow_output, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            uuid4(),  
            user_id,  
            query,  
            scraped_results,  
            langflow_output,  
            datetime.now()  
        ))
        print("Data inserted into Astra DB successfully.")
    except Exception as e:
        print(f"Error inserting data into Astra DB: {e}")
    finally:
        cluster.shutdown()

def get_existing_query_result(user_id, query):
    session, cluster = get_astra_client()
    if not session:
        return None

    try:
        result = session.execute("""
            SELECT scraped_results, langflow_output
            FROM user_queries
            WHERE user_id = %s AND query = %s
            LIMIT 1
        """, (user_id, query))

        if result:
            return result.one()
        else:
            return None
    except Exception as e:
        print(f"Error querying Astra DB: {e}")
        return None
    finally:
        cluster.shutdown()

# Index view
def index(request):
    if request.method == "POST":
        query = request.POST.get("query", "")
        user_id = request.user.id if request.user.is_authenticated else "anonymous"
        
        # Check if the query already exists in DB
        existing_result = get_existing_query_result(user_id, query)
        if existing_result:
            return render(request, "index.html", {
                "query": query,
                "scraped_results": existing_result.scraped_results,
                "langflow_output": existing_result.langflow_output,
            })
        
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
        
        # Insert query and results into Astra DB
        insert_query_result(user_id, query, langflow_input, main_output)
        
        return render(request, "index.html", {
            "query": query,
            "scraped_results": langflow_input, 
            "langflow_output": main_output,
        })
    
    return render(request, "index.html")
