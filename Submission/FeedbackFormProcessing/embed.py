import os
from google.cloud import bigquery
from vertexai.preview.language_models import TextEmbeddingModel
from concurrent.futures import ThreadPoolExecutor

# Set the environment variable for the service account key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = " "

# Initialize BigQuery client
client = bigquery.Client(project=" ")

# Initialize the Vertex AI model
model = TextEmbeddingModel.from_pretrained("text-embedding-005")

# Query to fetch rows with empty embeddings
query = """
SELECT ID, Survey 
FROM ` `
WHERE ARRAY_LENGTH(Embedding) = 0
"""

print("Fetching rows with empty embeddings...")
surveys = client.query(query).result()
print("Rows with empty embeddings fetched.")

# Define batch size
batch_size = 50 

def process_batch(batch):
    try:
        ids, surveys_text = zip(*batch)
        embedding_responses = model.get_embeddings(list(surveys_text))
        embeddings = [response.values for response in embedding_responses]

        for id_, embedding in zip(ids, embeddings):
            update_query = """
            UPDATE ` `
            SET Embedding = @embedding
            WHERE ID = @id
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ArrayQueryParameter("embedding", "FLOAT64", embedding),
                    bigquery.ScalarQueryParameter("id", "INT64", id_)
                ]
            )
            client.query(update_query, job_config=job_config).result()
            print(f"Updated ID {id_} with embedding.")
    except Exception as e:
        print(f"Error processing batch: {e}")

# Create batches
batches = []
batch = []
for row in surveys:
    batch.append((row.ID, row.Survey))
    if len(batch) == batch_size:
        batches.append(batch)
        batch = []
if batch:
    batches.append(batch)

# Process batches in parallel
with ThreadPoolExecutor(max_workers=4) as executor: 
    executor.map(process_batch, batches)

print("Embedding process completed for rows with empty embeddings.")
