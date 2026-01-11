import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def perform_eda(csv_file):
    # Load the data
    df = pd.read_csv(csv_file)

    # Display basic information about the dataset
    print("\nBasic Information:")
    print(df.info())

    # Display summary statistics
    print("\nSummary Statistics:")
    print(df.describe(include='all'))

    # Check for missing values
    print("\nMissing Values:")
    print(df.isnull().sum())

    # Check for duplicate rows
    print("\nDuplicate Rows:")
    print(df.duplicated().sum())

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

# Example usage
if __name__ == "__main__":
    perform_eda("unclean_data.csv")