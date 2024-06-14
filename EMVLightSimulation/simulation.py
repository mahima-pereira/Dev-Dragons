import requests
import folium
import os
import webbrowser
from geopy.distance import geodesic

# Your Google Maps API key
API_KEY = 'AIzaSyCajSz9hfSCKEnVlO7ccWTtvVLnDJ5uVf4'

# Get patient location from user input
patient_lat = float(input("Enter patient's latitude: "))
patient_lng = float(input("Enter patient's longitude: "))
patient_location = (patient_lat, patient_lng)

# Ambulance locations
ambulance_locations = [
    (12.9352, 77.6245),  # Ambulance 1
    (12.9279, 77.6271),  # Ambulance 2
    (12.9507, 77.5848)   # Ambulance 3
]

# Get nearby hospitals using Google Places API
def get_nearby_hospitals(api_key, location, radius=5000, keyword='hospital'):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location[0]},{location[1]}&radius={radius}&keyword={keyword}&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json().get('results', [])
        hospitals = [(place['geometry']['location']['lat'], place['geometry']['location']['lng'], place['name']) for place in results]
        return hospitals
    else:
        print(f"Error fetching nearby hospitals: {response.status_code}")
        print(response.text)
        return []

# Get shortest path with traffic using Google Directions API
def get_shortest_path(api_key, origin, destination):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin[0]},{origin[1]}&destination={destination[0]},{destination[1]}&key={api_key}&departure_time=now"
    response = requests.get(url)
    if response.status_code == 200:
        directions = response.json().get('routes', [])
        if directions:
            route = directions[0]['legs'][0]
            steps = route['steps']
            path = [(step['start_location']['lat'], step['start_location']['lng']) for step in steps]
            path.append((steps[-1]['end_location']['lat'], steps[-1]['end_location']['lng']))
            return path, route['duration_in_traffic']['text']
        else:
            print(f"No routes found: {response.json()}")
            return [], None
    else:
        print(f"Error fetching directions: {response.status_code}")
        print(response.text)
        return [], None

# Find the nearest ambulance to the patient
def find_nearest_ambulance(patient_location, ambulance_locations):
    nearest_ambulance = None
    shortest_distance = float('inf')
    for ambulance in ambulance_locations:
        distance = geodesic(patient_location, ambulance).km
        if distance < shortest_distance:
            shortest_distance = distance
            nearest_ambulance = ambulance
    return nearest_ambulance

# Main logic
nearest_ambulance = find_nearest_ambulance(patient_location, ambulance_locations)
if not nearest_ambulance:
    print("No ambulances found.")
    exit()

hospitals = get_nearby_hospitals(API_KEY, patient_location)
if not hospitals:
    print("No hospitals found.")
    exit()

# Find the nearest hospital to the patient
nearest_hospital = find_nearest_ambulance(patient_location, [(hospital[0], hospital[1]) for hospital in hospitals])
nearest_hospital_name = next(hospital[2] for hospital in hospitals if (hospital[0], hospital[1]) == nearest_hospital)

# Get the path from the nearest ambulance to the patient and then to the nearest hospital
path_to_patient, duration_to_patient = get_shortest_path(API_KEY, nearest_ambulance, patient_location)
path_to_hospital, duration_to_hospital = get_shortest_path(API_KEY, patient_location, nearest_hospital)

# Combine the two paths
full_path = path_to_patient + path_to_hospital[1:]

# Visualization
m = folium.Map(location=patient_location, zoom_start=13)

# Add markers for the ambulances
for i, ambulance in enumerate(ambulance_locations):
    folium.Marker(location=ambulance, popup=f'Ambulance {i+1}', icon=folium.Icon(color='red')).add_to(m)

# Add patient and hospital markers
folium.Marker(location=patient_location, popup='Patient', icon=folium.Icon(color='blue')).add_to(m)
folium.Marker(location=nearest_hospital, popup=nearest_hospital_name, icon=folium.Icon(color='green')).add_to(m)

# Draw the path
folium.PolyLine(locations=full_path, color='blue', weight=5, opacity=0.7).add_to(m)

# Save map with placeholders for ambulance movement
map_path = 'ambulance_route.html'
m.save(map_path)

# JavaScript for animated movement
animation_script = f"""
<script>
var path_coords = {full_path};
var ambulanceIcon = L.icon({{
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/2961/2961633.png',
    iconSize: [38, 38],
    iconAnchor: [19, 19]
}});
var ambulanceMarker = L.marker(path_coords[0], {{icon: ambulanceIcon}}).addTo(mymap);
var step = 0;
function moveAmbulance() {{
    if (step < path_coords.length) {{
        ambulanceMarker.setLatLng(path_coords[step]);
        step++;
    }} else {{
        clearInterval(animation);
    }}
}}
var animation = setInterval(moveAmbulance, 1000);
</script>
"""

# Read the HTML file and insert the animation script
with open(map_path, 'r') as file:
    data = file.read()

data = data.replace('</body>', animation_script + '</body>')

# Write the updated HTML file
with open(map_path, 'w') as file:
    file.write(data)

# Open the map in a web browser
webbrowser.open('file://' + os.path.realpath(map_path))
