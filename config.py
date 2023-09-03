import osmnx as ox

place = "Yakutsk, Russia"
mode = "drive"
optimizer = "length"
graph = ox.graph_from_place(place, network_type=mode)

max_length_factor = 1.5

colors = [
    "blue",
    "red",
    "green",
    "black",
    "darkgreen",
    "darkred",
    "purple",
    "darkblue",
]

file_name = "route_map.html"