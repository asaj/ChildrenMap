import create_points as create_points
import create_tract_map as create_tract_map

children_columns_1970_0 = ["CE600" + str(i) for i in range(10)]
children_columns_1970_1 = ["CE60" + str(i) for i in range(10, 19)]
children_columns_1970_2 = ["CE610" + str(i) for i in range(2, 10)]
children_columns_1970_3 = ["CE61" + str(i) for i in range(10, 20)]
children_columns_1970 = children_columns_1970_0 + children_columns_1970_1 + children_columns_1970_2 + children_columns_1970_3
population_columns_1970_0 = ["CE60" + str(i) for i in range(10, 100)]
population_columns_1970_1 = ["CE6" + str(i) for i in range(100, 203)] 
population_columns_1970 = population_columns_1970_0 + population_columns_1970_1

children_columns_1980_0 = ["C6700" + str(i) for i in range(10)]
children_columns_1980 = children_columns_1980_0 + ["C67010", "C67011"]
population_columns_1980 = ["C670" + str(i) for i in range(10, 27)] + children_columns_1980_0

children_columns_1990_0 = ["ET300" + str(i) for i in range(10)]
children_columns_1990 = children_columns_1990_0 + ["ET3010", "ET3011", "ET3012"]
population_columns_1990 = ["ET30" + str(i) for i in range(10, 32)] + children_columns_1990_0

children_columns_2000_0 = ["FMZ00" + str(i) for i in range(5)]
children_columns_2000_1 = ["FMZ02" + str(i) for i in range(4, 8)]
children_columns_2000 = children_columns_2000_0 + children_columns_2000_1
population_columns_2000_0 = ["FMZ00" + str(i) for i in range(10)]
population_columns_2000_1 = ["FMZ0" + str(i) for i in range(10, 47)]
population_columns_2000 = population_columns_2000_0 + population_columns_2000_1

children_columns_2010_0 = ["H7600" + str(i) for i in range(3, 7)]
children_columns_2010_1 = ["H760" + str(i) for i in range(27, 31)] 
children_columns_2010 = children_columns_2010_0 + children_columns_2010_1
population_columns_2010 = ["H76001"]

children_columns = {"2010":children_columns_2010, "2000":children_columns_2000,
										"1990":children_columns_1990, "1980":children_columns_1980,
										"1970":children_columns_1970}

population_columns = {"2010":population_columns_2010, "2000":population_columns_2000,
											"1990":population_columns_1990, "1980":population_columns_1980,
											"1970":population_columns_1970}

"""
city = "SF"
csv_restrict_columns = "COUNTY"
csv_restrict_values = ["San Francisco", "San Francisco County"]
"""
city = "CAMBRIDGE"
csv_restrict_columns = ["COUNTY", "TRACTA"]
csv_restrict_values = [str(i) for i in range(352100, 355100)]
for i in range(3521, 3551):
	csv_restrict_values.append(str(i))
csv_restrict_values.append("Middlesex County")
csv_restrict_values.append("Middlesex")
csv_tract_column = "TRACTA"
years = ["2010", "2000", "1990", "1980", "1970"]
input_csvs = ["../static/data/census/age_" + year + "_tract.csv" for year in years]
output_json = ["../static/data/points/" + city + "_children_data_" + year + ".json" for year in years]

input_geojson = "../static/data/maps/US_tract_2010.geojson"
city_geojson = "../static/data/maps/" + city + "_tract_2010.geojson"
geo_state_field = "STATEFP10"
geo_state_value = "06"
geo_tract_field = "TRACTCE10"
##create_tract_map.create_tract_map(input_geojson, csv_tract_values, geo_state_field, geo_state_value, geo_tract_field, city_geojson)

for i in range (len(years)):
	print "Creating data for year " + years[i]
	create_points.create_map_data(city, input_csvs[i], children_columns[years[i]], population_columns[years[i]], csv_tract_column, csv_restrict_columns, csv_restrict_values, city_geojson, geo_tract_field, output_json[i]) 
	print "------------------------------------------\n\n"
	print "------------------------------------------"

