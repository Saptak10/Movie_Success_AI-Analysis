import pandas as pd
import numpy as np
import ast
from sentence_transformers import SentenceTransformer
import os

def parse_reviews(review_str):
    """
    Parses the stringified list of reviews into a Python list.
    """
    if pd.isna(review_str) or review_str == '':
        return []
    try:
        # The data seems to use single quotes which ast.literal_eval handles well for python literals
        return ast.literal_eval(review_str)
    except (ValueError, SyntaxError):
        print(f"Warning: Could not parse review string: {review_str[:50]}...")
        return []

def generate_embeddings():
    # File paths
    input_file = 'data/us_movies_with_revenue_and_budget_3_source.csv'
    output_file = 'data/us_movies_with_review_vectors.csv'

    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found.")
        return

    print("Loading data...")
    df = pd.read_csv(input_file)
    
    print("Loading SBERT model...")
    # Load a pre-trained model. 'all-MiniLM-L6-v2' produces 384-dimensional vectors.
    model = SentenceTransformer('all-MiniLM-L6-v2')
    vector_dim = 384

    print("Processing reviews...")
    
    review_vectors = []
    
    for index, row in df.iterrows():
        reviews_data = parse_reviews(row['reviews'])
        
        if not reviews_data:
            # If no reviews, use a zero vector
            review_vectors.append(np.zeros(vector_dim))
            continue

        review_texts = []
        for review in reviews_data:
            # Combine title and body. Handle potential missing keys or None values.
            title = review.get('title', '') or ''
            body = review.get('body', '') or ''
            full_text = f"{title}. {body}".strip()
            if full_text:
                review_texts.append(full_text)
        
        if not review_texts:
            review_vectors.append(np.zeros(vector_dim))
            continue

        # Encode all reviews for this movie
        embeddings = model.encode(review_texts)
        
        # Sum the vectors to combine them
        combined_vector = np.sum(embeddings, axis=0)
        
        review_vectors.append(combined_vector)

        if index % 100 == 0:
            print(f"Processed {index} movies...")

    # Convert list of arrays to a DataFrame with separate columns
    print("Expanding vectors into columns...")
    embedding_df = pd.DataFrame(review_vectors, columns=[f'embedding_{i}' for i in range(vector_dim)])
    
    # Concatenate with original dataframe
    df_final = pd.concat([df, embedding_df], axis=1)

    print(f"Saving results to {output_file}...")
    df_final.to_csv(output_file, index=False)
    print("Done.")

if __name__ == "__main__":
    generate_embeddings()
