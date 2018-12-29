import os
from smogon import Smogon

data_dir="D:/projetsIA/Pokai/pkmn_data"

data=Smogon(browser='chrome', driver_dir="D:/projetsIA/Pokai/driver/chromedriver.exe")

if not os.path.exists(data_dir):
    os.makedirs(data_dir)

[os.remove(os.path.join(data_dir,x)) for x in os.listdir(data_dir)]

#data.get_all_moves(data_dir)
#data.get_all_items(data_dir)
data.get_all_abilities(data_dir)

data.driver.close()