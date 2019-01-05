import os
from smogon import Smogon

data_dir="D:/projetsIA/pokeIA/pkmn_data"

data=Smogon(browser='chrome', driver_dir="D:/projetsIA/pokeIA/driver/chromedriver.exe")

if not os.path.exists(data_dir):
    os.makedirs(data_dir)


data.get_all_abilities(data_dir)
data.get_all_items(data_dir)
data.get_all_moves(data_dir)
data.get_all_pkmns(data_dir)

data.driver.close()