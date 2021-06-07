import sys
import uuid
import time
import datetime
import argparse
import numpy as np
from geopy.distance import geodesic
from sklearn_extra.cluster import KMedoids
import utm

start = f"{datetime.datetime.now():%Y%m%d-%H%M%S}"

original_cli = ' '.join (sys.argv)

parser = argparse.ArgumentParser (description=
                                 "Application of scikit\'s k-medoids to geographic positions. "
                                 "Goal: to divide the list of positions into separate K groups, and find for each group a centroid among one of the original positions. "
                                 "Input format: A csv with 3 columns (id,lat,lon). "
                                 "Output format: three different files (each with a timestamp in the name) - "
                                 "1) A csv of labeled positions with 4 columns (id,gid,lat,lon); "
                                 "2) A csv of label centers with 3 columns (gid,lat,lon); "
                                 "3) A run file with command arguments and time elapsed."
                                 )

parser._action_groups.pop ()
required = parser.add_argument_group ('Required arguments')
optional = parser.add_argument_group ('Optional arguments')

required.add_argument ('-c', '--csv-input',
                      required=True,
                      help="Input path to a csv file, with format (id,lat,lon).")

optional.add_argument ('-o', '--output-name',
                      default="output",
                      help="Output path and name, to be applied as prefix of all generated files (default='output').")

optional.add_argument ('-r', '--random-state',
                      type=int,
                      default=0,
                      help="Random seed (default=0).")

optional.add_argument ('-k', '--k-clusters',
                      type=int,
                      default=200,
                      help="Number of target sets (default=200).")

optional.add_argument ('-i', '--iter-max',
                      type=int,
                      default=300,
                      help="Maximum number of iterations (default=300).")

optional.add_argument ('-s', '--start-init',
                      default="k-medoids++",
                      choices=['random', 'heuristic', 'k-medoids++', 'build'],
                      help="Initialization type (default='k-medoids++').")

optional.add_argument ('-m', '--method',
                      default="alternate",
                      choices=['pam', 'alternate'],
                      help="Fit method (default='alternate').")

optional.add_argument ('-d', '--distance-metric',
                      default="euclidean",
                      choices=['euclidean', 'haversine', 'geodesic'],
                      help="Select a distance metric. (default: 'euclidean'). When using euclidean, positions are projected to UTM. Warning: the geodesic method is very precise, but really slow. Leave this option to euclidean unless the input locations span multiple UTM zones, and use haversine otherwise. Euclidean distances over UTM are way faster to compute, and more precise than haversine when locations are local enough.")

args = parser.parse_args ()

input_file = args.csv_input
output_positions_file = f'{args.output_name}_{start}_positions.csv'
output_centers_file = f'{args.output_name}_{start}_centers.csv'
output_run_file = f'{args.output_name}_{start}_runinfo.txt'
kmedoids_random_state = args.random_state
kmedoids_n_clusters = args.k_clusters
kmedoids_max_iter = args.iter_max
kmedoids_init = args.start_init
kmedoids_method = args.method
kmedoids_metric = args.distance_metric

# Load positions
uids,lats,lons = np.genfromtxt (input_file, delimiter=',', names=True, dtype="S8,f8,f8", unpack=True)
uids = [u.decode (encoding='UTF-8') for u in uids]

if kmedoids_metric == 'euclidean':  # Project locations to UTM (cartesian coordinates)
    utm_result = utm.from_latlon (lats, lons)
    X = np.column_stack ((utm_result[0], utm_result[1]))
    utmz_n = utm_result[2]
    utmz_l = utm_result[3]
else:  # We keep geographic coordinates
    X = np.column_stack ((lats, lons))
if kmedoids_metric == 'haversine':  # in this case, we need radians
    X = np.radians (X)


# If we use geodesic as a callable, run times becomes too long.
# kmedoids_metric = lambda a, b: geodesic (a, b).m
# We try a to precompute a distance metric matrix.
# This is slow too, maybe the operation should be vectorized (numpy.vectorize)
if kmedoids_metric == 'geodesic':  # building a distance matrix of geodesic distances
    geodesic_tic = time.perf_counter ()
    DM = np.zeros ((len (uids),len (uids)))
    for i, (ilat, ilon) in enumerate (zip (lats, lons)):
        print (f'{i}/{len(uids)}')
        for j, (jlat, jlon) in enumerate (zip (lats, lons)):
            DM[i,j] = geodesic ((ilat, ilon), (jlat, jlon)).m
    geodesic_metric = DM
    geodesic_elapsed = time.perf_counter () - geodesic_tic
    geodesic_elapsed_string = str (datetime.timedelta (seconds=geodesic_elapsed))
    print (f"Time elapsed for geodesic distance matrix (seconds): {geodesic_elapsed:0.4f}")
    print (f"Time elapsed for geodesic distance matrix (hh:mm:ss): {geodesic_elapsed_string}")

# compute kmedoids
kmedoids_tic = time.perf_counter ()
kmedoids = KMedoids (n_clusters=kmedoids_n_clusters,
                     random_state=kmedoids_random_state,
                     init=kmedoids_init,
                     method=kmedoids_method,
                     metric=kmedoids_metric,
                     max_iter=kmedoids_max_iter).fit (X)
kmedoids_elapsed = time.perf_counter () - kmedoids_tic
kmedoids_elapsed_string = str (datetime.timedelta (seconds=kmedoids_elapsed))


# write positions in output, each with the computed label
gids = np.zeros (len (kmedoids.labels_))
gids = [uuid.uuid4 () for _ in gids]
with open (output_positions_file, 'w') as ft:
    print ('uid,gid,latitude,longitude', file=ft)
    for uid, label, lat, lon in zip (uids, kmedoids.labels_, lats, lons):
        print (f'{uid},{gids[label]},{lat},{lon}', file=ft)

# write labels in output, each with its center
if kmedoids_metric == 'euclidean':
    C = np.column_stack (utm.to_latlon (kmedoids.cluster_centers_[:,0], kmedoids.cluster_centers_[:,1], utmz_n, utmz_l))
if kmedoids_metric == 'haversine':
    C = np.degrees (kmedoids.cluster_centers_)
if kmedoids_metric == 'geodesic':
    C = kmedoids.cluster_centers_
with open (output_centers_file, 'w') as fc:
    print ('gid,latitude,longitude', file=fc)
    for i, pos in enumerate (C):
        print (f'{gids[i]},{pos[0]},{pos[1]}', file=fc)

# standard output summary
end= f"{datetime.datetime.now():%Y%m%d-%H%M%S}"
with open (output_run_file, 'w') as fr:
    print (original_cli, file=fr)
    print ("", file=fr)
    print (f"input: {input_file}", file=fr)
    print (f"output: {output_positions_file}, {output_centers_file}", file=fr)
    print ("", file=fr)
    print (f"kmedoids_random_state: {kmedoids_random_state}", file=fr)
    print (f"kmedoids_n_clusters: {kmedoids_n_clusters}", file=fr)
    print (f"kmedoids_max_iter: {kmedoids_max_iter}", file=fr)
    print (f"kmedoids_init: {kmedoids_init}", file=fr)
    print (f"kmedoids_method: {kmedoids_method}", file=fr)
    print (f"kmedoids_metric: {kmedoids_metric}", file=fr)
    print ("", file=fr)
    print (f"Time elapsed for K-medoids fit (seconds): {kmedoids_elapsed:0.4f}", file=fr)
    print (f"Time elapsed for K-medoids fit (hh:mm:ss): {kmedoids_elapsed_string}", file=fr)
    print (f"{sys.argv[0]} started at {start}", file=fr)
    print (f"{sys.argv[0]} ended at {end}", file=fr)
