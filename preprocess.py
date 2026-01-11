import pandas as pd
import requests
import re
import json

def clean_and_process_data(json_file, unclean_csv, output_csv):
    # Load the JSON data into a DataFrame
    df = pd.read_json(json_file)

    # Save the unclean version of the data
    df.to_csv(unclean_csv, index=False)

    # Display basic information before cleaning
    print("\nBasic Information BEFORE Cleaning:")
    print(df.info())

    # Drop rows with missing prices
    df = df.dropna(subset=['price'])

    # Clean and standardize the 'price' column
    df['price'] = df['price'].replace(r'[^0-9]', '', regex=True)
    df['price'] = pd.to_numeric(df['price'], errors='coerce')  # Convert to numeric, invalid values become NaN

    # Convert 'attributes' column to strings temporarily to handle duplicates
    df['attributes'] = df['attributes'].apply(lambda x: json.dumps(x) if isinstance(x, dict) else x)

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Parse JSON-like strings in the 'attributes' column into separate columns
    def parse_attributes(attr):
        try:
            return json.loads(attr) if isinstance(attr, str) else {}
        except json.JSONDecodeError:
            return {}

    attributes_parsed = df['attributes'].apply(parse_attributes)
    attributes_df = pd.json_normalize(attributes_parsed)
    df = pd.concat([df, attributes_df], axis=1)
    df = df.drop(columns=['attributes'])  # Drop the original 'attributes' column

    # Validate and clean the 'location' column
    df['location'] = df['location'].apply(lambda x: x if isinstance(x, str) and x.startswith('http') else None)

    # Remove the 'url' column
    df = df.drop(columns=['url'])

    # Standardize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    #remove all catagories that aren't properties for sale
    df = df[df['category'] == 'Property For Sale']

    # Remove columns with zero non-null values
    df = df.loc[:, df.notna().any()]

    # Display basic information after cleaning
    print("\nBasic Information After Cleaning:")
    print(df.info())


    # Save the cleaned and processed data to a CSV file
    df.to_csv(output_csv, index=False)


def show_unique_values(csv_file, column_name):
    """
    Reads a CSV file and prints all unique values of a specified column.

    Args:
        csv_file (str): The path to the CSV file.
        column_name (str): The name of the column to check.
    """
    try:
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(csv_file)
        
        # Check if the column exists
        if column_name in df.columns:
            # Get the unique values
            unique_values = df[column_name].unique()
            
            print(f"Unique values in column '{column_name}':")
            for value in unique_values:
                print(value)
        else:
            print(f"Error: Column '{column_name}' not found in the CSV file.")
            print(f"Available columns are: {list(df.columns)}")
            
    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{csv_file}' is empty.")
    except Exception as e:
        print(f"An error occurred: {e}")



if __name__ == "__main__":
    clean_and_process_data("property_data.json", "unclean_data.csv", "processed_data.csv")
    # show_unique_values("processed_data.csv", "category")

    # df = pd.read_csv("processed_data.csv")
    # print(df.info())