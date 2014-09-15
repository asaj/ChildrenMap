import makedots as md
print "Creating points for 2010"
args_dict = {}
args_dict["input_geojson"] = "../static/data/maps/MA_blocks.geojson"
args_dict["geo_feat_name"] = "GISJOIN"
args_dict["input_csv"] = "../static/data/census/age/age2010.csv"
args_dict["csv_key_column"] = "TRACTA"
args_dict["csv_sum_columns"] =  ["H76003", "H76004", "H76005", "H76006", "H76027", "H76028", "H76029", "H76030"]
args_dict["csv_denominator_columns"] =  ["H76001"]
args_dict["csv_restrict_column"] = "TRACTA"
args_dict["csv_restrict_values_file"] = "../static/data/census/cambridge_tracts.json"
args_dict["bbox_file"] = "../static/data/maps/tracts_to_bbox.json"
args_dict["output_json"] = "../static/data/age/age2010boundary.json"
md.main(args_dict)

"""
print "Creating points for 2000"
args_dict = {}
args_dict["input_geojson"] = "../static/data/maps/MA_blocks.geojson"
args_dict["geo_feat_name"] = "GISJOIN"
args_dict["input_csv"] = "../static/data/census/age/age2000.csv"
args_dict["csv_key_column"] = "TRACTA"
args_dict["csv_sum_columns"] =  ["FYM001", "FYM002", "FYM003", "FYM004", "FYM024", "FYM025", "FYM026", "FYM027"]
args_dict["csv_denominator_columns"] =  ["FYM001","FYM002","FYM003","FYM004","FYM005","FYM006","FYM007","FYM008","FYM009","FYM010","FYM011","FYM012","FYM013","FYM014","FYM015","FYM016","FYM017","FYM018","FYM019","FYM020","FYM021","FYM022","FYM023","FYM024","FYM025","FYM026","FYM027","FYM028","FYM029","FYM030","FYM031","FYM032","FYM033","FYM034","FYM035","FYM036","FYM037","FYM038","FYM039","FYM040","FYM041","FYM042","FYM043","FYM044","FYM045","FYM046"]
args_dict["csv_restrict_column"] = "TRACTA"
args_dict["bbox_file"] = "../static/data/maps/tracts_to_bbox.json"
args_dict["csv_restrict_values_file"] = "../static/data/census/cambridge_tracts.json"
args_dict["output_json"] = "../static/data/age/age2000.json"
md.main(args_dict)

print "Creating points for 1990"
args_dict = {}
args_dict["input_geojson"] = "../static/data/maps/MA_blocks.geojson"
args_dict["geo_feat_name"] = "GISJOIN"
args_dict["input_csv"] = "../static/data/census/age/age1990.csv"
args_dict["csv_key_column"] = "TRACTA"
args_dict["csv_sum_columns"] =  ["ET3001","ET3002","ET3003","ET3004","ET3005","ET3006","ET3007","ET3008","ET3009","ET3010","ET3011","ET3012"]
args_dict["bbox_file"] = "../static/data/maps/tracts_to_bbox.json"
args_dict["csv_denominator_columns"] =  ["ET3001","ET3002","ET3003","ET3004","ET3005","ET3006","ET3007","ET3008","ET3009","ET3010","ET3011","ET3012","ET3013","ET3014","ET3015","ET3016","ET3017","ET3018","ET3019","ET3020","ET3021","ET3022","ET3023","ET3024","ET3025","ET3026","ET3027","ET3028","ET3029","ET3030","ET3031"]
args_dict["csv_restrict_column"] = "TRACTA"
args_dict["csv_restrict_values_file"] = "../static/data/census/cambridge_tracts.json"
args_dict["output_json"] = "../static/data/age/age1990.json"
md.main(args_dict)


print "Creating points for 1980"
args_dict = {}
args_dict["input_geojson"] = "../static/data/maps/MA_blocks.geojson"
args_dict["geo_feat_name"] = "GISJOIN"
args_dict["input_csv"] = "../static/data/census/age/age1980.csv"
args_dict["csv_key_column"] = "TRACTA"
args_dict["csv_sum_columns"] =  ["C67001","C67002","C67003","C67004","C67005","C67006","C67007","C67008","C67009","C67010","C67011"]
args_dict["csv_denominator_columns"] =  ["C67001","C67002","C67003","C67004","C67005","C67006","C67007","C67008","C67009","C67010","C67011","C67012","C67013","C67014","C67015","C67016","C67017","C67018","C67019","C67020","C67021","C67022","C67023","C67024","C67025","C67026"]
args_dict["bbox_file"] = "../static/data/maps/tracts_to_bbox.json"
args_dict["csv_restrict_column"] = "TRACTA"
args_dict["csv_restrict_values_file"] = "../static/data/census/cambridge_tracts.json"
args_dict["output_json"] = "../static/data/age/age1980.json"
md.main(args_dict)

print "Creating points for 1970"
args_dict = {}
args_dict["input_geojson"] = "../static/data/maps/MA_blocks.geojson"
args_dict["geo_feat_name"] = "GISJOIN"
args_dict["input_csv"] = "../static/data/census/age/age1970.csv"
args_dict["bbox_file"] = "../static/data/maps/tracts_to_bbox.json"
args_dict["csv_key_column"] = "TRACTA"
args_dict["csv_sum_columns"] =  ["CM7001","CM7002","CM7003","CM7004","CM7005","CM7006","CM7007","CM7008","CM7009","CM7022","CM7023","CM7024","CM7025","CM7026","CM7027","CM7028","CM7029","CM7030"]
args_dict["csv_denominator_columns"] =  ["CM7001","CM7002","CM7003","CM7004","CM7005","CM7006","CM7007","CM7008","CM7009","CM7010","CM7011","CM7012","CM7013","CM7014","CM7015","CM7016","CM7017","CM7018","CM7019","CM7020","CM7021","CM7022","CM7023","CM7024","CM7025","CM7026","CM7027","CM7028","CM7029","CM7030","CM7031","CM7032","CM7033","CM7034","CM7035","CM7036","CM7037","CM7038","CM7039","CM7040","CM7041","CM7042"]
args_dict["csv_restrict_column"] = "TRACTA"
args_dict["csv_restrict_values_file"] = "../static/data/census/cambridge_tracts.json"
args_dict["output_json"] = "../static/data/age/age1970.json"
md.main(args_dict)
"""
