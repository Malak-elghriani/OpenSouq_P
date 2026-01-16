import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from urllib.parse import urlparse, parse_qs

def clean_data(input_csv, output_csv):
    """
    Cleans and standardizes the property data.
    """
    df = pd.read_csv(input_csv)

    # Drop unnecessary columns
    columns_to_drop = [
        'category', 'reference_id', 'payment_method', 'main_amenities', 'nearby',
        'additional_amenities', 'land_area', 'property_status', 'country',
        'real_estate_type', 'floor', 'zoned_for', 'number_of_floors'
    ]
    df.drop(columns=columns_to_drop, inplace=True, errors='ignore')

    # Remove specific subcategory
    df = df[df['subcategory'] != 'Farms & Chalets for Sale']

    # Handle missing values
    for col in ['bedrooms', 'bathrooms', 'lister_type']:
        df[col] = df[col].fillna(df[col].mode()[0])

    fill_value_columns = {'facade': 'Unknown', 'property_mortgaged?': 'No'}
    df.fillna(value=fill_value_columns, inplace=True)

    # Standardize categorical columns
    bedroom_mapping = {
        'More Than 6 Bedrooms': 7, 'Studio': 1, '1 Bedroom': 1, '2 Bedrooms': 2,
        '3 Bedrooms': 3, '4 Bedrooms': 4, '5 Bedrooms': 5
    }
    bathroom_mapping = {
        'More Than 6 Bathrooms': 7, 'One Bathroom': 1, '2 Bathrooms': 2,
        '3 Bathrooms': 3, '4 Bathrooms': 4, '5 Bathrooms': 5
    }
    df['bedrooms'] = df['bedrooms'].replace(bedroom_mapping).astype(float)
    df['bathrooms'] = df['bathrooms'].replace(bathroom_mapping).astype(float)

    # Clean and convert surface area to numeric
    df['surface_area'] = (
        df['surface_area']
        .astype(str)
        .str.replace(' meter square', '', regex=False)
        .apply(pd.to_numeric, errors='coerce')
    )

    df.to_csv(output_csv, index=False)

def transform_cleaned_data(input_csv, output_csv):
    """
    Transforms the cleaned data for further analysis.
    """
    df = pd.read_csv(input_csv)

    # Convert to boolean
    boolean_columns = {'furnished?': 'Furnished', 'property_mortgaged?': 'Yes'}
    for col, true_value in boolean_columns.items():
        df[col] = df[col].apply(lambda x: x == true_value)

    # Convert to numeric, coercing errors
    df['building_age'] = df['building_age'].astype(str).str.extract('(\\d+)').astype(float) # Extracts numbers from strings like '5 years'
    df['price'] = pd.to_numeric(df['price'], errors='coerce')


    # Debugging: Check initial values in 'building_age'
    print("Initial 'building_age' values:")
    print(df['building_age'].head())

    # Convert to numeric, coercing errors
    df['building_age'] = df['building_age'].astype(str).str.extract('(\\d+)').astype(float)  # Extracts numbers from strings like '5 years'

    # Debugging: Check transformed values in 'building_age'
    print("Transformed 'building_age' values:")
    print(df['building_age'].head())

    # Impute missing building age values
    df['building_age'] = df.groupby('neighborhood')['building_age'].transform(lambda x: x.fillna(x.median()))
    df['building_age'].fillna(df['building_age'].median(), inplace=True)

    # Remove rows with non-numeric or missing prices
    df.dropna(subset=['price'], inplace=True)

    # Filter data based on realistic values
    df = df[(df['price'] >= 150000) & (df['price'] <= 65000000)]
    df = df[(df['surface_area'] >= 50) & (df['surface_area'] <= 10000)]
    # Remove apartments for sale with surface area > 250 and bedrooms < 4
    df = df[~((df['subcategory'] == 'Apartment for Sale') & (df['surface_area'] > 250) & (df['bedrooms'] < 4))]

    # Extract latitude and longitude from location links
    df = extract_lat_long_from_location(df, 'location')

    # Remove impossible location values (Libya bounds)
    df = df[(df['latitude'] >= 19.5) & (df['latitude'] <= 33)]
    df = df[(df['longitude'] >= 9) & (df['longitude'] <= 25)]

    # Drop unnecessary columns
    df.drop(columns=['location'], errors='ignore', inplace=True)

    df.to_csv(output_csv, index=False)

def eda(input_csv):
    df = pd.read_csv(input_csv)
    print("\nShape of the DataFrame:")
    print(df.shape)
    print("\nBasic Information After Cleaning:")
    print(df.info())
    print("\nFirst few rows of the DataFrame:")
    print(df.head())
    print("\nSummary Statistics:")
    print(df.describe())
    print("\nTypes")
    print(df.dtypes)
    print("\nMissing Vlues per column: ")
    print(df.isnull().sum())
    print("\nNumber of Duplicates")
    print(df.duplicated().sum())
    print("\nCount of each value in 'facade' column")
    print(df['facade'].value_counts())
    print("\nCount of each value in 'lister_type' column")
    print(df['lister_type'].value_counts())
    print("\nCount of each value in 'subcategory' column")
    print(df['subcategory'].value_counts())

def basic_plotting(input_csv):
    df = pd.read_csv(input_csv)
    # Plot distributions of numeric columns
    numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
    for column in numeric_columns:
        plt.figure(figsize=(8, 5))
        sns.histplot(df[column], kde=True, bins=30)
        plt.title(f"Distribution of {column}")
        plt.xlabel(column)
        plt.ylabel("Frequency")
        plt.savefig(f"distribution_{column}.png")
        plt.close()

    # Plot correlations between numeric columns
    if len(numeric_columns) > 1:
        plt.figure(figsize=(10, 8))
        correlation_matrix = df[numeric_columns].corr()
        sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Correlation Matrix")
        plt.savefig("correlation_matrix.png")
        plt.close()

    # Scatter plot for Latitude and Longitude if present
    if 'latitude' in df.columns and 'longitude' in df.columns:
        plt.figure(figsize=(8, 6))
        sns.scatterplot(x='longitude', y='latitude', data=df)
        plt.title("Geographical Distribution")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.savefig("geographical_distribution.png")
        plt.close()

def outlier_detection(input_csv, column):
    """Graphs a box and whiskers plot for price grouped by subcategory."""
    df = pd.read_csv(input_csv)
    plt.figure(figsize=(12, 8))
    sns.boxplot(x=column, y='price', data=df)
    plt.title('Price Distribution by: ' + column)
    plt.xlabel(column)
    plt.ylabel('Price')
    plt.xticks(rotation=45)
    plt.savefig("price_distribution_by_" + column + "_clean_2.png")
    plt.close()

def extract_lat_long_from_location(df, location_column):
    """
    Extracts latitude and longitude from Google Maps links in the specified column.

    Args:
        df (pd.DataFrame): The DataFrame containing the location column.
        location_column (str): The name of the column with Google Maps links.

    Returns:
        pd.DataFrame: DataFrame with added 'latitude' and 'longitude' columns.
    """
    latitudes = []
    longitudes = []

    for link in df[location_column]:
        try:
            # Parse the URL and extract the query parameters
            parsed_url = urlparse(link)
            query_params = parse_qs(parsed_url.query)

            # Extract the 'query' parameter containing the coordinates
            if 'query' in query_params:
                coords = query_params['query'][0].split(',')
                if len(coords) == 2:
                    latitudes.append(float(coords[0]))
                    longitudes.append(float(coords[1]))
                else:
                    latitudes.append(None)
                    longitudes.append(None)
            else:
                latitudes.append(None)
                longitudes.append(None)
        except Exception as e:
            latitudes.append(None)
            longitudes.append(None)

    df['latitude'] = latitudes
    df['longitude'] = longitudes
    return df

if __name__ == "__main__":
    # print("eda before cleaning")
    # eda("processed_data.csv")

    clean_data("processed_data.csv", "cleaned_data.csv")
    # print("eda after clean_data() was preformed")
    # eda("cleaned_data.csv")

    transform_cleaned_data("cleaned_data.csv", "cleaned_data.csv")
    print("eda after transform_cleaned_data() was preformed")
    eda("cleaned_data.csv")

    # # Load your dataset
    # df = pd.read_csv('cleaned_data.csv')
    # df.to_csv('cleaned_data.csv', index=False)  # Replace 'cleaned_file.csv' with your desired output file name

    # basic_plotting("cleaned_data.csv")
    # outlier_detection("cleaned_data.csv")