import pandas as pd
import os
import time
from parseRevenueMojo import add_revenue_to_dataframe

# Setup paths
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, "..", "data")
input_file = os.path.join(data_dir, "us_movies_with_reviews.csv")

if not os.path.exists(input_file):
    print(f"Error: {input_file} does not exist.")
    exit()

# Load just 5 movies
print("Loading 5 movies for testing...")
df = pd.read_csv(input_file).head(5)

# Define a temporary output file
output_file = os.path.join(data_dir, "test_speed_output.csv")
if os.path.exists(output_file):
    os.remove(output_file)

print("Starting processing...")
start_time = time.time()

# Run the function
df_result = add_revenue_to_dataframe(df, output_file)

end_time = time.time()
print(f"Processed 5 movies in {end_time - start_time:.2f} seconds")
print(df_result[['tconst', 'budget', 'revenue']])
