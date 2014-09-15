import os
import io
import re
import sys
import json
import ogr
from shapely.geometry import Polygon
from random import uniform
import sqlite3
from globalmaptiles import GlobalMercator
import zipfile
from time import time
import csv

def create_tract_map(input_map_path, tract_list_path, field_name, output_map_path):
	# Read inputs
	with open(tract_list_path) as json_file:
		tracts = json.load(json_file)

	# open the geojson file
	ds = ogr.Open( input_map_path )
	if ds is None:
		print "Open failed.\n"
		sys.exit( 1 )

	lyr = ds.GetLayerByIndex( 0 )
	lyr.ResetReading()

	feat_defn = lyr.GetLayerDefn()
	field_defns = [feat_defn.GetFieldDefn(i) for i in range(feat_defn.GetFieldCount())]

	# Get the feature size we'll be mapping in.
	for i, defn in enumerate( field_defns ):
		if defn.GetName() == field_name:
			field_index = i

	geojson_feats = [feat for feat in lyr]
	feature_collection = {"type": "FeatureCollection",
	                      "features": []
 											  }

	for feat in geojson_feats:
		tract = feat.GetField(field_index)
		if tract in tracts:
			feature_collection["features"].append(feat.ExportToJson())
	with open(output_map_path, 'w') as f:
		json.dump(feature_collection, f, ensure_ascii=True)

create_tract_map("../static/data/maps/MA-TRACTS.geojson",
								 "../static/data/census/cambridge_tracts.json",
								 "TRACTCE10", "../static/data/maps/CAMBRIDGE-TRACTS.geojson")
