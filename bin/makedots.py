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
def map_csv_sum_to_map_geojson_sum(geojson_keys, csv_keys, map_csv_sum):
	num_matched_csv_keys = 0
	key_map = {}
	map_geojson_sum = {}

	for csv_key in csv_keys:
		# First, find geojson key that matches csv_key
		found = True
		matched_geojson_keys = []
		# Look for exact match
		if csv_key in geojson_keys:
			matched_geojson_key = csv_key
		# Check if csv_key is a substring of a geo_json_key
		elif any(csv_key in geojson_key for geojson_key in geojson_keys):
			matched_geojson_keys = [geojson_key for geojson_key in geojson_keys if csv_key in geojson_key] 
			if len(matched_geojson_keys) == 1:
				matched_geojson_key = matched_geojson_keys[0]
			elif len(matched_geojson_keys) > 1:
				print "CSV key " + csv_key + " is substring of multiple geojson keys " + str(matched_geojson_keys)
				found = False
		# Remove last character from csv_key, look for exact match
		elif csv_key[:-1] in geojson_keys:
			matched_geojson_key = csv_key[:-1]
		# Remove last character form csv_key, check if is a substring of geojson key
		elif any(csv_key[:-1] in geojson_key for geojson_key in geojson_keys):
			matched_geojson_keys = [geojson_key for geojson_key in geojson_keys if csv_key[:-1] in geojson_key] 
			if len(matched_geojson_keys) == 1:
				matched_geojson_key = matched_geojson_keys[0]
			elif len(matched_geojson_keys) > 1:
				print "Removing one character from geojson keys causes csv key " + csv_key + " to match multiple geojson keys " + str(matched_geojson_keys)
				found = False
		# Insert a '0' between the last and second to last character in csv_key, look for match
		elif csv_key[:-1] + '0' + csv_key[-1:] in geojson_keys:
			matched_geojson_key = csv_key[:-1] + '0' + csv_key[-1:]
		else:
			found = False

		# If a matching key was found, add the csv sum to the geojson map
		if found:
			num_matched_csv_keys += 1
			if matched_geojson_key in map_geojson_sum.keys():
				map_geojson_sum[matched_geojson_key] = map_geojson_sum[matched_geojson_key] + map_csv_sum[csv_key]
			else:
				map_geojson_sum[matched_geojson_key] = map_csv_sum[csv_key]
		# If multiple matching keys were found, divide the csv sum evenly amongst them
		elif len(matched_geojson_keys) > 0:
			for mgk in matched_geojson_keys:
				if mgk in map_geojson_sum.keys():
					map_geojson_sum[mgk] = map_geojson_sum[mgk] + map_csv_sum[csv_key]/len(matched_geojson_keys)
				else:
					map_geojson_sum[mgk] = map_csv_sum[csv_key]/len(matched_geojson_keys)
		else:
			print "CSV key " + csv_key + " has no matching geojson key."
	print "Mapped " + str(len(map_geojson_sum.keys())) + " geojson features to " + str(num_matched_csv_keys) + " csv rows."
	return map_geojson_sum
				
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
				if (within_n_digits(row[restrict_column_index], restrict_values, 2)):
					key = row[key_column_index]
					sum = 0
					for i in sum_column_indices:
						sum += int(row[i])
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
	csv_denominator_columns = args_dict["csv_denominator_columns"]
	csv_restrict_column = args_dict["csv_restrict_column"]
	csv_restrict_values_file = args_dict["csv_restrict_values_file"]
	with open(csv_restrict_values_file) as json_file:
		csv_restrict_values = json.load(json_file)
	# Get a map of geographical features to number of children.
	map_sum_data = map_sum_data_from_columns(input_csv, csv_key_column, csv_sum_columns, csv_restrict_column, csv_restrict_values) 
	map_denominator_data = map_sum_data_from_columns(input_csv, csv_key_column, csv_denominator_columns, csv_restrict_column, csv_restrict_values) 

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
	map_geojson_sum = map_csv_sum_to_map_geojson_sum(geojson_keys, map_sum_data.keys(), map_sum_data)
	map_geojson_denominator = map_csv_sum_to_map_geojson_sum(geojson_keys, map_denominator_data.keys(), map_denominator_data)

	for feat in geojson_feats:
		# Get population
		geo_feat = feat.GetField(geo_field)
		
		# GISJOIN values in csv and geojson don't line up.

		pop = 0
		if geo_feat in map_geojson_sum.keys():
			pop = map_geojson_sum[geo_feat]
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
			point_dict["density"] = (pop * 100) / map_geojson_denominator[geo_feat]
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
args_dict["csv_denominator_columns"] =  ["H8D001"]
args_dict["csv_restrict_column"] = "TRACTA"
args_dict["csv_restrict_values_file"] = "../static/data/census/cambridge_tracts.json"
args_dict["output_json"] = "../static/data/children/children2010density.json"
main(args_dict)
"""

args_dict = {}
args_dict["input_geojson"] = "../static/data/maps/MA-TRACTS.geojson"
args_dict["geo_feat_name"] = "GISJOIN"
args_dict["input_csv"] = "../static/data/census/children2000.csv"
args_dict["csv_key_column"] = "GISJOIN"
args_dict["csv_sum_columns"] =  ["GIO001", "GIO003", "GIO005"] 
args_dict["csv_denominator_columns"] =  ["GIO001", "GIO002", "GIO003", "GIO004", "GIO005", "GIO006"]
args_dict["csv_restrict_column"] = "TRACTA"
args_dict["csv_restrict_values_file"] = "../static/data/census/cambridge_tracts.json"
args_dict["output_json"] = "../static/data/children/children2000.json"
main(args_dict)

"""
args_dict = {}
args_dict["input_geojson"] = "../static/data/maps/MA-TRACTS.geojson"
args_dict["geo_feat_name"] = "GISJOIN"
args_dict["input_csv"] = "../static/data/census/children1990.csv"
args_dict["csv_key_column"] = "GISJOIN"
args_dict["csv_sum_columns"] =  ["ET8003", "ET8005", "ET8007"]
args_dict["csv_denominator_columns"] =  ["ET8001", "ET8002", "ET8003", "ET8004", "ET8005", "ET8006", "ET8007", "ET8008", "ET8009", "ET8010"]
args_dict["csv_restrict_column"] = "TRACTA"
args_dict["csv_restrict_values_file"] = "../static/data/census/cambridge_tracts.json"
args_dict["output_json"] = "../static/data/children/children1990density.json"
main(args_dict)

args_dict = {}
args_dict["input_geojson"] = "../static/data/maps/MA-TRACTS.geojson"
args_dict["geo_feat_name"] = "GISJOIN"
args_dict["input_csv"] = "../static/data/census/children1980.csv"
args_dict["csv_key_column"] = "GISJOIN"
args_dict["csv_sum_columns"] =  ["DI1001", "DI1002", "DI1003", "DI1005", "DI1006", "DI1007"]     
args_dict["csv_denominator_columns"] =  ["DI1001", "DI1002", "DI1003", "DI1004", "DI1005", "DI1006", "DI1007", "DI1005"]     
args_dict["csv_restrict_column"] = "TRACTA"
args_dict["csv_restrict_values_file"] = "../static/data/census/cambridge_tracts.json"
args_dict["output_json"] = "../static/data/children/children1980density.json"
main(args_dict)

args_dict = {}
args_dict["input_geojson"] = "../static/data/maps/MA-TRACTS.geojson"
args_dict["geo_feat_name"] = "GISJOIN"
args_dict["input_csv"] = "../static/data/census/children1970.csv"
args_dict["csv_key_column"] = "GISJOIN"
args_dict["csv_sum_columns"] =  ["C1W002", "C1W003", "C1W005", "C1W006", "C1W008", "C1W009"]
args_dict["csv_denominator_columns"] =  ["C1W002", "C1W003", "C1W004", "C1W005", "C1W006", "C1W007", "C1W008", "C1W009"]
args_dict["csv_restrict_column"] = "TRACTA"
args_dict["csv_restrict_values_file"] = "../static/data/census/cambridge_tracts.json"
args_dict["output_json"] = "../static/data/children/children1970density.json"
main(args_dict)

args_dict = {}
args_dict["input_geojson"] = "../static/data/maps/MA-TRACTS.geojson"
args_dict["geo_feat_name"] = "GISJOIN"
args_dict["input_csv"] = "../static/data/census/children1960.csv"
args_dict["csv_key_column"] = "GISJOIN"
args_dict["csv_sum_columns"] =  ["B8M002", "B8M003", "B8M005", "B8M007", "B8M008", "B8M010"]
args_dict["csv_denominator_columns"] =  ["B8M002", "B8M003", "B8M005", "B8M007", "B8M008", "B8M010"]
args_dict["csv_restrict_column"] = "TRACTA"
args_dict["csv_restrict_values_file"] = "../static/data/census/cambridge_tracts.json"
args_dict["output_json"] = "../static/data/children/children1960.json"
main(args_dict)

cambridge_tracts = [str(i) for i in range(352100, 355100)] 
with open("../static/data/census/cambridge_tracts.json", 'w') as f:
  json.dump(cambridge_tracts, f, ensure_ascii=False)
"""
