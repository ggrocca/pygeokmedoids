import sys
import argparse
import numpy as np
from collections import namedtuple

parser = argparse.ArgumentParser (description="collate pygeokmedoids results in a single output file, with format (user_id,start_point_id,start_point_latitude,start_point_longitude,potential_group_members). Assumption: positions can share the same identity")

parser._action_groups.pop ()
required = parser.add_argument_group ('Required arguments')
optional = parser.add_argument_group ('Optional arguments')

required.add_argument ('-p', '--positions',
                      required=True,
                      help="Input path to a csv file, with format (uid,gid,latitude,longitude).")

required.add_argument ('-c', '--centers',
                      required=True,
                      help="Input path to a csv file, with format (gid,latitude,longitude).")

optional.add_argument ('-o', '--output',
                      default="collated.csv",
                      help="Output file (default='collated.csv').")

args = parser.parse_args ()

# load positions, with their id and label
pos_uids,pos_gids,pos_lats,pos_lons = np.genfromtxt (args.positions, delimiter=',', names=True, dtype="S8,S36,f8,f8", unpack=True)
pos_uids = [u.decode (encoding='UTF-8') for u in pos_uids]
pos_gids = [u.decode (encoding='UTF-8') for u in pos_gids]

# Load label centers and names
cen_gids,cen_lats,cen_lons = np.genfromtxt (args.centers, delimiter=',', names=True, dtype="S36,f8,f8", unpack=True)
cen_gids = [u.decode (encoding='UTF-8') for u in cen_gids]

# Compute a label names dictionary "gids"
# This data structure holds, for each label, its center
# {key: label_id, value: lat,lon}
Pos = namedtuple ('Pos', ['lat', 'lon'])
gids = {}
for gid, lat, lon in zip (cen_gids,cen_lats,cen_lons):
    gids[gid] = Pos (lat,lon)

# Compute a position identities dictionary "uids"
# This data structure holds, for each identity, all the groups it belongs to, and with how many occurences.
# dictionary uids {key: position_id, value: dictionary _ {key: label_id, value: N_occurences} }
uids = {}
for uid, gid in zip (pos_uids, pos_gids):
    if uid not in uids:
        uids[uid] = {}
    if gid in uids[uid]:
        uids[uid][gid] += 1
    else:
        uids[uid][gid] = 1

# Initialize a label members dictionary "gids_members"
# This data structure will hold, for each label, all the identities that have most positions marked with that label
# dictionary gids {key: label_id, value: dictionary _ {key: position_id, value: True} }
gids_members = {}
for gid in gids:
    gids_members[gid] = {}

# Fill "gids_members"
# Compute a position identities dictionary "uids_maxgroup"
# This data structure holds, for each identity, the label that occurs the most for that identity
# dictionary uids_maxgroup {key: position_id, value: label_id}
uids_maxgroup = {}
for uid in uids:
    max_group = max (uids[uid], key=uids[uid].get)
    gids_members[max_group][uid] = True
    uids_maxgroup[uid] = max_group 

# Write output: for each unique identity, the label of the final group it belongs to, the group location, and all other identities belonging to the same group
def dict_without_key_tostring (d, k):
    nd = d.copy ()
    nd.pop (k)
    return ','.join (nd)
with open (args.output, 'w') as fo:
    print ('user_id,start_point_id,start_point_latitude,start_point_longitude,potential_group_members', file=fo)        
    for uid in uids:
        max_group = uids_maxgroup[uid]
        members = dict_without_key_tostring (gids_members[max_group], uid)
        print (f'{uid},{max_group},{gids[max_group].lat},{gids[max_group].lon},"{members}"', file=fo)
