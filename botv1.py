from showdown import ShowdownBot
from multiprocessing import Process

teamtxt_path="D:/projetsIA/pokeIA/team_backup/pkmn_team_test.txt"

bot=ShowdownBot("iamabot447","projectia21",browser='chrome', driver_dir="D:/projetsIA/pokeIA/driver/chromedriver.exe")
bot.start_driver()
bot.login()
bot.turn_off_sound()
bot.import_teams(teamtxt_path)
id=bot.start_challenge_battle("canbusload",100,"gen7ou")
#id=bot.accept_challenge_battle("canbusload",100)
#id=bot.start_ladder_battle("gen7ou")

bot.play_battle(id,True)




