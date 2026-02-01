import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import numpy as np
from urllib.parse import urlparse, parse_qs

def clean_data(input_csv, output_csv):
    """
    Cleans and standardizes the property data.
    """
    df = pd.read_csv(input_csv)

    # Drop unnecessary columns
    columns_to_drop = [
        'category', 'reference_id', 'payment_method', 'main_amenities', 'nearby', 'building_age',
        'additional_amenities', 'land_area', 'property_status', 'country',
        'real_estate_type', 'floor', 'zoned_for', 'number_of_floors', 'url', 'description'
    ]
    df.drop(columns=columns_to_drop, inplace=True, errors='ignore')

    # Remove specific subcategory
    df = df[df['subcategory'] != 'Farms & Chalets for Sale']
    df = df[df['subcategory'] != 'Whole Building for Sale']

    df['subcategory'] = df['subcategory'].replace({'Apartments for Sale': 'Apartment', 'Villas for Sale': 'Villa', 'Homes for Sale': 'House'})

    # Handle missing values
    for col in ['bedrooms', 'bathrooms', 'lister_type']:
        df[col] = df[col].fillna(df[col].mode()[0])

    fill_value_columns = {'facade': 'Unknown', 'property_mortgaged?': 'No'}
    df.fillna(value=fill_value_columns, inplace=True)

    # Standardize categorical columns
    bedroom_mapping = {
        '7 +': 7, 'More Than 6 Bedrooms': 7, 'Studio': 1, '1 Bedroom': 1, '2 Bedrooms': 2,
        '3 Bedrooms': 3, '4 Bedrooms': 4, '5 Bedrooms': 5
    }
    bathroom_mapping = {
        '7 +': 7, 'More Than 6 Bathrooms': 7, 'One Bathroom': 1, '2 Bathrooms': 2,
        '3 Bathrooms': 3, '4 Bathrooms': 4, '5 Bathrooms': 5
    }

    df['bedrooms'] = df['bedrooms'].replace(bedroom_mapping).astype(float)
    df['bathrooms'] = df['bathrooms'].replace(bathroom_mapping).astype(float)

    # Clean and convert surface area to numeric
    df['surface_area'] = (
        df['surface_area']
        .astype(str)
        .str.replace(' meter square', '', regex=False)
        .str.replace(' sqm', '', regex=False)
        .apply(pd.to_numeric, errors='coerce')
    )

    # Convert to boolean
    boolean_columns = {'furnished?': 'Furnished', 'property_mortgaged?': 'Yes'}
    for col, true_value in boolean_columns.items():
        df[col] = df[col].apply(lambda x: x == true_value)

    # Convert to numeric, coercing errors
    df['price'] = (df['price'].str.replace('LYD', '', regex=False).str.replace(',', '', regex=False).str.strip())
    df['price'] = df['price'].astype(str).str.extract('(\\d+)').astype(float)
    df['price'] = pd.to_numeric(df['price'], errors='coerce')

    # Remove rows with non-numeric or missing prices
    df.dropna(subset=['price'], inplace=True)

    df.to_csv(output_csv, index=False)

def transform_cleaned_data(input_csv, output_csv):
    """
    Removes unrealistic property listings based on price and surface area.
    """
    df = pd.read_csv(input_csv)

    # Filter data based on realistic values
    df = df[(df['price'] >= 15000) & (df['price'] <= 15000000)]
    df = df[(df['surface_area'] >= 50) & (df['surface_area'] <= 1000)]

    # # Extract latitude and longitude from location links
    # df = extract_lat_long_from_location(df, 'location')
    # # Drop unnecessary columns
    # df.drop(columns=['location'], errors='ignore', inplace=True)

    # Remove impossible location values (Libya bounds)
    df = df[(df['latitude'] >= 19.5) & (df['latitude'] <= 33)]
    df = df[(df['longitude'] >= 9) & (df['longitude'] <= 25)]

    df.to_csv(output_csv, index=False)

def standardize_city_name(name):
    if not isinstance(name, str) or name.lower() == 'nan':
        return "Other"
    
    #Basic Normalization
    name = name.lower().strip()
    name = name.replace('-', ' ').replace("'", "")

    # 2. PHONETIC NORMALIZATION (The "Sounds-Like" Step)
    # This step handles the e/i/ee and h/ah differences before the mapping
    def normalize_sounds(text):
        # Convert ee, i, y to a single 'i'
        text = re.sub(r'ee|y|e', 'i', text)
        # Handle terminal 'h' or 'ah' (Common in Arabic names like Humaidah)
        text = re.sub(r'(ah|h)$', 'a', text)
        # Standardize Al/An/As/Ar prefixes
        text = re.sub(r'^(an|as|ar|at|ad|az|ash)\s+', 'al ', text)
        # Remove double consonants (e.g., Hammoudat -> Hamodat)
        text = re.sub(r'(.)\1+', r'\1', text)
        return text.strip()

    # 3. Comprehensive Mapping based on your latest list
    # The keys here are the "Standard" names you want for your project
    mapping = {
        'tripoli': ['ain zara', 'janzour', 'Qasr Bin Ghashir', 'soug al juma’aa', 'tajoura', 'souq al jomoa', 'souq al jumaa', 'tripoli', 'طرابلس'],
        'al khoms': ['al khoms', 'al khums'],
        'misratah': ['misrata', 'misratah', 'misurata'],
        'al zawiya': ['الزاويه جودايم'],
        'other': ['l.l']
    }

    # First, try an exact match with the normalized version
    normalized_name = normalize_sounds(name)
    
    for standard, variations in mapping.items():
        # Normalize all variations for comparison
        norm_variations = [normalize_sounds(v) for v in variations]
        
        # Check if the input (normalized) matches any variation (normalized)
        if normalized_name in norm_variations:
            return standard
            
        # Partial match (if 'ainzara' is found within 'ainzara road')
        for nv in norm_variations:
            if nv in normalized_name or normalized_name in nv:
                return standard

    return name.strip().title()

def standardize_street_name(name):
    if not isinstance(name, str) or name.lower() == 'nan':
        return "Other"
    
    #Basic Normalization
    name = name.lower().strip()
    name = name.replace('-', ' ').replace("'", "")
    
    # Map Arabic to English equivalents (Add more as you find them)
    arabic_map = {
        'عين زارة': 'ain zara',
        'جوددائم': 'juddaim'
    }
    if name in arabic_map:
        name = arabic_map[name]

    # 2. PHONETIC NORMALIZATION (The "Sounds-Like" Step)
    # This step handles the e/i/ee and h/ah differences before the mapping
    def normalize_sounds(text):
        # Convert ee, i, y to a single 'i'
        text = re.sub(r'ee|y|e', 'i', text)
        # Handle terminal 'h' or 'ah' (Common in Arabic names like Humaidah)
        text = re.sub(r'(ah|h)$', 'a', text)
        # Standardize Al/An/As/Ar prefixes
        text = re.sub(r'^(an|as|ar|at|ad|az|ash)\s+', 'al ', text)
        # Remove double consonants (e.g., Hammoudat -> Hamodat)
        text = re.sub(r'(.)\1+', r'\1', text)
        return text.strip()

    # 3. Comprehensive Mapping based on your latest list
    # The keys here are the "Standard" names you want for your project
    mapping = {
        '20 Ramadan': ['9th of july', '20 ramadan'],
        'Ain Zara': ['ain zara', 'ainzara'],
        'Al Baiesh': ['al baish', 'al baish', 'albaishi', 'al baish'],
        'Al Dahra': ['al dahra', 'al dhahra', 'zawiyat al dahmani'],
        'Al Fatih': ['al fatih', 'al fateh'],
        'Al Fakat': ['al faqaat', 'al fakat'],
        'Al Furnaj': ['al furnaj', 'al fornaj'],
        'Al Fuwayhat': ['al fuwaihat', 'al fuwaihatf', 'al fuwayhat'],
        'Al Hadba': ['al hadba al khadra', 'alhadba alkhadra', 'alhadba', 'eastern hadba', 'hadba project'],
        'Al Hamodat': ['al hamodat', 'al hamoudat', 'al hammoudat'],
        'Al Kreemia': ['al kreemia', 'al krimiah', 'kriimia', 'karimia', 'alkrimiah'],
        'Al Majouri': ['al majouri', 'al majouri', 'al majouri'],
        'Al Nofleen': ['al nofliyen', 'al nofleen'],
        'Al Sarraj': ['al sarraj', 'al serraj', 'hay al siraj'],
        'Al Siyahiya': ['al siyahiya', 'al seyaheyya'],
        'Al Swani': ['al swani', 'alswani'],
        'Al Zawiya': ['al zawiya', 'al zawya', 'al zawiyah', 'western zawiya'],
        'Airport Road': ['airport', 'al matar'],
        'Bin Ashour': ['bin ashur', 'bin ashour'],
        'Dollar': ['dollar'],
        'Qasr Bin Ghashir': ['qasr bin ghashir', 'qasr bin ghasher', 'bab bin ghashier'],
        'Salah Al Din': ['salah al din', 'salah al dien', 'salah aldeen'],
        'Sidi Hussein': ['sidi husain', 'sidi hussein'],
        'Souq Al Juma': ['souq al juma', 'souq al jumaa', 'soq al jomua'],
        'Tajoura': ['tajura', 'tajoura'],
        'Venice': ['venice', 'venecia'],
        'Wildlife Road': ['wildlife', 'wild life'],
        'Zanata': ['zanata', 'zanatah'],
        'Al Humaida': ['al humaida', 'al humaidah', 'al humaidia'],
        'Al Najila': ['al najila', 'al nejela', 'an najila'],
        'Al Ruwaisat': ['alruwesat', 'al ruwaisat', 'ruweisat'],
        'Al Salmani': ['al salmani', 'as sulmani', 'as sulmani al sharqi'],
        'Beloun': ['baloun', 'beloun'],
        'Diplomatic Quarter': ['diplomacy', 'diplomatic'],
        'Espiaa': ['asbia', 'espiaa'],
        'Hai Al Andalous': ['hai alandalus', 'hay al andalous'],
        'Janzour': ['zanzour', 'janzour', 'zanzour al shat'],
        'Khallet Al Furjan': ['khallet alforjan', 'khallet al furjan'],
        'Sidi Younis': ['bin yunus', 'sidi younis'],
        'Um Mabrokah': ['om mabroka', 'um mabrokah']
    }

    # First, try an exact match with the normalized version
    normalized_name = normalize_sounds(name)
    
    for standard, variations in mapping.items():
        # Normalize all variations for comparison
        norm_variations = [normalize_sounds(v) for v in variations]
        
        # Check if the input (normalized) matches any variation (normalized)
        if normalized_name in norm_variations:
            return standard
            
        # Partial match (if 'ainzara' is found within 'ainzara road')
        for nv in norm_variations:
            if nv in normalized_name or normalized_name in nv:
                return standard

    # 4. Final Fallback: Cleanup formatting for unique names
    name = re.sub(r'\b(road|st|street|rd|district|neighbourhood|ave|avenue|quarter)\b', '', name)
    return name.strip().title()

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
    # clean_data('data/combined_data.csv','data/cleaned_data.csv')
    # outlier_detection('data/cleaned_data.csv', 'facade', 'price', '_pre_cleaning')

    # transform_cleaned_data('data/cleaned_data.csv','data/cleaned_data_transformed.csv')
    # remove_outliers_by_category('data/cleaned_data_transformed.csv', 'data/cleaned_data_transformed.csv', 'facade', 'price')
    
    # outlier_detection('data/cleaned_data_transformed.csv', 'facade', 'price', '_post_cleaning')

    # basic_plotting('data/cleaned_data_transformed.csv')
    show_regression_plot('data/cleaned_data_transformed.csv', 'surface_area', 'price')
    show_regression_plot('data/cleaned_data_transformed.csv', 'longitude', 'price')
    show_regression_plot('data/cleaned_data_transformed.csv', 'latitude', 'price')
    show_regression_plot('data/cleaned_data_transformed.csv', 'bedrooms', 'price')
    show_regression_plot('data/cleaned_data_transformed.csv', 'bathrooms', 'price')
    # eda('data/cleaned_data_transformed.csv')

    #REMEMBER TO MAKE THE COLUMN PRICE PER METER SQUARE LATER

    # first_list = ['20 Ramadan Road', '9th of July', 'AL Khalij Al Arabi St', 'AL-Mansoura', 'ALJAZERAH', 'ALMOQAWBAH', 'ALRWESAT', 'ALSKERAT', 'ALZAROQ', 'Abbad', 'Abu Meshmasha', "Abu Naw'was", 'Abu Rouiah', 'Abu Saleem', 'Abu Sittah', 'Ain Zara', 'Ain Zara Road', 'Ainzara St', 'Airport Highway', 'Airport Road', 'Al Bifi', 'Al Dahra', 'Al Entisar District', 'Al Fateh neighbourhood', 'Al Ghiran', "Al Hada'iq", 'Al Halis District', 'Al Hawary', 'Al Hilal Street', "Al Jala'a", 'Al Nahr Road', 'Al Nasr St', 'Al Nofleen', 'Al Rawda neighbourhood', 'Al Sabaa', 'Al Sarim', 'Al Serraj', 'Al Zawya Street', 'Al-Ahd Street', 'Al-Azeeb', "Al-Ba'ish", 'Al-Baesh', 'Al-Baiesh', 'Al-Berka', 'Al-Bivio', 'Al-Dhahra', 'Al-Fallah Road', "Al-Faqa'at", 'Al-Fatih', 'Al-Fornaj', 'Al-Fuwaihat', 'Al-Fuwayhat', 'Al-Ghasi', "Al-Hadaba'tool Rd", 'Al-Hadba Al-Khadra', 'Al-Hae Al-Senaea', 'Al-Hai Al-Jamei', 'Al-Halis', 'Al-Hammoudat', 'Al-Hamoudat', 'Al-Hani', 'Al-Haraba Road', 'Al-Harsha', 'Al-Hashan', 'Al-Hijaz st.', 'Al-Humaida', 'Al-Humaidah', 'Al-Jabs', "Al-Jadada'a", 'Al-Jamahirriyah St', 'Al-Jarabah St', 'Al-Jumhuriya Street', 'Al-Karuba', 'Al-Kesh', 'Al-Kremiah', 'Al-Kuwaifiyya', 'Al-Lithi', 'Al-Mahishi', 'Al-Majoure', 'Al-Majouri', 'Al-Manshia', 'Al-Mansoura', 'Al-Maqrif', 'Al-Masakin', 'Al-Mashtal Rd', 'Al-Mashtal Road', 'Al-Masira Al-Kubra St', 'Al-Matar St.', 'Al-Najila', 'Al-Nasr Street', 'Al-Nawaqiya', 'Al-Nofliyen', 'Al-Qaio', 'Al-Rahba', 'Al-Raidaat Road', 'Al-Rayaidat Island', 'Al-Ruwaisat', 'Al-Sabaa', 'Al-Sabaa Road', 'Al-Salam', 'Al-Salmani', 'Al-Sareem', 'Al-Sarraj neighbourhood', 'Al-Sarti', "Al-Sayeda A'esha", 'Al-Sedra', 'Al-Serraj', 'Al-Seyaheyya', 'Al-Shat Road', 'Al-Shawahda', 'Al-Shawarn Road', 'Al-Shok Rd', 'Al-Sidra', 'Al-Sindibad District', 'Al-Siyahiya', 'Al-Talhia', 'Al-Wakalat Street', 'Al-Zaiton District', 'Al-Zawiya', 'Al-Zawiyah St', 'Al-Zohour Al-Daribi District', 'AlHabbara', 'AlKhadra', 'AlMaqasbah', 'AlQadariya', 'AlSakt', 'AlZawraq', 'Alfornaj', 'Alhadba Alkhadra', 'Alhadba St', 'Almasaken', 'Alnejela', 'Alswani', 'Altagel', 'An Nawwaqiyah', 'An-Najila', 'Arada', 'Ard Zwawa Albahriya', 'Ard lamloom', 'As-Sulmani', 'As-Sulmani Al-Sharqi', "Asbi'a", 'Assabri', 'Aziziya', 'Bab Al-Azizia', 'Bab Bin Ghashier', 'Baloun', 'Baninah', 'Bashier Sadawi', 'Bayda', 'Beloun', 'Benghazi', 'Bin Ashour', 'Bin Ashur', 'Bin Yunus', 'Bir Al-Alam Road', 'Bir al-Isti Milad', 'Bo sneib', 'Boatni', 'Bodzirah', 'Bohdema', 'Bossneb', 'Boudressa', 'Bu Hadi', 'Buhadi', 'Cyrene', 'Dagadosta', 'Dakkadosta', 'Diplomacy District', 'Diplomatic Quarter', 'Dollar', 'Dollar neighbourhood', 'Downtown', 'Dubai Road', 'Dubai Street', 'Eastern Hadba Rd', 'Edraibi', 'Espiaa', 'Fashloum', 'Fourth Circular Road', 'Ganfouda', 'Gardens', 'Garyounis', 'Gasr Garabulli', 'Ghanima', 'Gharghour', 'Gharyan Road', 'Ghut Shaal', 'Gorje', 'Hadaba project', 'Hai Al-Batata', 'Hai Alandalus', 'Hai Alsslam', 'Hai Qatar', 'Haiti St', 'Hawary', 'Hay Al-Islami', 'Hay Al-Siraj', 'Hay Al-andalous', 'Hay Demsheq', 'Hay Es Salem', 'Hay Qatar', 'Hay almachriki', 'Independence St', 'Islamic preaching', "Jama'a Saqa'a", 'Janzour', 'Jazeerat Al-Fahm', 'Jikharra', 'Kaam Area', 'Kaam village', 'Karzaz', 'Kashlaf', 'Keesh', 'Kerzaz', 'Khalatat St', 'Khalla Al-Rashah', 'Khallet Al Furjan', 'Khallet Alforjan', 'Khorasan', 'Kraut', 'Kreemia', 'Kuwayfiyah', 'Lebanon District', 'MISRATA', 'Masr St', 'Military Hospital', 'Mizran St', 'Moqawaba', 'New Benghazi', 'Old City', 'Old Soar Road', 'Omar Al-Mukhtar Rd', 'Omar Al-Mukhtar Street', 'Other', 'Palestine St', 'Pepsi Street', 'Pepsi street', 'QASER AHMED', 'Qaminis', 'Qanfooda', 'Qar Yunis', 'Qasr Ahmed Road', 'Qasr Bin Ghashir', 'Qasr bin Ghasher', 'Qawarsheh', 'Qerqarish', 'Ras Abaydah', 'Ras Hassan', 'River Road', 'Ruweisat', 'Saidi St', 'Salah Al-Din', 'Salah Al-dien', 'Salah Aldeen', 'Shabna', 'Shawqy St', 'Sidi Al-Masri', "Sidi Al-Sae'a", 'Sidi Bons', 'Sidi Faraj', 'Sidi Husain', 'Sidi Hussein', 'Sidi Khalifa', 'Sidi Younis', 'Soap Factory Road', 'Soq Al-Jomua road', "Souq Al Jum'aa", "Souq Al-Juma'a", 'Souq Al-Khamis', 'Souq Elkhamis', 'Street Alswani', 'Syria Street', 'TAREQ ALTHMANYAH', 'TIMENAH', 'Tabalino', 'Tajoura', 'Tajura', 'Talil', 'Tamina', 'Tareeq Al-Mashtal', 'Tariq Zanatah', 'That Al-Emad', 'The highway near', 'The second ring', 'Tikah', 'Tripoli', 'Tripoli St', 'Twenty Street', 'Um Mabrokah', 'Um Shweisha', 'University district', 'University of Tripoli', 'Vehicles', 'Venecia', 'Venice', 'Venice 2', 'Wadi Al-Rabi', 'West Zawiya', 'Western Zawiya', 'Wild Life Rd', 'Wildlife Road', 'Yeder', 'Zamzam neighbourhood', 'Zanata', 'Zanatah', 'Zanzour al shat', 'Zawiyat Al Dahmani', 'Zawiyat Al-Dahmani', 'Zawiyat Al-Mahjoub', 'al fakat', 'al hadbai', 'al magzaha', 'al rahaba', 'al talheya', 'albaeishei', 'alkhili', 'kareimia', 'om mabroka', 'saida aisha', 'tajoura', 'wakalet', 'جوددائم', 'عين زارة', 'nan']


