import requests
import pandas as pd
from datetime import datetime
import streamlit as st

# Fetch Earthquake Data
def fetch_earthquake_data():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2024-08-01&endtime=2024-08-31&minmagnitude=5"
    response = requests.get(url)
    data = response.json()
    
    earthquakes = []
    for feature in data['features']:
        properties = feature['properties']
        time = datetime.utcfromtimestamp(properties['time'] / 1000)
        magnitude = properties['mag']
        place = properties['place']
        earthquakes.append([time, magnitude, place])
    
    df = pd.DataFrame(earthquakes, columns=['Time', 'Magnitude', 'Place'])
    return df

# Fetch OpenWeather Data
def fetch_openweather_data(lat=33.40, lon=-94.40, api_key='b4ff7b1fbbd4668912b7a6c42082f1d5'):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    print(f"url = {url}")
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(data)  # Debugging purposes
        
        # Extract relevant data from the response
        weather_info = {
            "Location": data.get('name'),
            "Temperature (C)": data['main']['temp'],
            "Feels Like (C)": data['main']['feels_like'],
            "Min Temperature (C)": data['main']['temp_min'],
            "Max Temperature (C)": data['main']['temp_max'],
            "Pressure (hPa)": data['main']['pressure'],
            "Humidity (%)": data['main']['humidity'],
            "Weather Description": data['weather'][0]['description'],
            "Wind Speed (m/s)": data['wind']['speed'],
            "Wind Direction (°)": data['wind']['deg']
        }
        return weather_info
    else:
        print(f"Error fetching weather data: {response.status_code}")
        return None


# Preprocess Earthquake Data
def preprocess_data(df):
    df['Normalized_Magnitude'] = (df['Magnitude'] - df['Magnitude'].min()) / (df['Magnitude'].max() - df['Magnitude'].min())
    return df

# Display Dashboard with Streamlit
def display_dashboard(earthquake_data, weather_data):
    st.title("Real-Time Natural Disaster Monitoring")
    
    # Display earthquake data
    st.write("### Earthquake Data")
    st.dataframe(earthquake_data)
    
    # Visualize earthquake magnitude
    st.line_chart(earthquake_data[['Time', 'Magnitude']].set_index('Time'))
    
    # Display weather data
    if weather_data:
        st.write("### Current Weather Data")
        st.json(weather_data)
    else:
        st.write("Weather data not available.")

# Run the Streamlit app
if name == 'main':
    # Fetch and display earthquake data
    earthquake_data = fetch_earthquake_data()
    earthquake_data = preprocess_data(earthquake_data)

    # Fetch OpenWeather data
    weather_data = fetch_openweather_data()

    # Display data in the dashboard
    display_dashboard(earthquake_data, weather_data)

# Example usage of sending an alert
from twilio.rest import Client

def send_alert(message_body):
    account_sid = 'accountsid'
    auth_token = 'authtoken'
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=message_body,
        from_='+12348135304',  # Your Twilio number
        to='+918302176114'      # Destination number
    )
    print(f"Alert sent: {message.sid}")

send_alert("Earthquake Alert: Magnitude 7.0 expected near San Francisco!")

#HTJMFZT2BREULQL474NFQTXFF