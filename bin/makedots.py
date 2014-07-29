import os
import io
import re
import sys
import json
import ogr
from shapely.geometry import Polygon
from random import uniform
import sqlite3
import map_tracts_to_blocks as mt2b
import csv

def make_ogr_point(x,y):
	return ogr.Geometry(wkt="POINT(%f %f)"%(x,y))

def point_in_bbox(x, y, bbox):
	ll,bb,rr,tt = bbox
	return x >= ll and x <= rr and y <= tt and y >= bb

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
	
	total = 0
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
				if (row[restrict_column_index] in restrict_values):
					key = row[key_column_index]
					sum = 0
					for i in sum_column_indices:
						sum += int(row[i])
					map_sum_data[key] = sum
					total += sum
	print "Found " + str(len(map_sum_data.keys())) + " matching rows with a total sum of " + str(total)
	return map_sum_data

def map_gisjoin_to_tract(csv_path, gisjoin_column, tract_column, restrict_column, restrict_values):
	print "Mapping gisjoin to tracts"
	map_gisjoin_tract = {}
	unique_tracts = []
	with open(csv_path, 'rb') as csvfile:
		census_reader = csv.reader(csvfile, delimiter='\t', quotechar='|')
		first_row = True
		for row in census_reader:
			# Find index of interesting columns.
			if first_row:
				first_row = False
				for i, data in enumerate(row):
					if data == restrict_column:
						restrict_column_index = i
					if data == gisjoin_column:
						gisjoin_column_index = i
					if data == tract_column:
						tract_column_index = i
			else:
				if (row[restrict_column_index] in restrict_values):
					gisjoin = row[gisjoin_column_index]
					tract = row[tract_column_index]
					if tract not in unique_tracts:
						unique_tracts.append(tract)
					map_gisjoin_tract[gisjoin] = tract
	print "Mapped " + str(len(map_gisjoin_tract.keys())) + " gisjoins to " + str(len(unique_tracts)) + " unique tracts."
	return map_gisjoin_tract
	
def get_sum_and_denominator_tract_maps(args_dict, map_gisjoin_tract):
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
	bbox_file = args_dict["bbox_file"]
	with open(csv_restrict_values_file) as json_file:
		csv_restrict_values = json.load(json_file)
	# Get a map of gisjoin to number of children.
	map_sum_data = map_sum_data_from_columns(input_csv, csv_key_column, csv_sum_columns, csv_restrict_column, csv_restrict_values) 
	# Get a map of gisjoin to total population
	map_denominator_data = map_sum_data_from_columns(input_csv, csv_key_column, csv_denominator_columns, csv_restrict_column, csv_restrict_values) 

	# Get a map of tract to number of children
	map_tract_children = {}
	for gisjoin in map_sum_data.keys():
		tract = map_gisjoin_tract[gisjoin]
		if tract in map_tract_children.keys():
			map_tract_children[tract] += map_sum_data[gisjoin]
		else:
			map_tract_children[tract] = map_sum_data[gisjoin]

	total_children = 0
	for tract in map_tract_children.keys():
		total_children += map_tract_children[tract]
	print "Mapped " + str(len(map_tract_children.keys())) + " tracts to " + str(total_children) + " total children."

	# Get a map of tract to total population
	map_tract_population = {}
	for gisjoin in map_denominator_data.keys():
		tract = map_gisjoin_tract[gisjoin]
		if tract in map_tract_population.keys():
			map_tract_population[tract] += map_denominator_data[gisjoin]
		else:
			map_tract_population[tract] = map_denominator_data[gisjoin]
	total_pop = 0
	for tract in map_tract_population.keys():
		total_pop += map_tract_population[tract]
	print "Mapped " + str(len(map_tract_population.keys())) + " tracts to " + str(total_pop) + " total people."
	return (map_tract_children, map_tract_population)

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
	
	print "------------------------------------------"
	print "Making map of gisjoins to tracts." 
	with open(csv_restrict_values_file) as json_file:
		csv_restrict_values = json.load(json_file)
	map_gisjoin_tract = map_gisjoin_to_tract(input_csv, csv_key_column, csv_restrict_column, csv_restrict_column, csv_restrict_values)

	print "------------------------------------------"
	print "Making map of tracts to population."
	map_tract_children, map_tract_population = get_sum_and_denominator_tract_maps(args_dict, map_gisjoin_tract)

	points_dict = {}
	print "------------------------------------------"
	args_dict = {}
	args_dict["input_geojson"] = "../static/data/maps/MA_blocks.geojson"
	args_dict["geo_gisjoin_name"] = "GISJOIN"
	args_dict["geo_tract_name"] = "TRACTCE10"
	print "Creating points."
	map_tract_points = mt2b.create_points(args_dict, map_gisjoin_tract, map_tract_children, map_tract_population)
	total_points = 0
	for tract in map_tract_points.keys():
		total_points += len(map_tract_points[tract])

	print "Generated " + str(total_points) + " total points."
	# Write to file
	print "Finished processing %s"%output_json
	points_dict["points"] = map_tract_points
	points_dict["num_points"] = total_points 
	points_dict["tracts"] = map_tract_points.keys()
	with open(output_json, 'w') as f:
	  json.dump(points_dict, f, ensure_ascii=False)
"""
cambridge_tracts = [str(i) for i in range(352100, 355100)] 
with open("../static/data/census/cambridge_tracts.json", 'w') as f:
  json.dump(cambridge_tracts, f, ensure_ascii=False)
"""
