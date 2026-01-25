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
    df = df[(df['surface_area'] >= 50) & (df['surface_area'] <= 1000)]
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
        plt.savefig(f"graphs/distribution_{column}.png")
        plt.close()

    # Plot correlations between numeric columns
    if len(numeric_columns) > 1:
        plt.figure(figsize=(10, 8))
        correlation_matrix = df[numeric_columns].corr()
        sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Correlation Matrix")
        plt.savefig("graphs/correlation_matrix.png")
        plt.close()

    # Scatter plot for Latitude and Longitude if present
    if 'latitude' in df.columns and 'longitude' in df.columns:
        plt.figure(figsize=(8, 6))
        sns.scatterplot(x='longitude', y='latitude', data=df)
        plt.title("Geographical Distribution")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.savefig("graphs/geographical_distribution.png")
        plt.close()

def outlier_detection(input_csv, category_column, value_column, save_extention):
    """Graphs a box and whiskers plot for value_column grouped by category_column."""
    df = pd.read_csv(input_csv)
    plt.figure(figsize=(12, 8))
    sns.boxplot(x=category_column, y=value_column, data=df)
    plt.title('Price Distribution by: ' + category_column)
    plt.xlabel(category_column)
    plt.ylabel(value_column)
    plt.xticks(rotation=45)
    plt.savefig(f"graphs/box_plot_{value_column}_by_{category_column + save_extention}.png")
    plt.close()

def remove_outliers_by_category(input_csv, output_csv, category_column, value_column):
    """Removes outliers in the value_column within each category of the category_column."""
    df = pd.read_csv(input_csv)

    def remove_outliers(group):
        q1 = group[value_column].quantile(0.25)
        q3 = group[value_column].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        return group[(group[value_column] >= lower_bound) & (group[value_column] <= upper_bound)]

    filtered_df = df.groupby(category_column, group_keys=False).apply(remove_outliers)
    filtered_df.to_csv(output_csv, index=False)
    print(f"Outliers removed and data saved to {output_csv}")

def extract_lat_long_from_location(df, location_column):
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

def plot_null_values_bar_chart(csv_file):
    """
    Creates a bar chart showing the number of null values in each column of a CSV file.

    Args:
        csv_file (str): Path to the CSV file.
    """
    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Calculate the number of null values per column
    null_counts = df.isnull().sum()

    # Plot the bar chart
    plt.figure(figsize=(10, 6))
    null_counts.plot(kind='bar', color='skyblue')
    plt.title('Number of Null Values per Column')
    plt.xlabel('Columns')
    plt.ylabel('Number of Null Values')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('graphs/null_values_bar_chart.png')
    plt.close()

def show_regression_plot(input_csv, x_column, y_column):
    """
    Displays a regression plot showing the relationship between two columns in the dataset.

    Parameters:
        data (pd.DataFrame): The dataset containing the columns.
        x_column (str): The name of the column to be used as the x-axis.
        y_column (str): The name of the column to be used as the y-axis.
    """
    data = pd.read_csv(input_csv)
    plt.figure(figsize=(10, 6))
    sns.regplot(x=x_column, y=y_column, data=data, line_kws={"color": "red"})
    plt.title(f'Regression Plot: {x_column} vs {y_column}')
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.grid(True)
    plt.show()
    plt.savefig(f"graphs/Regression_Plot:_{x_column}_vs_{y_column}.png")
    plt.close()

if __name__ == "__main__":
    df = pd.read_csv('cleaned_data_no_outliers.csv')
    plt.figure(figsize=(8, 6))
    sns.scatterplot(x='longitude', y='latitude', data=df)
    plt.title("Geographical Distribution")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.savefig("graphs/geographical_distribution.png")
    plt.close()
