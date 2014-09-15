import json
cambridge_tracts = [str(i) for i in range(352100, 355100)] 
for i in range(3521, 3551):
	cambridge_tracts.append(str(i))
with open("../static/data/census/cambridge_tracts.json", 'w') as f:
  json.dump(cambridge_tracts, f, ensure_ascii=False)
