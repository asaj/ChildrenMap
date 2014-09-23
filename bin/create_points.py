import os
import io
import re
import sys
import json
import ogr
from shapely.geometry import Polygon
from random import uniform
import sqlite3
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
	if ll == float("inf") or bb == float("inf") or rr == float("-inf") or tt == float("-inf"):
		print "Can't find bounding box!"
		
	return (ll,bb,rr,tt)
			
def create_map_tract_points(input_geojson, geo_tract_name, map_tract_children, map_tract_population):
	# Read inputs
	print "------------------------------------------"
	print "Making map of tracts to points."

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
		if defn.GetName() == geo_tract_name:
			geo_tract_field = i

	geojson_feats = [feat for feat in lyr]

	# Map csv tracts to geojson tracts 
	map_geo_tract_geom = {}
	for feat in geojson_feats:
		tract = feat.GetField(geo_tract_field)
		# Get geometry
		geom = feat.GetGeometryRef()
		if geom is None:
			continue
		if tract in map_geo_tract_geom.keys():
			print "Found multiple geoms with tract " + tract
		else:
			map_geo_tract_geom[tract] = geom
	print "Found " + str(len(map_geo_tract_geom.keys())) + " tracts in geojson file."

	map_csv_tract_geom = {}
	in_csv_and_geojson = [tract for tract in map_tract_children.keys() if tract in map_geo_tract_geom.keys()]
	for tract in in_csv_and_geojson:
		map_csv_tract_geom[tract] = [map_geo_tract_geom[tract]]
	in_csv_but_not_geojson = [tract for tract in map_tract_children.keys() if tract not in map_geo_tract_geom.keys()]   
	in_geojson_but_not_csv = [tract for tract in map_geo_tract_geom.keys() if tract not in map_tract_children.keys()]   
	unmatched_geojson_tracts = in_geojson_but_not_csv
	if (len(in_csv_but_not_geojson) or len( in_geojson_but_not_csv)):
		print "------------------------------------------"
		print "Tracts in csv but not in geojson:"
		print in_csv_but_not_geojson
		print "------------------------------------------"
 		print "Tracts in geojson but not in csv:"
		print in_geojson_but_not_csv
		print "------------------------------------------"
 		print "Mapping tracts in csv to tracts in geojson."
		for csv_tract in in_csv_but_not_geojson:
			matching_tracts = [geo_tract for geo_tract in unmatched_geojson_tracts if csv_tract in geo_tract or geo_tract[:-1] in csv_tract]
			#if (len(matching_tracts) == 0):
		#		matching_tracts = [geo_tract for geo_tract in unmatched_geojson_tracts if csv_tract[:-1] in geo_tract[:-1]]
			for matching_tract in matching_tracts:
				map_tract_children[matching_tract] = map_tract_children[csv_tract] / len(matching_tracts)
				map_tract_population[matching_tract] = map_tract_population[csv_tract] / len(matching_tracts)
			map_tract_population.pop(csv_tract, None)
			map_tract_children.pop(csv_tract, None)
			for matching_tract in matching_tracts:
				unmatched_geojson_tracts.remove(matching_tract)
			print "Mapped csv tract " + csv_tract + " to geojson tracts " + str(matching_tracts)
	else:
		print "------------------------------------------"
		print "Tracts in csv match those in geojson."
	
	print "------------------------------------------"
	print "Tracts in geojson unmatched with those in csv:"
	print unmatched_geojson_tracts

	# Generate points in geoms
	print "------------------------------------------"
	# Limit number of dots we create to ~10k
	total_children = sum([map_tract_children[tract] for tract in map_tract_children.keys()])
	scaling_factor = total_children / 10000
	scaling_factor = 1
	points_map = {}
	for tract in map_tract_children.keys():
		children_in_tract = map_tract_children[tract]
		population_in_tract = map_tract_population[tract]
		geom = map_geo_tract_geom[tract]
		points_list = []
		if (children_in_tract == 0 and population_in_tract == 0):
			density = 0
		else:
			density = int((children_in_tract * 100) / population_in_tract)
		bbox = get_bbox( geom )
		ll,bb,rr,tt = bbox
		# generate a sample within the geometry for every child
		for i in range(children_in_tract / scaling_factor):
			while True:
				samplepoint = make_ogr_point( uniform(ll,rr), uniform(bb,tt) )
				if geom.Intersects( samplepoint ):
					break
			point = {}
			point["lat"] = samplepoint.GetY()
			point["lng"] = samplepoint.GetX()
			point["tract"] = tract
			point["density"] = density
			points_list.append(point)
		points_map[tract] = points_list
	return points_map

# Maps geojson keys into arrays containing csv_keys.  Each csv_key should be mapped to exactly once.
def create_map_data_sum(csv_path, key_column, sum_columns, restrict_columns, restrict_values):
	print "Processing %s"%csv_path
	map_sum_data = {}
	sum_column_indices = []
	restrict_column_indices = []
	
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
					if data in restrict_columns:
						restrict_column_indices.append(i)
			else:
				# Sum the number of children in this row.
				restrict = [row[i] in restrict_values for i in restrict_column_indices]
				if (False not in restrict):
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

def create_map_data(city_name, input_csv, csv_children_columns, csv_population_columns, csv_tract_column, csv_restrict_columns, csv_restrict_values, input_geojson, geo_tract_field, output_json):
	# Read inputs
	print "------------------------------------------"
	print "Making map of tracts to children."
	map_tract_children = create_map_data_sum(input_csv, csv_tract_column, csv_children_columns, csv_restrict_columns, csv_restrict_values)
	total_children = sum([map_tract_children[tract] for tract in map_tract_children.keys()])
	print "Found " + str(total_children) + " children in " + str(len(map_tract_children.keys())) + " tracts in " + city_name
	print "------------------------------------------"
	print "Making map of tracts to population."
	map_tract_population = create_map_data_sum(input_csv, csv_tract_column, csv_population_columns, csv_restrict_columns, csv_restrict_values)
	total_population = sum([map_tract_population[tract] for tract in map_tract_population.keys()])
	print "Found " + str(total_population) + " people in " + str(len(map_tract_children.keys())) + " tracts in " + city_name
	
	print "------------------------------------------"
	print "Creating points."
	map_tract_points = create_map_tract_points(input_geojson, geo_tract_field, map_tract_children, map_tract_population)
	total_points = sum([len(map_tract_points[tract]) for tract in map_tract_points.keys()])
	print "Generated " + str(total_points) + " total points in " + str(len(map_tract_points.keys())) + " tracts in " + city_name

	data = {}
	city_data ={}
	city_data["name"] = city_name
	city_data["children"] = total_children
	city_data["population"] = total_population
	data["city"] = city_data
	for tract in map_tract_points.keys():
		tract_data = {}
		tract_data["population"] = map_tract_population[tract]
		tract_data["children"] = map_tract_children[tract]
		tract_data["name"] = tract
		data[tract] = tract_data
	points_dict = {}
	points_dict["points"] = map_tract_points
	points_dict["data"] = data
	points_dict["tracts"] = map_tract_points.keys()
	# Write to file
	print "Finished processing %s"%output_json
	with open(output_json, 'w') as f:
	  json.dump(points_dict, f, ensure_ascii=False)
