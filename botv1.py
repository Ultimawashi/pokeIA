from showdown import Showdown

bot=Showdown(browser='chrome', driver_dir="D:/projetsIA/pokeIA/driver/chromedriver.exe")
bot.start_driver()
bot.login("iamabot447","projectia21")
bot.choose_tier('gen7randombattle')
bot.start_ladder_battle()
