import os, json
dir='D:/projetsIA/pokeIA/battlelog/battle-gen7randombattle-851038814'
filelist=[x for x in os.listdir(dir) if x.endswith('.json')]
data=[]
for filename in filelist:
    with open(os.path.join(dir, filename)) as json_file:
        data.append(json.load(json_file))