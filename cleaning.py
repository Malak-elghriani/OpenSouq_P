import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

def clean_data(input_csv, output_csv):
    """Cleans and standardizes the property data."""
    df = pd.read_csv(input_csv)

    # Handle missing values
    df['bedrooms'] = df['bedrooms'].fillna(df['bedrooms'].mode()[0])
    df['bathrooms'] = df['bathrooms'].fillna(df['bathrooms'].mode()[0])
    df['furnished?'] = df['furnished?'].fillna('Unfurnished')
    df['property_mortgaged?'] = df['property_mortgaged?'].fillna('No')
    df['lister_type'] = df['lister_type'].fillna(df['lister_type'].mode()[0])
    df['payment_method'] = df['payment_method'].fillna('Cash')
    df = df.dropna(subset=['surface_area', 'land_area'])

    # Standardize categorical columns
    df['bedrooms'] = df['bedrooms'].replace({'More Than 6 Bedrooms': 7, 'Studio': 1, '1 Bedroom': 1, '2 Bedrooms': 2, '3 Bedrooms': 3, '4 Bedrooms': 4, '5 Bedrooms': 5, 'More Than 6 Bedrooms': 7})
    df['bathrooms'] = df['bathrooms'].replace({'More Than 6 Bathrooms': 7, 'One Bathroom': 1, '2 Bathrooms': 2, '3 Bathrooms': 3, '4 Bathrooms': 4, '5 Bathrooms': 5})

    # Clean and convert to numeric
    for col in ['surface_area', 'land_area']:
        df[col] = df[col].astype(str).str.replace(' meter square', '', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['bedrooms'] = pd.to_numeric(df['bedrooms'], errors='coerce')
    df['bathrooms'] = pd.to_numeric(df['bathrooms'], errors='coerce')


    df.to_csv(output_csv, index=False)

def transform_cleaned_data(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    # Convert to boolean
    df['furnished?'] = df['furnished?'].apply(lambda x: True if x == 'Furnished' else False)
    df['property_mortgaged?'] = df['property_mortgaged?'].apply(lambda x: True if x == 'Yes' else False)

    # Convert to numeric, coercing errors
    df['number_of_floors'] = pd.to_numeric(df['number_of_floors'], errors='coerce')
    df['building_age'] = df['building_age'].astype(str).str.extract('(\d+)').astype(float) # Extracts numbers from strings like '5 years'

    # Remove columns with no non-null values
    df.dropna(axis=1, how='all', inplace=True)

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
    print("\nCount of each value in 'payment_method' column")
    print(df['payment_method'].value_counts())
    print("\nCount of each value in 'category' column")
    print(df['category'].value_counts())
    print("\nCount of each value in 'subcategory' column")
    print(df['subcategory'].value_counts())
    print("\nCount of each value in 'property_status' column")
    print(df['property_status'].value_counts())

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
        plt.show()

    # Plot correlations between numeric columns
    if len(numeric_columns) > 1:
        plt.figure(figsize=(10, 8))
        correlation_matrix = df[numeric_columns].corr()
        sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Correlation Matrix")
        plt.show()

    # Scatter plot for Latitude and Longitude if present
    if 'latitude' in df.columns and 'longitude' in df.columns:
        plt.figure(figsize=(8, 6))
        sns.scatterplot(x='longitude', y='latitude', data=df)
        plt.title("Geographical Distribution")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.show()

if __name__ == "__main__":
    # clean_data("processed_data.csv", "cleaned_data.csv")
    # print("Data cleaning complete. Cleaned data saved to cleaned_data.csv")
    # transform_cleaned_data("cleaned_data.csv", "cleaned_data.csv")
    eda("cleaned_data.csv")
    # basic_plotting("cleaned_data.csv")