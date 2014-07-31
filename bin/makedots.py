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

# Maps geojson keys into arrays containing csv_keys.  Each csv_key should be mapped to exactly once.
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
						if row[i] == '':
							continue
						sum += int(row[i])
					if key in map_sum_data.keys():
						map_sum_data[key] += sum
					else:
						map_sum_data[key] = sum
					total += sum
	print "Found " + str(len(map_sum_data.keys())) + " matching rows with a total sum of " + str(total)
	return map_sum_data

def map_tract_to_gisjoin(csv_path, gisjoin_column, tract_column, restrict_column, restrict_values):
	print "Mapping tracts to gisjoins."
	map_tract_gisjoin = {}
	num_gisjoins = 0
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
					num_gisjoins += 1
					gisjoin = row[gisjoin_column_index]
					tract = row[tract_column_index]
					if tract not in map_tract_gisjoin.keys():
						map_tract_gisjoin[tract] = [gisjoin]
					else:
						map_tract_gisjoin[tract].append(gisjoin)
	print "Mapped " + str(len(map_tract_gisjoin.keys())) + " tracts to " + str(num_gisjoins) + " gisjoins."
	return map_tract_gisjoin

def main(args_dict):
	# Read inputs
	output_json = args_dict["output_json"]
	csv_path = args_dict["input_csv"] 
	key_column = args_dict["csv_key_column"]
	children_columns = args_dict["csv_sum_columns"]
	pop_columns = args_dict["csv_denominator_columns"]
	restrict_column = args_dict["csv_restrict_column"]
	restrict_values_file = args_dict["csv_restrict_values_file"]
	with open(restrict_values_file) as json_file:
		restrict_values = json.load(json_file)
	
	print "------------------------------------------"
	print "Getting map of tracts to gisjoins."
	map_tract_gisjoin = map_tract_to_gisjoin(csv_path, "GISJOIN", "TRACTA", restrict_column, restrict_values)
	print "Found map of " + str(len(map_tract_gisjoin.keys())) + " tracts to gisjoins."

	print "------------------------------------------"
	print "Making map of tracts to children."
	map_tract_children = map_sum_data_from_columns(csv_path, key_column, children_columns, restrict_column, restrict_values)
	print "------------------------------------------"
	print "Making map of tracts to population."
	map_tract_population = map_sum_data_from_columns(csv_path, key_column, pop_columns, restrict_column, restrict_values)
	
	points_dict = {}
	print "------------------------------------------"
	print "Creating points."
	args_dict = {}
	args_dict["input_geojson"] = "../static/data/maps/MA_blocks.geojson"
	args_dict["geo_gisjoin_name"] = "GISJOIN"
	args_dict["geo_tract_name"] = "TRACTCE10"
	args_dict["cambridge_tracts"] = restrict_values
	map_tract_points = mt2b.create_points(args_dict, map_tract_children, map_tract_population)

	total_children = 0
	total_population = 0
	for tract in map_tract_children.keys():
		total_children += map_tract_children[tract]
		total_population += map_tract_population[tract]
	data = {}
	city_data ={}
	city_data["name"] = "cambridge"
	city_data["children"] = total_children
	city_data["population"] = total_population
	data["cambridge"] = city_data

	total_points = 0
	for tract in map_tract_points.keys():
		total_points += len(map_tract_points[tract])

	print "Generated " + str(total_points) + " total points."
	# Write to file
	print "Finished processing %s"%output_json
	points_dict["points"] = map_tract_points
	for tract in map_tract_points.keys():
		tract_data = {}
		tract_data["population"] = map_tract_population[tract]
		tract_data["children"] = map_tract_children[tract]
		tract_data["name"] = tract
		lat = 0;
		lng = 0;
		center_data = {}
		for point in map_tract_points[tract]:
			lat += point["lat"]
			lng += point["lng"]
		lat = lat / len(map_tract_points[tract])
		lng = lng / len(map_tract_points[tract])
		center_data["lat"] = lat
		center_data["lng"] = lng
		tract_data["center"] = center_data
		data[tract] = tract_data
	points_dict["data"] = data
	points_dict["tracts"] = map_tract_points.keys()
	with open(output_json, 'w') as f:
	  json.dump(points_dict, f, ensure_ascii=False)
"""
"""
