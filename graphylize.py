import sys
import argparse
import numpy as np
from collections import namedtuple
import matplotlib.pyplot as plt
from geopy.distance import geodesic
from sklearn.metrics.pairwise import haversine_distances
from sklearn.metrics.pairwise import euclidean_distances
import utm

parser = argparse.ArgumentParser (description="Analyze and graph the results of pygeokmedoids.")

parser._action_groups.pop ()
required = parser.add_argument_group ('Required arguments')
optional = parser.add_argument_group ('Optional arguments')

required.add_argument ('-p', '--positions',
                      required=True,
                      help="Input path to a csv file, with format (uid,gid,latitude,longitude).")

required.add_argument ('-c', '--centers',
                      required=True,
                      help="Input path to a csv file, with format (gid,latitude,longitude).")

optional.add_argument ('-d', '--distance-metric',
                      default="euclidean",
                      choices=['euclidean', 'haversine', 'geodesic'],
                      help="Select a distance metric. (default: 'geodesic')")

args = parser.parse_args ()

def haversine_distance (alat, alon, blat, blon):
    rx = np.radians ([[alat, alon], [blat, blon]])
    dm = haversine_distances (rx) * 6371000
    return np.array (dm).item (1)

def euclidean_distance (alat, alon, blat, blon):
    utm_result = utm.from_latlon (np.array ([alat, blat]), np.array ([alon, blon]))
    x = np.column_stack ((utm_result[0], utm_result[1]))
    dm = euclidean_distances (x)
    return np.array (dm).item (1)

def geodesic_distance (alat, alon, blat, blon):
    return geodesic ((alat, alon), (blat, blon)).m

def distance (metric, alat, alon, blat, blon):
    if metric == 'euclidean':
        return euclidean_distance (alat, alon, blat, blon)
    if metric == 'haversine':
        return haversine_distance (alat, alon, blat, blon)
    if metric == 'geodesic':
        return geodesic_distance (alat, alon, blat, blon)

# Load positions, with their id and label
pos_uids,pos_gids,pos_lats,pos_lons = np.genfromtxt (args.positions, delimiter=',', names=True, dtype="S8,S36,f8,f8", unpack=True)
pos_uids = [u.decode (encoding='UTF-8') for u in pos_uids]
pos_gids = [u.decode (encoding='UTF-8') for u in pos_gids]

# Load label centers and names
cen_gids,cen_lats,cen_lons = np.genfromtxt (args.centers, delimiter=',', names=True, dtype="S36,f8,f8", unpack=True)
cen_gids = [u.decode (encoding='UTF-8') for u in cen_gids]

Pos = namedtuple ('Pos', ['lat', 'lon'])

# Compute a label names dictionary, and initialize the label sizes dictionary
gids = {}
gids_size = {}
for gid, lat, lon in zip (cen_gids, cen_lats, cen_lons):
    gids[gid] = Pos (lat,lon)
    gids_size[gid] = 0

# Compute distances to cluster centers for every position, according to metric, and accumulate the size of each label
pos_dist = np.zeros (len (pos_uids))
for i, (gid, lat, lon) in enumerate (zip (pos_gids, pos_lats, pos_lons)):
    pos_dist[i] = distance (args.distance_metric, lat, lon, gids[gid].lat, gids[gid].lon)
    gids_size[gid] += 1

# Print average and 3sigma for distances
print (f'Average distance: {pos_dist.mean()}, 3sigma: {3 * pos_dist.std()}, max: {pos_dist.max()}, min {pos_dist.min()}')
# Print average and 3sigma for sizes
gids_size_array = np.array (list (gids_size.values ()))
print (f'Average label size: {gids_size_array.mean()}, 3sigma: {3 * gids_size_array.std()}, max: {gids_size_array.max()}, min {gids_size_array.min()}')

# Plot distances
plt.bar (np.arange (len (pos_dist)), np.sort (pos_dist))
plt.show ()

# Plot sizes
plt.bar (np.arange (len (gids_size_array)), np.sort (gids_size_array))
plt.show ()
