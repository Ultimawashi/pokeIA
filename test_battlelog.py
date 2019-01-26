import os, json
dir='D:/projetsIA/pokeIA/battlelog/iamabot447/battle-gen7ou-854201636'
filelist= [x for x in os.listdir(dir) if x.endswith('.json')]
filelist=sorted(filelist, key=lambda a: int(a.split("_")[1].split('.')[0]))
data=[]
for filename in filelist:
    with open(os.path.join(dir, filename)) as json_file:
        data.append(json.load(json_file))