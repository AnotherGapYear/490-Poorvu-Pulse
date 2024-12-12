from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import bigquery
from vertexai.preview.language_models import TextEmbeddingModel
import os

app = Flask(__name__)
CORS(app, resources={r"/feedback/*": {"origins": ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"]}})

# Set up credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = " "

# Initialize clients
client = bigquery.Client(project=" ")
model = TextEmbeddingModel.from_pretrained("text-embedding-005")

# Number of embeddings to retrieve
NUM_EMBEDDINGS = 100

def convert_to_embedding(text: str):
    embedding_response = model.get_embeddings([text])[0]
    return embedding_response.values

def format_feedback(result):
    formatted_surveys = []
    for index, row in enumerate(result):
        survey_text = row.Survey
        # Transform each survey's format
        survey_lines = survey_text.split('; Question: ')
        
        # Start with feedback form number
        formatted_text = f"Feedback form #{index + 1}:\n\n"
        
        # Process each question-answer pair
        for line in survey_lines:
            if line.strip():
                # Split question and answer
                parts = line.split('Answer: ')
                if len(parts) == 2:
                    question = parts[0].strip()
                    answer = parts[1].strip()
                    # Format with Answer on new line
                    formatted_text += f"Question: {question}\n"
                    formatted_text += f"Answer: {answer}\n\n"
        
        formatted_surveys.append(formatted_text.strip())
    
    # Join all formatted surveys with double newlines
    return "\n\n".join(formatted_surveys)

def search_feedback(query_embedding):
    search_query = """
    WITH valid_feedback AS (
        SELECT ID, Survey, Embedding
        FROM ` `
        WHERE ARRAY_LENGTH(Embedding) > 0
    ), similarity_scores AS (
        SELECT 
            Survey,
            (1 - COSINE_DISTANCE(Embedding, @query_embedding)) as similarity_score
        FROM valid_feedback
        ORDER BY similarity_score DESC
        LIMIT @num_embeddings
    )
    SELECT Survey, similarity_score
    FROM similarity_scores
    ORDER BY similarity_score DESC
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", query_embedding),
            bigquery.ScalarQueryParameter("num_embeddings", "INT64", NUM_EMBEDDINGS)
        ]
    )

    result = client.query(search_query, job_config=job_config).result()
    return format_feedback(result)

@app.route('/feedback/', methods=['GET'])
def get_feedback():
    try:
        query = request.args.get('query', type=str)
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400
        
        query_embedding = convert_to_embedding(query)
        combined_feedback = search_feedback(query_embedding)
        
        return jsonify({"combined_feedback": combined_feedback})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
