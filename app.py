import os
import requests
import pandas as pd
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()

# Fetch Earthquake Data
def fetch_earthquake_data(start_date="2024-08-01", end_date="2024-08-31", min_magnitude=5):
    try:
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_date}&endtime={end_date}&minmagnitude={min_magnitude}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
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
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching earthquake data: {e}")
        return pd.DataFrame()

# Fetch OpenWeather Data
def fetch_openweather_data(lat, lon):
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            raise ValueError("API key for OpenWeather not found.")

        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

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
            "Wind Direction (\u00b0)": data['wind']['deg']
        }
        return weather_info
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {e}")
        return None
    except KeyError as e:
        st.error(f"Unexpected data format: missing {e}")
        return None

# Preprocess Earthquake Data
def preprocess_data(df):
    if df.empty:
        return df
    df['Normalized_Magnitude'] = (df['Magnitude'] - df['Magnitude'].min()) / (df['Magnitude'].max() - df['Magnitude'].min())
    return df

# Display Dashboard with Streamlit
def display_dashboard(earthquake_data, weather_data):
    st.title("Real-Time Natural Disaster Monitoring")

    # Sidebar customization
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/2/29/USGS_logo.png", width=150)
    st.sidebar.markdown("**Customize Settings**")

    # Display earthquake data
    st.write("### Earthquake Data")
    if not earthquake_data.empty:
        st.dataframe(earthquake_data, use_container_width=True)
        st.line_chart(earthquake_data[['Time', 'Magnitude']].set_index('Time'))
    else:
        st.write("No earthquake data available.")

    # Display weather data
    if weather_data:
        st.write("### Current Weather Data")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Temperature", f"{weather_data['Temperature (C)']} °C", delta=f"Feels like {weather_data['Feels Like (C)']} °C")
            st.metric("Pressure", f"{weather_data['Pressure (hPa)']} hPa")
            st.metric("Humidity", f"{weather_data['Humidity (%)']} %")
        with col2:
            st.metric("Wind Speed", f"{weather_data['Wind Speed (m/s)']} m/s")
            st.metric("Wind Direction", f"{weather_data['Wind Direction (°)']} {chr(176)}")
            st.markdown(f"**Description:** {weather_data['Weather Description']}")
    else:
        st.write("Weather data not available.")

# Send Alert
def send_alert(message_body):
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_number = os.getenv('TWILIO_NUMBER')
        recipient_number = os.getenv('RECIPIENT_NUMBER')

        # Check for missing credentials
        if not all([account_sid, auth_token, twilio_number, recipient_number]):
            raise ValueError("Twilio credentials are missing or invalid.")

        # Ensure recipient_number is not None
        if recipient_number is None:
            raise ValueError("Recipient number is missing.")

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message_body,
            from_=twilio_number,
            to=recipient_number
        )
        st.success(f"Alert sent: {message.sid}")
    except ValueError as ve:
        st.error(f"Validation Error: {ve}")
    except Exception as e:
        st.error(f"Error sending alert: {e}")


# Run the Streamlit app
if __name__ == '__main__':
    # User inputs for location
    st.sidebar.title("Settings")
    lat = st.sidebar.number_input("Latitude", value=33.40, format="%f")
    lon = st.sidebar.number_input("Longitude", value=-94.40, format="%f")

    # Fetch and display earthquake data
    earthquake_data = fetch_earthquake_data()
    earthquake_data = preprocess_data(earthquake_data)

    # Fetch OpenWeather data
    weather_data = fetch_openweather_data(lat, lon)

    # Display data in the dashboard
    display_dashboard(earthquake_data, weather_data)

    # Send alerts based on conditions
    if not earthquake_data.empty and earthquake_data['Magnitude'].max() > 6:
        send_alert("Earthquake Alert: Magnitude above 6 detected!")
