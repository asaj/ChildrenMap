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
	if ll == float("inf") or bb == float("inf") or rr == float("-inf") or tt == float("-inf"):
		print "Can't find bounding box!"
		
	return (ll,bb,rr,tt)
			
def create_points(args_dict, map_tract_children, map_tract_population):
	# Read inputs
	geojson_path = args_dict["input_geojson"]
	geo_tract_name = args_dict["geo_tract_name"]
	geo_gisjoin_name = args_dict["geo_gisjoin_name"]
	cambridge_tracts = args_dict["cambridge_tracts"]
	print "------------------------------------------"
	print "Making map of tracts to geoms."
	print "Processing: %s - Ctrl-Z to cancel"%geojson_path

	# open the geojson file
	ds = ogr.Open( geojson_path )
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

	# Map tracts to geoms
	num_geoms = 0
	map_tract_geom = {}
	for feat in geojson_feats:
		tract = feat.GetField(geo_tract_field)
		if tract not in cambridge_tracts:
			continue
		# Get geometry
		geom = feat.GetGeometryRef()
		if geom is None:
			continue
		num_geoms += 1
		if tract not in map_tract_geom.keys():
			map_tract_geom[tract] = [geom]
		else:
			map_tract_geom[tract].append(geom) 
	print "Mapped " +  str(len(map_tract_geom.keys())) + " tracts to " + str(num_geoms) + " geoms."

	in_csv_but_not_geojson = [tract for tract in map_tract_children.keys() if tract not in map_tract_geom.keys()]   
	in_geojson_but_not_csv = [tract for tract in map_tract_geom.keys() if tract not in map_tract_children.keys()]   
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
			matching_tracts = [geo_tract for geo_tract in in_geojson_but_not_csv if csv_tract[:-1] in geo_tract]
			print "Mapped csv tract " + csv_tract + " to geojson tracts " + str(matching_tracts)
			for matching_tract in matching_tracts:
				map_tract_children[matching_tract] = map_tract_children[csv_tract] / len(matching_tracts)
				map_tract_population[matching_tract] = map_tract_population[csv_tract] / len(matching_tracts)
			map_tract_children[csv_tract] = 0
			map_tract_population[csv_tract] = 0
	else:
		print "------------------------------------------"
		print "Tracts in csv match those in geojson."

	# Get area of each tract 
	print "------------------------------------------"
	print "Mapping tracts to area."
	map_tract_area = {}
	for tract in map_tract_geom.keys():
		total_area = 0
		for geom in map_tract_geom[tract]:
			bbox = get_bbox( geom )
			ll,bb,rr,tt = bbox
			total_area += abs((tt - bb) * (rr - ll))
		map_tract_area[tract] = total_area

	# Generate points in geoms
	print "------------------------------------------"
	points_map = {}
	for tract in map_tract_geom.keys():
		points_list = []
		children_in_tract = map_tract_children[tract]
		population_in_tract = map_tract_population[tract]
		density = int((children_in_tract * 100) / population_in_tract)
		total_points = 0
		for geom in map_tract_geom[tract]:
			bbox = get_bbox( geom )
			ll,bb,rr,tt = bbox
			geom_area = abs((tt - bb) * (rr - ll))
			children_in_geom = int((geom_area * children_in_tract) / map_tract_area[tract])
			# generate a sample within the geometry for every children
			for i in range(children_in_geom):
				while True:
					samplepoint = make_ogr_point( uniform(ll,rr), uniform(bb,tt) )
					if geom.Intersects( samplepoint ):
						break
				total_points += 1
				point_dict = {}
				point_dict["lat"] = samplepoint.GetY()
				point_dict["lng"] = samplepoint.GetX()
				point_dict["tract"] = tract
				point_dict["density"] = density
				points_list.append(point_dict)
		points_map[tract] = points_list
	return points_map
