import csv
import json

csvfile = open('zip_codes_states.csv', 'r')
jsonfile = open('zip_codes_states.json', 'w')

field_names = ('zip_code', 'latitude', 'longitude', 'city', 'state', 'county')
reader = csv.DictReader(csvfile, field_names)
rows = {}
for row in reader:
    rows[row['zip_code']] = row

json.dump(rows, jsonfile)
