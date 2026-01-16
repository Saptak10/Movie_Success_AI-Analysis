import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from scipy.sparse import hstack, csr_matrix
from sklearn.preprocessing import StandardScaler
import joblib

def train_model():
    print("Loading train and test data...")
    train_df = pd.read_csv("data/train_movies.csv")
    test_df = pd.read_csv("data/test_movies.csv")

    target_col = 'revenue'
    
    train_df = train_df.dropna(subset=[target_col])
    test_df = test_df.dropna(subset=[target_col])

    y_train = train_df[target_col]
    y_test = test_df[target_col]

    tfidf_cols = ['genres', 'director_names', 'writer_names', 'cast_members']
    
    train_features_list = []
    test_features_list = []

    print("Processing TF-IDF features...")
    
    if 'genres' in train_df.columns:
        train_df['genres'] = train_df['genres'].str.replace(',', ' ')
        test_df['genres'] = test_df['genres'].str.replace(',', ' ')

    for col in tfidf_cols:
        if col in train_df.columns:
            print(f"  - Vectorizing {col}...")
            train_df[col] = train_df[col].fillna('')
            test_df[col] = test_df[col].fillna('')

            vectorizer = TfidfVectorizer(max_features=5000, stop_words='english') 
            
            X_train_tfidf = vectorizer.fit_transform(train_df[col])
            X_test_tfidf = vectorizer.transform(test_df[col])
            
            train_features_list.append(X_train_tfidf)
            test_features_list.append(X_test_tfidf)
            
            print(f"    {col} Train matrix shape: {X_train_tfidf.shape}")
            print(f"    {col} Test matrix shape: {X_test_tfidf.shape}")

    print("Processing numerical features...")
    
    sbert_cols = [c for c in train_df.columns if c.startswith('review_emb_')]
    
    other_num_cols = ['budget', 'runtimeMinutes', 'startYear']
    
    num_cols = other_num_cols + sbert_cols
    
    for col in other_num_cols:
        train_df[col] = train_df[col].replace(0, np.nan)
        test_df[col] = test_df[col].replace(0, np.nan)

    for col in other_num_cols:
        median_val = train_df[col].median()
        print(f"Imputing {col} with median: {median_val}")
        train_df[col] = train_df[col].fillna(median_val)
        test_df[col] = test_df[col].fillna(median_val)

    scaler = StandardScaler()
    X_train_num = scaler.fit_transform(train_df[num_cols])
    X_test_num = scaler.transform(test_df[num_cols])

    train_features_list.append(csr_matrix(X_train_num))
    test_features_list.append(csr_matrix(X_test_num))

    print("Stacking features...")
    X_train = hstack(train_features_list)
    X_test = hstack(test_features_list)

    print(f"Final Training Shape: {X_train.shape}")
    print(f"Final Testing Shape: {X_test.shape}")

    print("Training Ridge Regression model...")
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)

    print("Evaluating model...")
    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("\n--- Model Performance ---")
    print(f"RMSE: {rmse:,.2f}")
    print(f"MAE:  {mae:,.2f}")
    print(f"R2 Score: {r2:.4f}")

if __name__ == "__main__":
    train_model()
