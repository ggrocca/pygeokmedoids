# PyGeoKMedoids

Application of [scikit-learn-extra's][1] k-medoids to the spatial clustering of geographic positions, expressed in latitude, longitude format (reference WGS84) . Beware: this is nothing more than a proof-of-concept. It might be interesting to anyone who's exploring a bit the capabilities of Python's statistical learning and geographical libraries, though. The code should be easy to read and modify.

The main application, `geokmedoids.py`, provides a command line interface to all relevant [k-medoids parameters][2] (number of clusters, method, initialization) and lets you choose among three different distance metrics:

- The euclidean distance as provided by scikit, after projection of all coordinates to UTM (using the [utm library][3]). This is the best combination of speed and accuracy, provided all the input locations are known to be in the same UTM zone (or near to one).
- The haversine distance, as provided by scikit, after conversion of the geographic position to radians. The haversine distance computes the distance of two points, using a sphere as an approximation for the Earth surface. Computation is way slower, but this might be a decent compromise if the input locations are scattered across multiple UTM zones.
- A true geodesic function over the ellipsoid (you might say that also the ellipsoid is an approximation for the earth surface, and you would be right, but let's say that at least is a way more accurate one, in particular if the locations are not separated by big elevation changes). This is the most precise method, unfortunately it's also very expensive to compute, at least with the library in use right now ([GeoPy][4]), so it's not going to work if you have more than a few hundred locations as input. I have to admit that I have not yet explored all possibilities, though: [GeographicLib's python bindings][5] could provide a better, faster implementation, and I have not experimented with vectorizing the geodesic distance operation to take advantage of numpy's optimization features,  which could provide a big speed-up.

Keep in mind that several parameters and distance combinations might result in very long computation times, depending on input size. k-medoids is an algorithm with [quadratic computational complexity][6].

It would interesting to do the same experiment with [hierarchical / agglomerative clustering][7] too.

[1]: https://scikit-learn-extra.readthedocs.io/en/stable/
[2]: https://scikit-learn-extra.readthedocs.io/en/latest/generated/sklearn_extra.cluster.KMedoids.html
[3]: https://github.com/Turbo87/utm
[4]: https://geopy.readthedocs.io/en/stable/#module-geopy.distance
[5]: https://geographiclib.sourceforge.io/1.50/python/code.html#geographiclib.geodesic.Geodesic.Inverse
[6]: https://en.wikipedia.org/wiki/K-medoids
[7]: https://scikit-learn.org/stable/modules/clustering.html#hierarchical-clustering

## Install

Clone the repo, than create a virtual environment with an up to date python interpreter (>3.8), and install the requirements:
```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```


## Run

This project provides four utilities:

1) `geokmedoids.py` is the main program. It takes in input a set of geographic coordinates and writes in output three files: the first file contains the same locations, each labeled with the id of the cluster it belongs to; a second file with the set of generated clusters; and a third file with run information (parameters, time elapsed). The center of a cluster is one of the locations it contains. I/O is performed using csv files.
2) `graphylize.py` analyzes and graphs the results of `geokmedoids.py`. 
3) `collate.py` takes in input the results of `geokmedoids.py`, and converts them into a single file with a specific format.
4) `benchmark_distancemetrics.py` is a very quick benchmark for different distance metric computations (both performance and accuracy).

### geokmedoids.py

Goal: to divide the list of positions into separate K groups, and find for each group a centroid among one of the original positions. Input format: A csv with 3 columns `(id, lat, lon)`.
Output format: three different files (each with a timestamp in the name):
1) A csv of labeled positions, with 4 columns
`(id, gid, lat, lon)`;
2) A csv with the computed clusters, with 3 columns `(gid, lat, lon)`;
3) A run file with command arguments and time elapsed.

Example run (500 clusters, other options left as default):
```
python3 geokmedoids.py -c input.csv -o output -k 500
```

See the output of `python3 geokmedoids.py -h` for all options:
```
Required arguments:
  -c CSV_INPUT, --csv-input CSV_INPUT
                        Input path to a csv file, with format (id,lat,lon).

Optional arguments:
  -o OUTPUT_NAME, --output-name OUTPUT_NAME
                        Output path and name, to be applied as prefix of all generated files (default='output').
  -r RANDOM_STATE, --random-state RANDOM_STATE
                        Random seed (default=0).
  -k K_CLUSTERS, --k-clusters K_CLUSTERS
                        Number of target sets (default=200).
  -i ITER_MAX, --iter-max ITER_MAX
                        Maximum number of iterations (default=300).
  -s {random,heuristic,k-medoids++,build}, --start-init {random,heuristic,k-medoids++,build}
                        Initialization type (default='k-medoids++').
  -m {pam,alternate}, --method {pam,alternate}
                        Fit method (default='alternate').
  -d {euclidean,haversine,geodesic}, --distance-metric {euclidean,haversine,geodesic}
                        Select a distance metric. (default: 'euclidean'). When using euclidean, positions are
                        projected to UTM. Warning: the geodesic method is very precise, but really slow. Leave this
                        option to euclidean unless the input locations span multiple UTM zones, and use haversine
                        otherwise. Euclidean distances over UTM are way faster to compute, and more precise than
                        haversine when locations are local enough.
```

### graphylize.py

This utlity performs a basic analysis of the main output (distribution of distances to the centers, and of cluster sizes), with simple [matplotlib](https://matplotlib.org/) graphs (close the first graph to see the second one when running it). Example run:
```
python3 graphylize.py -p output_*_positions.csv -c output_*_centers.csv -d euclidean
```

### collate.py

This utility converts `geokmedoids.py`'s output into a different format, discarding original locations and keeping just the cluster centers. The assumption is that each location in input has an identity, and that each identity can own multiple locations. The output file contains one line for each identity (not for each location). Each identity is assigned to the cluster to which most of its locations belong to. The last column, `potential_group_members`, contains all the companions: all the other identities that belong to the same group.

The output has the format:
```
(user_id, start_point_id, start_point_latitude, start_point_longitude, potential_group_members)
```

Run as follow:
```
python3 collate.py -p output_*_positions.csv -c output_*_centers.csv -o fused.csv
```


### benchmark_distancemetrics.py

A quick and simple standalone test showing computation times and accuracy for different distance metrics. The reference distance is the one computed using the geodesic method.
Run as follow:
```
python3 benchmark_distancemetrics.py input.csv
```
