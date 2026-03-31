import pickle
import numpy as np
import pandas as pd

__model = None

def load_model():
    global __model
    with open('Model\libya_house_price_model.pkl', 'rb') as f:
        __model = pickle.load(f)

def get_estimated_price(bedrooms, bathrooms, surface_area, latitude, longitude):
    suf = np.log(surface_area)
    x = pd.DataFrame(
        [[bedrooms, bathrooms, suf, latitude, longitude]],
        columns=['bedrooms', 'bathrooms', 'surface_area', 'latitude', 'longitude']
    )

    return round(np.exp(__model.predict(x)[0]), 2)

if __name__ == '__main__':
    load_model()
    print(get_estimated_price(3, 1, 70, 50.7128, -74.0060))
    print(get_estimated_price(5, 2, 100, 50.7128, -74.0060))
    print(get_estimated_price(1, 1, 40, 50.7128, -74.0060))
