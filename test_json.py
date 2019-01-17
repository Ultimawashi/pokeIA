import os, json
dir='D:/projetsIA/pokeIA/pkmn_data'
with open(os.path.join(dir, 'pkmns.json')) as json_file:
    dataSet=json.load(json_file)