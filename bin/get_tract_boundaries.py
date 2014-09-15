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
			
def get_tract_boundaries(geojson_path, cambridge_tracts_path, geo_gisjoin_name, geo_tract_name):
	# Read inputs
	with open(cambridge_tracts_path) as json_file:
		cambridge_tracts = json.load(json_file)

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
	keep_feats = []
	for feat in geojson_feats:
		tract = feat.GetField(geo_tract_field)
		if tract not in cambridge_tracts:
			continue
		keep_feats.append(feat)
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

	# Generate points in geoms
	'''
	map_tract_points = {}
	for tract in map_tract_geom.keys():
		tract_points = []
		for geom in map_tract_geom[tract]:
			bbox = get_bbox( geom )
			ll,bb,rr,tt = bbox
			x_width = int((tt * 3000) - (bb * 3000))
			y_height = int((rr * 3000) - (ll * 3000))
			for x in range (x_width):
				for y in range (y_height):
					samplepoint = make_ogr_point(ll + (float(y) / 3000.0), bb + (float(x) / 3000.0))
					if geom.Intersects(samplepoint): 
						point_dict = {}
						point_dict["lat"] = samplepoint.GetY()
						point_dict["lng"] = samplepoint.GetX()
						point_dict["tract"] = tract
						point_dict["density"] = .5
						tract_points.append(point_dict)
		map_tract_points[tract] = tract_points
		print "Found " + str(len(tract_points)) + " boundary points for tract " + tract
		'''
	return map_tract_points

geojson_path = "../static/data/maps/MA_blocks.geojson"
cambridge_tracts_path = "../static/data/census/cambridge_tracts.json"
geo_gisjoin_name = "GISJOIN"
geo_tract_name = "TRACTCE10"

get_tract_boundaries(geojson_path, cambridge_tracts_path, geo_gisjoin_name, geo_tract_name)
