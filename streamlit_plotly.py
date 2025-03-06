import streamlit as st
import plotly.graph_objects as go

st.title("Map with Checkboxes and Dynamic Line")

# Define the coordinates and names for the markers
markers = {
    "Marker 1": (38.03043, -120.38745),
    "Marker 2": (38.03043, -120.38772),
    "Marker 3": (38.03108, -120.38756),
}

# Initialize session state for checkboxes if it doesn't exist
if 'selected_markers' not in st.session_state:
    st.session_state.selected_markers = []

# Create checkboxes for each marker
for marker_name in markers:
    checkbox_key = f"checkbox_{marker_name}"
    if st.checkbox(marker_name, key=checkbox_key):
        if marker_name not in st.session_state.selected_markers:
            st.session_state.selected_markers.append(marker_name)
    else:
        if marker_name in st.session_state.selected_markers:
            st.session_state.selected_markers.remove(marker_name)

# Create the map figure
fig = go.Figure()

# Add markers to the map
marker_colors = {"Marker 1": "blue", "Marker 2": "red", "Marker 3": "purple"}
for marker_name, coords in markers.items():
    fig.add_trace(go.Scattermap(
        lat=[coords[0]],
        lon=[coords[1]],
        mode='markers',
        marker=go.scattermap.Marker(
            size=14,
            color=marker_colors[marker_name]
        ),
        text=[marker_name],
        hovertemplate=f"<b>{marker_name}</b><br>Latitude: %{{lat}}<br>Longitude: %{{lon}}",
        name=marker_name
    ))

# Conditionally add the line trace if exactly two markers are selected
if len(st.session_state.selected_markers) == 2:
    marker1_name, marker2_name = st.session_state.selected_markers
    marker1_coords = markers[marker1_name]
    marker2_coords = markers[marker2_name]
    fig.add_trace(go.Scattermap(
        lat=[marker1_coords[0], marker2_coords[0]],
        lon=[marker1_coords[1], marker2_coords[1]],
        mode='lines',
        line=dict(width=2, color='green'),
        name=f"Path between {marker1_name} and {marker2_name}",
        hovertemplate=f"Path between {marker1_name} and {marker2_name}"
    ))

# Calculate the average of the coordinates of the selected markers to center the map.
selected_coords = [markers[name] for name in st.session_state.selected_markers]
if selected_coords:
    center_latitude = sum(coord[0] for coord in selected_coords) / len(selected_coords)
    center_longitude = sum(coord[1] for coord in selected_coords) / len(selected_coords)
else:
    center_latitude = sum(coord[0] for coord in markers.values()) / len(markers)
    center_longitude = sum(coord[1] for coord in markers.values()) / len(markers)

# Update the layout to center the map and set the zoom
fig.update_layout(
    map=dict(
        style="open-street-map",
        center=dict(lat=center_latitude, lon=center_longitude),
        zoom=15,  # Adjust zoom as needed
    ),
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    title="Map with Dynamic Line",
    showlegend=True
)

# Display the map in Streamlit
st.plotly_chart(fig)
