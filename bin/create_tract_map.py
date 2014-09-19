import os
import io
import re
import sys
import json
import ogr

def create_tract_map(input_map_path, tracts, state_field_name, state, tract_field_name, output_map_path):
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
		print defn.GetName()
		if defn.GetName() == tract_field_name:
			tract_field_index = i
		if defn.GetName() == state_field_name:
			state_field_index = i

	geojson_feats = [feat for feat in lyr]
	feature_collection = {"type": "FeatureCollection",
	                      "features": []
 											  }

	for feat in geojson_feats:
		feat_state = feat.GetField(state_field_index)
		tract = feat.GetField(tract_field_index)
		print tract
		if state == feat_state and tract in tracts:
			feature_collection["features"].append(feat.ExportToJson())
	with open(output_map_path, 'w') as f:
		json.dump(feature_collection, f, ensure_ascii=True)
