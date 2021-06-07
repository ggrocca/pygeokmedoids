import sys
import time
import datetime
import argparse
#from math import radians
import numpy as np
from geopy.distance import geodesic
from sklearn.metrics.pairwise import haversine_distances
from sklearn.metrics.pairwise import euclidean_distances
import utm

start = f"{datetime.datetime.now():%Y%m%d-%I%M%S}"

parser = argparse.ArgumentParser (description="Benchmark of a distance matrix computation with euclidean, haversine and geodesic functions. Checks both running time and accuracy, using geopy's geodesic as the ground truth.")

parser.add_argument ('input_file',
                    help="Input path to a csv file, with format (id,lat,lon)."
                    )
args = parser.parse_args ()

uids,lats,lons = np.genfromtxt (args.input_file, delimiter=',', names=True, dtype="S8,f8,f8", unpack=True)
uids = [u.decode (encoding='UTF-8') for u in uids]
X = np.column_stack ((lats, lons))

# euclidean test
EDM = np.zeros ((len (uids),len (uids)))
euclidean_tic = time.perf_counter ()
utm_result = utm.from_latlon (lats, lons)
CX = np.column_stack ((utm_result[0], utm_result[1]))
EDM = euclidean_distances (CX)
euclidean_elapsed = time.perf_counter () - euclidean_tic
euclidean_elapsed_string = str (datetime.timedelta (seconds=euclidean_elapsed))
print (f"Time elapsed for euclidean distance matrix (seconds): {euclidean_elapsed:0.4f}")
print (f"Time elapsed for euclidean distance matrix (hh:mm:ss): {euclidean_elapsed_string}")
print ("")


# haversine test
HDM = np.zeros ((len (uids),len (uids)))
haversine_tic = time.perf_counter ()
RX = np.radians (X)
HDM = haversine_distances (RX)
HDM = HDM * 6371000
haversine_elapsed = time.perf_counter () - haversine_tic
haversine_elapsed_string = str (datetime.timedelta (seconds=haversine_elapsed))
print (f"Time elapsed for haversine distance matrix (seconds): {haversine_elapsed:0.4f}")
print (f"Time elapsed for haversine distance matrix (hh:mm:ss): {haversine_elapsed_string}")
print ("")

# geodesic test
GDM = np.zeros ((len (uids),len (uids)))
geodesic_tic = time.perf_counter ()
for i, (ilat, ilon) in enumerate (X):
#    print (f'{i}/{len(uids)}')
    for j, (jlat, jlon) in enumerate (X):
        GDM[i,j] = geodesic ((ilat, ilon), (jlat, jlon)).m
geodesic_elapsed = time.perf_counter () - geodesic_tic
geodesic_elapsed_string = str (datetime.timedelta (seconds=geodesic_elapsed))
print (f"Time elapsed for geodesic distance matrix (seconds): {geodesic_elapsed:0.4f}")
print (f"Time elapsed for geodesic distance matrix (hh:mm:ss): {geodesic_elapsed_string}")
print ("")


print (f"euclidean speedup over haversine: {haversine_elapsed / euclidean_elapsed}X")
print (f"euclidean speedup over geodesic: {geodesic_elapsed / euclidean_elapsed}X")
print (f"haversine speedup over geodesic: {geodesic_elapsed / haversine_elapsed}X")
print ("")

# check accuracy
low_indices = np.triu_indices (len (uids), 1)
ED = np.asarray (EDM[low_indices])
HD = np.asarray (HDM[low_indices])
GD = np.asarray (GDM[low_indices])

print ("ED")
print (ED)
print ("GD")
print (HD)
print ("HD")
print (GD)

euclidean_differences = np.zeros (len (GD))
haversine_differences = np.zeros (len (GD))
for i, e in enumerate (GD):
    euclidean_differences[i] = abs (GD[i] - ED[i]) / GD[i]
    haversine_differences[i] = abs (GD[i] - HD[i]) / GD[i]

print (f'euclidean difference over geodesic: {euclidean_differences.mean()}, 3sigma: {3 * euclidean_differences.std()}, max: {euclidean_differences.max()}, min {euclidean_differences.min()}')
print (f'haversine difference over geodesic: {haversine_differences.mean()}, 3sigma: {3 * haversine_differences.std()}, max: {haversine_differences.max()}, min {haversine_differences.min()}')
