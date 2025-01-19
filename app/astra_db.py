import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from uuid import uuid4
from datetime import datetime

# Get the current directory of the script
current_directory = os.path.dirname(os.path.abspath(__file__))

# Astra DB credentials
CLIENT_ID = "TfwYhGSOuQRRPnbmpJBqKogu"
CLIENT_SECRET = "g+XOc+zl-sMDKf6bRLo_ZZxoKqeLOppmdqdY3h6a9jv2K4D9Ho_a5Dncb-8inioJT.iPROUR+i+dHfo7XybjZUQlXt.rZNmMnPPS6HPpasw1eD1qQdW5_Yub._leS0za"
SECURE_CONNECT_BUNDLE_PATH = os.path.join(current_directory, "secure-connect-swayyug.zip")
KEYSPACE = "default_keyspace"

# Auth provider
auth_provider = PlainTextAuthProvider(username=CLIENT_ID, password=CLIENT_SECRET)

# Cluster configuration
cluster = Cluster(
    cloud={
        "secure_connect_bundle": SECURE_CONNECT_BUNDLE_PATH
    },
    auth_provider=auth_provider
)

# Connect to the cluster
session = cluster.connect(KEYSPACE)

# Insert sample data
insert_query = """
    INSERT INTO user_queries (id, user_id, query, scraped_results, langflow_output, timestamp)
    VALUES (%s, %s, %s, %s, %s, %s)
"""
sample_data = (
    uuid4(),  # Generate a random UUID for the id
    "user123",  # Sample user_id
    "Sample query",  # Sample query
    "Scraped data",  # Sample scraped_results
    "Langflow output",  # Sample langflow_output
    datetime.now()  # Current timestamp
)

session.execute(insert_query, sample_data)
print("Sample data inserted successfully!")

# Query the table
rows = session.execute("SELECT * FROM user_queries")
print("\nData in user_queries table:")
for row in rows:
    print(row)

# Close the connection
cluster.shutdown()