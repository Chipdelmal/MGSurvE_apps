#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shutup; shutup.please()
from os import path
from sys import argv
import osmnx as ox
from shapely import wkt
from random import shuffle, uniform
from engineering_notation import EngNumber
import cartopy.crs as ccrs
import cartopy.feature as cf
import compress_pickle as pkl
import matplotlib
import matplotlib.pyplot as plt
from sklearn.cluster import AgglomerativeClustering, SpectralClustering, KMeans
import numpy as np
import pandas as pd
import MGSurvE as srv
import auxiliary as aux
ox.config(log_console=False , use_cache=True)
matplotlib.rc('font', family='Savoye LET')

if srv.isNotebook():
    (USR, COUNTRY, CODE, COMMUNE, COORDS, DIST) = (
        'sami',
        'Burkina Faso', 'BFA', 
        'Niangoloko', (10.2829, -4.9213), 3000
    )
else:
    (USR, COUNTRY, CODE, COMMUNE, COORDS, DIST) = argv[1:]
    COORDS = tuple(map(float, COORDS.split(', ')))
    DIST = int(DIST)
(PROJ, FOOTPRINT, CLUSTERS_ALG, CLUSTERS_NUM) = (
    ccrs.PlateCarree(), True, 
    KMeans, 750
)
###############################################################################
# Set Paths
###############################################################################
paths = aux.userPaths(USR)
###############################################################################
# Download Data
#   https://wiki.openstreetmap.org/wiki/Tag:place%3Dcity_block
#   tags={'building': True}
###############################################################################
BLD = ox.geometries.geometries_from_point(
    COORDS, tags={'building': True} , dist=DIST
)
NTW = ox.graph_from_point(
    COORDS, dist=DIST, network_type='all',
    retain_all=True, simplify=True, truncate_by_edge=True
)
BLD['centroid_lon'] = [poly.centroid.x for poly in BLD['geometry']]
BLD['centroid_lat'] = [poly.centroid.y for poly in BLD['geometry']]
BLD.reset_index(inplace=True)
###############################################################################
# Cluster Data
###############################################################################
if CLUSTERS_NUM and BLD.shape[0] > CLUSTERS_NUM:
    lonLats = np.array(list(zip(BLD['centroid_lon'], BLD['centroid_lat'])))
    clustering = CLUSTERS_ALG(n_clusters=CLUSTERS_NUM).fit(lonLats)
    BLD['cluster_id'] = clustering.labels_
else:
    BLD['cluster_id'] = range(0, BLD.shape[0])
###############################################################################
# Map
###############################################################################
STYLE_GD = {'color': '#8da9c4', 'alpha': 0.35, 'width': 0.5, 'step': 0.01, 'range': 1, 'style': ':'}
STYLE_BG = {'color': '#0b2545'}
STYLE_TX = {'color': '#faf9f9', 'size': 40}
STYLE_CN = {'color': '#faf9f9', 'alpha': 0.20, 'size': 25}
STYLE_BD = {'color': '#faf9f9', 'alpha': 0.950}
STYLE_RD = {'color': '#ede0d4', 'alpha': 0.100, 'width': 1.5}
CLUSTER_PALETTE= [
    '#f72585', '#b5179e', '#7209b7', '#560bad', '#3a0ca3',
    '#3f37c9', '#4361ee', '#4895ef', '#4cc9f0', '#80ed99',
    '#b8f2e6', '#e9ff70', '#fe6d73', '#ffc6ff', '#ffd670',
    '#a1b5d8', '#9e0059', '#f88dad', '#dfdfdf', '#ffeedd',
    '#d7e3fc', '#ef233c', '#eac4d5', '#04e762', '#ca7df9'
]
CLST_COL = CLUSTER_PALETTE*CLUSTERS_NUM
shuffle(CLST_COL)
G = ox.project_graph(NTW, to_crs=ccrs.PlateCarree())
(fig, ax) = ox.plot_graph(
    G, node_size=0, figsize=(40, 40), show=False,
    bgcolor=STYLE_BG['color'], edge_color=STYLE_RD['color'], 
    edge_alpha=STYLE_RD['alpha'], edge_linewidth=STYLE_RD['width']
)
if FOOTPRINT:
    (fig, ax) = ox.plot_footprints(
        BLD, ax=ax, save=False, show=False, close=False,
        bgcolor=STYLE_BG['color'], color=STYLE_BD['color'], 
        alpha=STYLE_BD['alpha']
    )
else:
    ax.scatter(
        BLD['centroid_lon'], BLD['centroid_lat'], 
        marker='x', s=STYLE_CN['size'], 
        color=STYLE_BD['color'], alpha=STYLE_BD['alpha']
    )
if CLUSTERS_NUM:
    (fig, ax) = ox.plot_footprints(
        BLD, ax=ax, save=False, show=False, close=False,
        bgcolor=STYLE_BG['color'], alpha=np.random.uniform(.35, .65),
        color=[CLST_COL[ix] for ix in BLD['cluster_id']], 
    )
ax.text(
    0.99, 0.01, 
    'Footprints: {}'.format(EngNumber(BLD.shape[0])), 
    transform=ax.transAxes, 
    horizontalalignment='right', verticalalignment='bottom', 
    color=STYLE_TX['color'], fontsize=STYLE_TX['size']
)
ylims = ax.get_ylim()
ax.set_ylim(ylims[0], ylims[1]*1.0001)
ax.text(
    0.5, 0.975,
    '{}'.format(COMMUNE), 
    transform=ax.transAxes, 
    horizontalalignment='center', verticalalignment='top', 
    color=STYLE_TX['color'], fontsize=STYLE_TX['size']*5
)
ax.vlines(
    np.arange(COORDS[1]-STYLE_GD['range'], COORDS[1]+STYLE_GD['range'], STYLE_GD['step']), 
    COORDS[0]-1, COORDS[0]+1, 
    colors=STYLE_GD['color'], alpha=STYLE_GD['alpha'], linestyles=STYLE_GD['style']
)
ax.hlines(
    np.arange(COORDS[0]-STYLE_GD['range'], COORDS[0]+STYLE_GD['range'], STYLE_GD['step']), 
    COORDS[1]-1, COORDS[1]+1, 
    colors=STYLE_GD['color'], alpha=STYLE_GD['alpha'], linestyles=STYLE_GD['style']
)
ax.set_facecolor(STYLE_BG['color'])
fig.savefig(
    path.join(paths['data'], 'HumanMobility', CODE, COMMUNE+'.png'), 
    facecolor=STYLE_BG['color'], bbox_inches='tight', pad_inches=1, dpi=300,
    transparent=False
)
plt.close('all')
###############################################################################
# Export to Disk
###############################################################################
pkl.dump(
    BLD, path.join(paths['data'], 'HumanMobility', CODE, COMMUNE+'_BLD'), 
    compression='bz2'
)
pkl.dump(
    NTW, path.join(paths['data'], 'HumanMobility', CODE, COMMUNE+'_NTW'), 
    compression='bz2'
)


# import matplotlib.font_manager
# from IPython.core.display import HTML
# def make_html(fontname):
#     return "<p>{font}: <span style='font-family:{font}; font-size: 24px;'>{font}</p>".format(font=fontname)
# code = "\n".join([make_html(font) for font in sorted(set([f.name for f in matplotlib.font_manager.fontManager.ttflist]))])
# HTML("<div style='column-count: 2;'>{}</div>".format(code))
