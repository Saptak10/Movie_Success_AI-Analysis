import pandas as pd
import numpy as np
import ast
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sentence_transformers import SentenceTransformer

def get_sbert_embedding(review_str, model):
    try:
        reviews = ast.literal_eval(review_str)
        if not reviews:
            return np.zeros(384)
        
        texts = [f"{r.get('title', '')}. {r.get('body', '')}" for r in reviews]
        
        embeddings = model.encode(texts)
        return np.mean(embeddings, axis=0)
    except:
        return np.zeros(384)

if __name__ == "__main__":

    df = pd.read_csv("data/us_movies_final_with_cast_directors.csv")
    df = df.drop(columns=['directors', 'writers'])

    print("Loading SBERT model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("Generating SBERT embeddings...")
    embeddings_list = []
    total_rows = len(df)
    for idx, review_str in enumerate(df['reviews']):
        embeddings_list.append(get_sbert_embedding(review_str, model))
        if (idx + 1) % 1000 == 0:
            print(f"Processed {idx + 1}/{total_rows} reviews...")
    
    embedding_df = pd.DataFrame(embeddings_list, columns=[f'review_emb_{i}' for i in range(384)])
    df = pd.concat([df, embedding_df], axis=1)
    print(f"SBERT embeddings added. Shape: {embedding_df.shape}")

    print("Splitting data into train and test sets...")
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    print(f"Training set size: {len(train_df)}")
    print(f"Test set size: {len(test_df)}")

    print("Saving train and test files...")
    train_df.to_csv("data/train_movies.csv", index=False)
    test_df.to_csv("data/test_movies.csv", index=False)
    print("Saved data/train_movies.csv and data/test_movies.csv")

