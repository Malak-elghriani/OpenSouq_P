from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import util

app = Flask(__name__)
CORS(app)

util.load_model()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/estimate_price', methods=['POST','OPTIONS'])
def estimate_price():

    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 200

    data = request.get_json()

    bedrooms = data.get('bedrooms')
    bathrooms = data.get('bathrooms')
    surface_area = data.get('surface_area')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if None in [bedrooms, bathrooms, surface_area, latitude, longitude]:
        return jsonify({'error': 'Missing required parameters'}), 400

    try:
        estimated_price = util.get_estimated_price(
            bedrooms, bathrooms, surface_area, latitude, longitude
        )

        return jsonify({'estimated_price': estimated_price})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting server...")
    app.run(port=5001)