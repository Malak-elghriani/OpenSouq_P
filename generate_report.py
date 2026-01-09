
import json
from collections import Counter

def generate_html_report(data):
    """Generates an HTML report from property data."""

    # --- Calculate Statistics ---
    total_properties = len(data)

    # Average Price
    total_price = 0
    price_count = 0
    for item in data:
        try:
            price_str = item.get('price', '0').replace(' LYD', '').replace(',', '')
            total_price += float(price_str)
            price_count += 1
        except (ValueError, AttributeError):
            pass # Ignore if price is not a valid number
    average_price = total_price / price_count if price_count > 0 else 0

    # Other Stats
    cities = [item.get('attributes', {}).get('City') for item in data]
    neighborhoods = [item.get('attributes', {}).get('Neighborhood') for item in data]
    bedrooms = [item.get('attributes', {}).get('Bedrooms') for item in data]
    furnished = [item.get('attributes', {}).get('Furnished?') for item in data]

    city_counts = Counter(c for c in cities if c)
    neighborhood_counts = Counter(n for n in neighborhoods if n)
    bedroom_counts = Counter(b for b in bedrooms if b)
    furnished_counts = Counter(f for f in furnished if f)


    # --- Generate HTML ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Malak's Beautiful Project!</title>
        <style>
            body {{ font-family: sans-serif; margin: 2em; }}
            h1, h2 {{ color: #333; }}
            .stats-container {{ display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 2em;}}
            .stat-box {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; min-width: 200px;}}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Malak's Beautiful Project</h1>

        <div class="stats-container">
            <div class="stat-box">
                <h2>Total Properties</h2>
                <p>{total_properties}</p>
            </div>
            <div class="stat-box">
                <h2>Average Price</h2>
                <p>{average_price:,.2f} LYD</p>
            </div>
        </div>

        <div class="stats-container">
            <div class="stat-box">
                <h2>Properties by City</h2>
                <ul>
                    {"".join(f"<li>{city}: {count}</li>" for city, count in city_counts.most_common())}
                </ul>
            </div>
            <div class="stat-box">
                <h2>Properties by Bedrooms</h2>
                <ul>
                    {"".join(f"<li>{bed}: {count}</li>" for bed, count in bedroom_counts.most_common())}
                </ul>
            </div>
            <div class="stat-box">
                <h2>Furnished vs. Unfurnished</h2>
                <ul>
                    {"".join(f"<li>{k}: {v}</li>" for k, v in furnished_counts.items())}
                </ul>
            </div>
        </div>
        
        <h2>All Properties</h2>
        <table>
            <tr>
                <th>Price</th>
                <th>City</th>
                <th>Neighborhood</th>
                <th>Bedrooms</th>
                <th>Surface Area</th>
                <th>URL</th>
            </tr>
    """

    for item in data:
        attributes = item.get('attributes', {})
        html_content += f"""
            <tr>
                <td>{item.get('price', 'N/A')}</td>
                <td>{attributes.get('City', 'N/A')}</td>
                <td>{attributes.get('Neighborhood', 'N/A')}</td>
                <td>{attributes.get('Bedrooms', 'N/A')}</td>
                <td>{attributes.get('Surface Area', 'N/A')}</td>
                <td><a href="{item.get('url', '#')}">Link</a></td>
            </tr>
        """

    html_content += """
        </table>
    </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    try:
        with open('property_data.json', 'r', encoding='utf-8') as f:
            property_data = json.load(f)
        
        html_report = generate_html_report(property_data)
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html_report)
            
        print("Successfully generated index.html")

    except FileNotFoundError:
        print("Error: 'property_data.json' not found.")
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from 'property_data.json'.")
