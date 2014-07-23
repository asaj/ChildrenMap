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

def make_ogr_point(x,y):
	return ogr.Geometry(wkt="POINT(%f %f)"%(x,y))

def get_bbox(geom):
	ll=float("inf")
	bb=float("inf")
	rr=float("-inf")
	tt=float("-inf")

	ch = geom.ConvexHull()
	if not ch:
		return None
	bd = ch.GetBoundary()
	if not bd:
		return None
	pts = bd.GetPoints()
	if not pts:
		return None

	for x,y in pts:
		ll = min(ll,x)
		rr = max(rr,x)
		bb = min(bb,y)
		tt = max(tt,y)
		
	return (ll,bb,rr,tt)
			
def add_digits(data, num_digits):
	if num_digits == 0:
		return data
	if num_digits == 1:
		new_data = []
		for d in data:
			for i in range(10):
				new_data.append(d + str(i))
		return new_data
	else:
		return add_digits(data, num_digits - 1)

def within_n_digits(shorter, longer_array, n):
	for l in longer_array:
		if str.startswith(str(l), shorter) and len(str(l)) - len(shorter) <= n:
			return True
	return False

# Maps geojson keys into arrays containing csv_keys.  Each csv_key should be mapped to exactly once.
def gisjoin_match_keys(geojson_keys, csv_keys):
	num_matched_csv_keys = 0
	key_map = {}
	for csv_key in csv_keys:
		found = True
		# Look for exact match
		if csv_key in geojson_keys:
			matched_geojson_key = csv_key
		# Remove last character from csv_key, look for match
		elif csv_key[:-1] in geojson_keys:
			matched_geojson_key = csv_key[:-1]
		# Insert a '0' between the last and second to last character in csv_key, look for match
		elif csv_key[:-1] + '0' + csv_key[-1:] in geojson_keys:
			matched_geojson_key = csv_key[:-1] + '0' + csv_key[-1:]
		else:
			# Remove last charcter from csv_key, see if is a substring of geojson key
			matched_geojson_keys = [geojson_key for geojson_key in geojson_keys if str.startswith(geojson_key, csv_key[:-1])]
			if len(matched_geojson_keys) == 1:
				matched_geojson_key = matched_geojson_keys[0]
			else:
				if len(matched_geojson_keys) > 0:
					print "Removing one character from geojson keys causes csv key " + csv_key + " to match multiple geojson keys " + str(matched_geojson_keys)
				found = False
		if found:
			num_matched_csv_keys += 1
			#print "CSV key " + csv_key + " matches geojson key " + matched_geojson_key
			if matched_geojson_key not in key_map.keys():
				key_map[matched_geojson_key] = [csv_key]
			else:
				key_map[matched_geojson_key].append(csv_key)
		else:
			print "CSV key " + csv_key + " has no matching geojson key."
	print "Mapped " + str(len(key_map.keys())) + " geojson features to " + str(num_matched_csv_keys) + " csv rows."
	return key_map
				
def map_sum_data_from_columns(csv_path, key_column, sum_columns, restrict_column, restrict_values):
	print "Processing %s"%csv_path
	map_sum_data = {}
	sum_column_indices = []
	
	with open(csv_path, 'rb') as csvfile:
		census_reader = csv.reader(csvfile, delimiter='\t', quotechar='|')
		first_row = True
		for row in census_reader:
			# Find index of interesting columns.
			if first_row:
				first_row = False
				for i, data in enumerate(row):
					if data in sum_columns:
						sum_column_indices.append(i)
					if data == key_column:
						key_column_index = i
					if data == restrict_column:
						restrict_column_index = i
			else:
				# Sum the number of children in this row.
				sum = 0
				for i, data in enumerate(row):
					if i == key_column_index:
						key = data
					if i in sum_column_indices:
						sum += int(data)
					if i == restrict_column_index:
						restrict_value = data
				# Only add to the map areas we are interested in.
				if (within_n_digits(restrict_value, restrict_values, 2)) :
					map_sum_data[key] = sum
	print "Found " + str(len(map_sum_data.keys())) + " matching rows."
	return map_sum_data
	
def main(args_dict):
	# Read inputs
	input_geojson = args_dict["input_geojson"]
	geo_feat_name = args_dict["geo_feat_name"]
	output_json = args_dict["output_json"]
	input_csv = args_dict["input_csv"] 
	csv_key_column = args_dict["csv_key_column"]
	csv_sum_columns = args_dict["csv_sum_columns"]
	csv_restrict_column = args_dict["csv_restrict_column"]
	csv_restrict_values_file = args_dict["csv_restrict_values_file"]
	with open(csv_restrict_values_file) as json_file:
		csv_restrict_values = json.load(json_file)
	# Get a map of geographical features to number of children.
	map_sum_data = map_sum_data_from_columns(input_csv, csv_key_column, csv_sum_columns, csv_restrict_column, csv_restrict_values) 

	print "Processing: %s - Ctrl-Z to cancel"%input_geojson
	merc = GlobalMercator()

	# open the geojson file
	ds = ogr.Open( input_geojson )
	if ds is None:
		print "Open failed.\n"
		sys.exit( 1 )

	lyr = ds.GetLayerByIndex( 0 )
	lyr.ResetReading()

	feat_defn = lyr.GetLayerDefn()
	field_defns = [feat_defn.GetFieldDefn(i) for i in range(feat_defn.GetFieldCount())]

	# Get the feature size we'll be mapping in.
	for i, defn in enumerate( field_defns ):
		if defn.GetName()==geo_feat_name:
			print "Found field " + geo_feat_name + " in " + input_geojson
			geo_field = i

	# set up the output file
	# if it already exists, delete it
	if os.path.isfile(output_json):
		os.system("rm %s"%output_json)
	
	n_features = len(lyr)

	points_dict = {}
	points_list = []
	total_sum = 0
	geojson_feats = [feat for feat in lyr]
	geojson_keys = [feat.GetField(geo_field) for feat in geojson_feats]
	key_map = gisjoin_match_keys(geojson_keys, map_sum_data.keys())
	total_matching_geo_feats = len(key_map.keys())
	for feat in geojson_feats:
		# Get population
		geo_feat = feat.GetField(geo_field)
		
		# GISJOIN values in csv and geojson don't line up.
		pop = 0
		if geo_feat in key_map.keys():
			matching_keys = key_map[geo_feat]
			for k in matching_keys:
				pop += map_sum_data[k]
		total_sum += pop

		# Get geometry
		geom = feat.GetGeometryRef()
		if geom is None:
			continue

		# Get bounding box of geometry
		bbox = get_bbox( geom )
		if not bbox:
			continue
		ll,bb,rr,tt = bbox

		# generate a sample within the geometry for every person
		for i in range(pop):
			while True:
				samplepoint = make_ogr_point( uniform(ll,rr), uniform(bb,tt) )
				if geom.Intersects( samplepoint ):
					break
			point_dict = {}
			point_dict["lat"] = samplepoint.GetY()
			point_dict["lng"] = samplepoint.GetX()
			point_dict["distance"] = 10
			point_dict["place_id"] = 1
			points_list.append(point_dict)

	# Write to file
	print "Finished processing %s"%output_json
	print "Found " + str(total_sum) + " households with children."
	points_dict["points"] = points_list
	with open(output_json, 'w') as f:
	  json.dump(points_dict, f, ensure_ascii=False)
"""
args_dict = {}
args_dict["input_geojson"] = "../static/data/maps/MA-TRACTS.geojson"
args_dict["geo_feat_name"] = "GISJOIN"
args_dict["input_csv"] = "../static/data/census/children2012.csv"
args_dict["csv_geo_feat_name"] = "GISJOIN"
args_dict["children_columns"] =  ["QT6E003", "QT6E010", "QT6E016"]
args_dict["csv_geo_restrict_feat_name"] = "TRACTA"
args_dict["csv_geo_restrict_feats_file"] = "../static/data/census/cambridge_tracts.json"
args_dict["output_file"] = "../static/data/children/children2012.json"
main(args_dict)

args_dict = {}
args_dict["input_geojson"] = "../static/data/maps/MA-TRACTS.geojson"
args_dict["geo_feat_name"] = "GISJOIN"
args_dict["input_csv"] = "../static/data/census/children2010.csv"
args_dict["csv_key_column"] = "GISJOIN"
args_dict["csv_sum_columns"] =  ["H8D008", "H8D012", "H8D015"]
args_dict["csv_restrict_column"] = "TRACTA"
args_dict["csv_restrict_values_file"] = "../static/data/census/cambridge_tracts.json"
args_dict["output_json"] = "../static/data/children/children2010copy.json"
main(args_dict)
"""
args_dict = {}
args_dict["input_geojson"] = "../static/data/maps/MA-TRACTS.geojson"
args_dict["geo_feat_name"] = "GISJOIN"
args_dict["input_csv"] = "../static/data/census/children1990.csv"
args_dict["csv_key_column"] = "GISJOIN"
args_dict["csv_sum_columns"] =  ["ET8003", "ET8005", "ET8007"]
args_dict["csv_restrict_column"] = "TRACTA"
args_dict["csv_restrict_values_file"] = "../static/data/census/cambridge_tracts.json"
args_dict["output_json"] = "../static/data/children/children1990.json"
main(args_dict)
"""
cambridge_tracts = [str(i) for i in range(352100, 355100)] 
with open("../static/data/census/cambridge_tracts.json", 'w') as f:
  json.dump(cambridge_tracts, f, ensure_ascii=False)
"""
