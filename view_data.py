
import json

def view_property_data(file_path):
    """
    Reads and displays property data from a JSON file.

    Args:
        file_path (str): The path to the JSON file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("The JSON file does not contain a list of properties.")
            return

        for i, property_data in enumerate(data):
            print(f"--- Property {i+1} ---")
            print(f"URL: {property_data.get('url', 'N/A')}")
            print(f"Price: {property_data.get('price', 'N/A')}")
            print(f"Location: {property_data.get('location', 'N/A')}")
            
            attributes = property_data.get('attributes', {})
            if attributes:
                print("Attributes:")
                for key, value in attributes.items():
                    print(f"  {key}: {value}")
            print("-" * 20)

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from the file '{file_path}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    view_property_data('property_data.json')
