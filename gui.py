"""
this window is for handling streamlit experiments
"""
# from utilities import path
import streamlit as st
import pandas as pd
import pydeck as pdk


# PATHS_ON_CAMPUS = path("campus_map_1.json")
# paths_df = pd.read_json(PATHS_ON_CAMPUS)

# def hex_to_rgb(hex_str):
#     hex_str = hex_str.lstrip("#")
#     return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

# paths_df["rgb_color"] = paths_df["rgb_color"].apply(hex_to_rgb)

# initial_view_state = pdk.ViewState(latitude=37.782556, longitude=-122.3484867, zoom=10)

# path_layer = pdk.Layer(
#     type="PathLayer",
#     data=paths_df,
#     pickable=True,
#     get_color="rgb_color",
#     width_scale=20,
#     width_min_pixels=2,
#     get_path="path",
#     get_width=5,
# )

# deck = pdk.Deck(layers=[path_layer], initial_view_state=initial_view_state, tooltip={"text": "{name}"})
# deck.to_html("bart_path_layer.html")


file_path = "output.xlsx"
sheet_name = "Sheet1"  # Change to the name of the sheet you need
column_name = "LatLon"  # Change to the column you need

# Read only the specified sheet
df = pd.read_excel(file_path, sheet_name=sheet_name, usecols=[column_name])
# creates a list of tuples from the column of the excel file
column_list = [tuple(map(float, val.split(','))) for val in df[column_name].dropna()]


# Converts the list of tuples into a DataFrame
df = pd.DataFrame(column_list, columns=['lat', 'lon'])

# Defines a PyDeck layer
layer = pdk.Layer(
    'ScatterplotLayer',
    df,
    # converts the tuple into the latitude and longitude
    get_position='[lon, lat]',
    # sets the color of the nodes
    get_color='[200, 30, 0, 160]',
    # sets the radius of the nodes
    get_radius=2,
    pickable=True
)

# Set the viewport location
view_state = pdk.ViewState(
    longitude=-120.388428,
    latitude=38.030901,
    zoom=14,
    pitch=50
)

# Render the map with PyDeck
st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/light-v10"
))
