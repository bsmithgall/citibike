#!/usr/bin/python2.7
# Author: Ben Smithgall

import requests
import math
import operator
import itertools
import networkx as nx
from cluster import KMeansClustering

STATIONS_ENDPOINT = 'http://citibikenyc.com/stations/json'
DIST_ENDPOINT = 'http://appservices.citibikenyc.com/data2/stations.php'

def prep_stations(url):
    """Returns a list where each element of that list is a station
    retreived from the endpoint passed in above"""
    stations = []
    _stations = requests.get(url).json()

    for _station in _stations['stationBeanList']:
        if _station['statusKey'] == 1:
            stations.append([_station['stationName'], _station['id'],
                             _station['availableDocks'], _station['totalDocks'],
                             _station['latitude'], _station['longitude']])

    return stations

def cluster_stations(stations, empty='empty'):
    """Uses the cluster library to perform kmeans geographical kmeans
    clustering on the input stations list. Expects a list of that
    format returned by prep_stations, and returns a list similar
    to the input list with the cluster number of each element added
    """
    if empty == 'empty':
        tocluster = [i for i in stations if (i[3] - i[2])/float(i[3]) < .2]
    else:
        tocluster = [i for i in stations if (i[2])/float(i[3]) < .2]
    cl = KMeansClustering([(i[4], i[5]) for i in tocluster])
    clusters = cl.getclusters(4)

    # Note that this returns a list of lists of lat/long tuples. We're
    # going to have to re-associate them back to the rest of the stations

    clustered = []
    for ix, i in enumerate(clusters):
        for j in i:
            for k in tocluster:
                if (j[0], j[1]) == (k[4], k[5]):
                    clustered.append([k[0], k[1], k[2],
                        k[3], k[4], k[5], ix+1])

    return clustered

def haversine(long1, lat1, long2, lat2):
    R = 6371 # Earth mean radius (in km)
    delta_long = long2 - long1
    delta_lat = lat2 - lat1
    a = math.sin(delta_lat/2)**2 + math.cos(lat1) * \
        math.cos(lat2) * math.sin(delta_long/2)**2
    c = 2 * math.asin(min(1,math.sqrt(a)))
    d = R * c
    return d

def haversine_distance(long1, lat1, long2, lat2):
    return haversine(math.radians(long1), math.radians(lat1),
                     math.radians(long2), math.radians(lat2))

def get_graph_breakdown(clustered):
    """Take clustered, and explode it outward into a list
    of edges. that can be added to a networkx as graph using
    add_weighted_edges_from"""
    edges, output = [], []
    combs = itertools.combinations(clustered, 2)
    for i in combs:
        edge1 = i[0][0]
        edge2 = i[1][0]
        dist = haversine_distance(i[0][5], i[0][4],
                                  i[1][5], i[1][4])

        if dist < .8:
            edges.append((edge1, edge2, dist))

    G = nx.DiGraph()
    G.add_weighted_edges_from(edges)
    degcent = nx.degree_centrality(G).items()

    for i in clustered:
        for j in degcent:
            if i[0] == j[0]:
                output.append([i[0], i[1], i[2],
                    i[3], i[4], i[5], i[6], j[1]])

    return output

def make_recs(graph_output, dist_url):
    recs, nearby = [], []
    _dists = requests.get(dist_url).json()
    nearbyLookup = dict((i['id'], [j['id'] for j in i['nearbyStations']]) for i in _dists['results'])

    for i in sorted(graph_output, key=operator.itemgetter(7), reverse=True):
        if i[1] not in nearby:
            recs.append(i)
        nearby.append(nearbyLookup[i[1]])
        if len(recs) > 4:
            break

    return recs

def get_recs(empty):
    output = []
    stations_toclutser = prep_stations(STATIONS_ENDPOINT)
    stations_cluster = cluster_stations(stations_toclutser, empty)
    for i in xrange(1, 5):
        cluster = [j for j in stations_cluster if j[-1] == i]
        output.extend(make_recs(get_graph_breakdown(cluster), DIST_ENDPOINT))

    return output
