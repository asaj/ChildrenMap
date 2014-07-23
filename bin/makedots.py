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
			
def get_children_count(input_filename, block_group_header, children_headers, geo_restriction_feature_name, geo_restriction_features):
	print "Processing %s"%input_filename
	map_block_group_children = {}
	children_columns = []
	
	with open(input_filename, 'rb') as csvfile:
		census_reader = csv.reader(csvfile, delimiter='\t', quotechar='|')
		first_row = True
		for row in census_reader:
			# Find index of interesting columns.
			if first_row:
				first_row = False
				for i, data in enumerate(row):
					if data in children_headers:
						children_columns.append(i)
					if data == block_group_header:
						block_group_column = i
					if data == geo_restriction_feature_name:
						geo_restriction_column = i
			else:
				# Sum the number of children in this row.
				block_children = 0
				for i, data in enumerate(row):
					if i == block_group_column:
						block_group = data
					if i in children_columns:
						block_children += int(data)
					if i == geo_restriction_column:
						geo_restriction_feat = data
				# Only add to the map areas we are interested in.
				if (int(geo_restriction_feat) in geo_restriction_features):
					map_block_group_children[block_group] = block_children
	return map_block_group_children
	
def main(args_dict):
	# Read inputs
	input_geojson = args_dict["input_geojson"]
	geo_feat_name = args_dict["geo_feat_name"]
	output_filename = args_dict["output_file"]
	input_csv = args_dict["input_csv"] 
	csv_feat = args_dict["csv_geo_feat_name"]
	csv_columns = args_dict["children_columns"]
	csv_geo_restrict_feat_name = args_dict["csv_geo_restrict_feat_name"]
	csv_geo_restrict_feats_file = args_dict["csv_geo_restrict_feats_file"]
	with open(csv_geo_restrict_feats_file) as json_file:
		csv_geo_restrict_feats = json.load(json_file)
	# Get a map of geographical features to number of children.
	map_geo_feat_children = get_children_count(input_csv, csv_feat, csv_columns, csv_geo_restrict_feat_name, csv_geo_restrict_feats) 

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
			print "Found field for " + geo_feat_name
			geo_field = i

	# set up the output file
	# if it already exists, delete it
	if os.path.isfile(output_filename):
		os.system("rm %s"%output_filename)
	
	n_features = len(lyr)

	points_dict = {}
	points_list = []
	total_children = 0
	for j, feat in enumerate( lyr ):
		# Progress indicator
		if j%1000==0:
			#conn.commit()
			if j%10000==0:
				print " %s/%s (%0.2f%%)"%(j+1,n_features,100*((j+1)/float(n_features)))
			else:
				sys.stdout.write(".")
				sys.stdout.flush()

		# Get population
		geo_feat = feat.GetField(geo_field)
		if (geo_feat_name == "GISJOIN"):
			# GISJOIN field in CSV has one more character than the GISJOIN field in geojson
			geo_feats = [geo_feat + str(i) for i in range(0, 10)]	
			pop = 0
			for gf in geo_feats:
				if (gf in map_geo_feat_children.keys()):
					pop += map_geo_feat_children[gf]
					print str(map_geo_feat_children[gf]) + " children in GISJOIN " + gf
		#geo_feat = re.sub('^0+', '', geo_feat)
		#if (geo_feat in map_geo_feat_children.keys()):
		#	pop = map_geo_feat_children[geo_feat] 
		else:
			continue
		total_children += pop

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
	print "Finished processing %s"%output_filename
	print "Found " + str(total_children) + " households with children."
	points_dict["points"] = points_list
	with open(output_filename, 'w') as f:
	  json.dump(points_dict, f, ensure_ascii=False)

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
#cambridge_tracts = [i for i in range(352100, 355100)] 
#with open("../static/data/census/cambridge_tracts.json", 'w') as f:
#  json.dump(cambridge_tracts, f, ensure_ascii=False)

