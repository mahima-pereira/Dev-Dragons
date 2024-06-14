from flask import Flask, render_template, request
import requests
import folium
from geopy.distance import geodesic

app = Flask(__name__)

# Your Google Maps API key
API_KEY = 'AIzaSyCajSz9hfSCKEnVlO7ccWTtvVLnDJ5uVf4'

# Updated list of ambulance locations including towards Bengaluru Airport
ambulance_locations = [
    (12.9716, 77.5946),   # Central Bengaluru
    (12.9352, 77.6245),   # South Bengaluru
    (12.9279, 77.6271),   # South-East Bengaluru
    (12.9507, 77.5848),   # South-West Bengaluru
    (12.9719, 77.6412),   # East Bengaluru
    (13.0111, 77.5668),   # North Bengaluru
    (13.0358, 77.5970),   # North-East Bengaluru
    (13.0227, 77.5895),   # North-West Bengaluru
    (12.9538, 77.4903),   # West Bengaluru
    (12.9833, 77.5600),   # Central-West Bengaluru
    (13.0067, 77.6000),   # Central-North Bengaluru
    (12.9109, 77.6017),   # South-Central Bengaluru
    (13.1835, 77.6922),
    (13.1806, 77.6893)
]

# Get nearby multispeciality hospitals using Google Places API
def get_nearby_multispeciality_hospitals(api_key, location, radius=5000, keyword='multispeciality hospital'):
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        patient_lat = request.form['latitude']
        patient_lng = request.form['longitude']
        patient_location = (float(patient_lat), float(patient_lng))

        nearest_ambulance = find_nearest_ambulance(patient_location, ambulance_locations)
        if not nearest_ambulance:
            return "No ambulances found."

        hospitals = get_nearby_multispeciality_hospitals(API_KEY, patient_location)
        if not hospitals:
            return "No multispeciality hospitals found."

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
        map_path = 'templates/ambulance_route.html'
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

        # Return the updated HTML file
        return render_template('ambulance_route.html')

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)


