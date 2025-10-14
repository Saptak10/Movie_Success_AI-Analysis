import pandas as pd
import os

def analyze_budget_coverage(file_path):
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    try:
        # Load the dataset
        df = pd.read_csv(file_path)
        
        # Calculate statistics
        total_rows = len(df)
        if 'budget' in df.columns:
            non_null_budget = df['budget'].count()
            missing_budget = total_rows - non_null_budget
            percent_missing = (missing_budget / total_rows) * 100
            
            # Report results
            print(f"--- Analysis of {file_path} ---")
            print(f"Total Movies: {total_rows}")
            print(f"Movies with Budget Data: {non_null_budget}")
            print(f"Missing Budget Data: {missing_budget}")
            print(f"Percentage Missing: {percent_missing:.2f}%")
        else:
            print(f"Column 'budget' not found in {file_path}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "..", "data")
    
    # Analyze Mojo file
    print("Mojo Data Analysis:")
    csv_path_mojo = os.path.join(data_dir, 'us_movies_with_revenue_and_budget_mojo.csv')
    analyze_budget_coverage(csv_path_mojo)
    
    print("\n" + "="*30 + "\n")

    # Analyze TMDb file
    print("TMDb Data Analysis (100 movies sample):")
    csv_path_tmdb = os.path.join(data_dir, 'us_movies_with_financials_tmdb.csv')
    analyze_budget_coverage(csv_path_tmdb)
