"""this is for downloading all of the required imports"""
import os

# downloads all of the required module dependencies
install_list = ['pandas', 'geopandas', 'folium', 'streamlit', 'streamlit_folium', "openpyxl"]
for i in install_list:
    command = f"pip install {i}"
    os.system(command)
