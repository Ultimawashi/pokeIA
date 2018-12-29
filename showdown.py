import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from exceptions import *

class Showdown():
    BASE_URL="https://play.pokemonshowdown.com"
    def __init__(self, url=BASE_URL, timer_on=False, browser='chrome', driver_dir="D:/projetsIA/Pokai/driver/chromedriver.exe"):
        self.url = url
        self.timer_on = timer_on
        self.browser = browser
        assert self.browser in ["firefox",
                                "chrome"], "please choose a valid browser (only chrome or firefox are supported)"
        if browser == "firefox":
            self.driver = webdriver.Firefox(executable_path=driver_dir)
        elif browser == "chrome":
            self.driver = webdriver.Chrome(executable_path=driver_dir)
        self.state = None
        self.poke_map = {
            0:0,1:1,2:2,3:3,4:4,5:5
        }

    def start_driver(self):
        self.driver.get(self.url)

    def get_state(self):
        url = self.driver.current_url
        if "battle" in url:
            return "battle"
        else:
            return "lobby"

    def wait_home_page(self):
        while self.driver.find_element_by_css_selector(".select.formatselect").get_attribute('value') != "gen7randombattle":
            time.sleep(1)

    def login(self, username, password):
        self.wait_home_page()
        time.sleep(1)
        elem = self.driver.find_element_by_name("login")
        elem.click()
        time.sleep(1)
        user = self.driver.find_element_by_name("username")
        user.send_keys(username)
        user.send_keys(Keys.RETURN)
        while not self.check_exists_by_name("password"):
            time.sleep(1)
        passwd = self.driver.find_element_by_name("password")
        passwd.send_keys(password)
        passwd.send_keys(Keys.RETURN)
        time.sleep(1)

    def choose_tier(self, tier='gen7ou'):
        try:
            while not self.check_exists_by_css_selector(".select.formatselect"):
                time.sleep(1)
            form = self.driver.find_element_by_css_selector(".select.formatselect")
            form.click()
            time.sleep(2)
            #self.driver.save_screenshot('ou.png')
            tier = self.driver.find_element_by_css_selector("[name='selectFormat'][value='%s']" % tier)
            tier.click()
        except:
            raise TierException()


    def start_ladder_battle(self):
        url1 = self.driver.current_url
        battle = self.driver.find_element_by_css_selector(".button.big")
        battle.click()
        battle_click = True
        time.sleep(1)
        if url1 == self.driver.current_url and self.check_exists_by_name("username"):
            ps_overlay = self.driver.find_element_by_xpath("/html/body/div[4]")
            ps_overlay.click()
            battle_click = False
        while url1 == self.driver.current_url and self.check_exists_by_name("login"):
            time.sleep(1)
        if url1 == self.driver.current_url and not battle_click:
            battle = self.driver.find_element_by_css_selector(".button.big")
            battle.click()
            time.sleep(1)
        while url1 == self.driver.current_url:
            time.sleep(1.5)

    def start_challenge_battle(self, name, tier='ou'):
        lobby = self.driver.find_element_by_css_selector(".ilink[href='/lobby']")
        lobby.click()
        time.sleep(2)
        if self.check_exists_by_css_selector(".userbutton.username[data-name=' %s']" % name):
            name = self.driver.find_element_by_css_selector(".userbutton.username[data-name=' %s']" % name)
            name.click()
        else:
           raise UserNotOnlineException()
        time.sleep(2)
        challenge = self.driver.find_element_by_css_selector("[name='challenge']")
        challenge.click()
        time.sleep(2)
        pm_window = self.driver.find_element_by_css_selector(".pm-window")
        form = pm_window.find_element_by_css_selector(".select.formatselect")
        form.click()
        time.sleep(2)
        tier = self.driver.find_element_by_css_selector("[name='selectFormat'][value='%s']" % tier)
        tier.click()
        time.sleep(2)
        make_challenge = pm_window.find_element_by_css_selector("[name='makeChallenge']")
        make_challenge.click()
        lobby_quit = self.driver.find_element_by_css_selector(".closebutton[href='/lobby']")
        lobby_quit.click()

    def get_battle_id(self):
        url = self.driver.current_url
        url_list = url.split('-')
        id = url_list[-2:]
        return '-'.join(id)

    def make_team(self, team):
        builder = self.driver.find_element_by_css_selector(".button[value='teambuilder']")
        builder.click()
        #self.screenshot('log.png')
        new_team = self.driver.find_element_by_css_selector("[name='new']")
        new_team.click()
        #self.screenshot('log.png')
        time.sleep(3)
        import_button = self.driver.find_element_by_css_selector(".majorbutton[name='import']")
        import_button.click()
        #self.screenshot('log.png')
        textfield = self.driver.find_element_by_css_selector(".teamedit .textbox")
        textfield.send_keys(team)
        #self.screenshot('log.png')
        save = self.driver.find_element_by_css_selector(".savebutton[name='saveImport']")
        save.click()
        #self.screenshot('log.png')
        close_button = self.driver.find_element_by_css_selector(".closebutton[href='/teambuilder']")
        close_button.click()
        #self.screenshot('log.png')
        time.sleep(2)

    def clear_cookies(self):
        self.driver.execute_script("localStorage.clear();")

    def turn_off_sound(self):
        sound = self.driver.find_element_by_css_selector(".icon[name='openSounds']")
        sound.click()
        mute = self.driver.find_element_by_css_selector("[name='muted']")
        mute.click()

    def get_my_primary(self):
        img = self.driver.find_elements_by_css_selector(".battle img")[6]
        text = img.get_attribute('src')
        poke = text.split("/")[-1]
        poke = poke[:-4]
        return poke

    def get_opp_primary(self):
        img = self.driver.find_elements_by_css_selector(".battle img")[5]
        text = img.get_attribute('src')
        poke = text.split("/")[-1]
        poke = poke[:-4]
        return poke

    def move(self, index, backup_switch, mega=False, volt_turn=None):
        if self.check_alive():
            if mega:
                mega_button = self.driver.find_element_by_name('megaevo')
                mega_button.click()
            moves = self.driver.find_elements_by_css_selector(".movemenu button")
            move = moves[index]
            move.click()
            if volt_turn is not None:
                self.wait_for_move()
                self.volt_turn(volt_turn)
        self.wait_for_move()
        self.backup_switch(backup_switch)

    def switch_initial(self, index, backup_switch):
        i = self.poke_map[index]
        choose = self.driver.find_elements_by_name("chooseTeamPreview")[index]
        choose.click()
        old_primary = None
        for k, v in self.poke_map.items():
            if v == 0:
                old_primary = k

        self.poke_map[index] = 0
        self.poke_map[old_primary] = i
        self.wait_for_move()

    def switch(self, index, backup_switch, use_backup=True):
        if self.check_alive():
            i = self.poke_map[index]
            buttons = self.driver.find_elements_by_css_selector(".switchmenu button")
            buttons[i].click()
            old_primary = None
            for k, v in self.poke_map.items():
                if v == 0:
                    old_primary = k

            self.poke_map[index] = 0
            self.poke_map[old_primary] = i

        self.wait_for_move()
        if use_backup:
            self.backup_switch(backup_switch)

    def backup_switch(self, index):
        if not self.check_alive():
            i = self.poke_map[index]
            buttons = self.driver.find_elements_by_css_selector(".switchmenu button")
            buttons[i].click()
            old_primary = None
            for k, v in self.poke_map.items():
                if v == 0:
                    old_primary = k
            self.poke_map[index] = 0
            self.poke_map[old_primary] = i
            self.wait_for_move()

    def volt_turn(self, index):
        if not self.check_exists_by_name("chooseMove"):
            i = self.poke_map[index]
            buttons = self.driver.find_elements_by_css_selector(".switchmenu button")
            buttons[i].click()
            old_primary = None
            for k, v in self.poke_map.items():
                if v == 0:
                    old_primary = k
            self.poke_map[index] = 0
            self.poke_map[old_primary] = i
        self.wait_for_move()

    def check_alive(self):
        return self.check_exists_by_css_selector(".rstatbar")

    def chat(self, message):
        chatbox = self.driver.find_elements_by_css_selector(".chatbox .textbox")[-1]
        chatbox.send_keys(message)
        chatbox.send_keys(Keys.RETURN)

    def check_exists_by_xpath(self, xpath):
        try:
            self.driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        return True

    def check_exists_by_id(self, id):
        try:
            self.driver.find_element_by_id(id)
        except NoSuchElementException:
            return False
        return True

    def check_exists_by_name(self, name):
        try:
            self.driver.find_element_by_name(name)
        except NoSuchElementException:
            return False
        return True

    def check_exists_by_class(self, cls):
        try:
            self.driver.find_elements_by_class_name(cls)
        except NoSuchElementException:
            return False
        return True

    def check_exists_by_css_selector(self, css, elem=None):
        try:
            if elem:
                result = elem.find_elements_by_css_selector(css)
            else:
                result = self.driver.find_elements_by_css_selector(css)
            return len(result) > 0
        except NoSuchElementException:
            return False

    def start_timer(self):
        if self.check_exists_by_name("setTimer"):
            timer = self.driver.find_element_by_name("setTimer")
            if timer.text == "Start timer":
                timer.click()
            self.timer_on = True

    def get_log(self):
        log = self.driver.find_element_by_css_selector(".battle-log")
        return log.text.encode('utf-8')

    def wait_for_move(self):
        move_exists = self.check_exists_by_css_selector(".movemenu") or self.check_exists_by_css_selector(".switchmenu")
        while move_exists == False:
            #self.driver.save_screenshot('fat.png')
            try:
                self.start_timer()
            except:
                pass
            time.sleep(2)
            move_exists = self.check_exists_by_css_selector(".movemenu") or self.check_exists_by_css_selector(".switchmenu")
            if self.check_exists_by_css_selector("[name='saveReplay']"):
                self.chat("gg")
                save_replay = self.driver.find_element_by_css_selector("[name='saveReplay']")
                save_replay.click()
                while not self.check_exists_by_id(self.get_battle_id()):
                    time.sleep(1)
                ps_overlay = self.driver.find_element_by_css_selector(".ps-overlay")
                ps_overlay.click()
                raise GameOverException()


    def reset(self):
        self.poke_map = {
            0:0,1:1,2:2,3:3,4:4,5:5
        }
        self.driver.get(self.url)
        time.sleep(2)

    def close(self):
        self.driver.close()

    def get_my_primary_health(self):
        if self.check_exists_by_css_selector(".rstatbar .hpbar .hptext"):
            hp_text = self.driver.find_element_by_css_selector(".rstatbar .hpbar .hptext")
            hp = hp_text.text.strip("%")
            hp = int(hp)
        else:
            hp = 0
        return hp


    def get_opp_primary_health(self):
        if self.check_exists_by_css_selector(".lstatbar .hpbar .hptext"):
            hp_text = self.driver.find_element_by_css_selector(".lstatbar .hpbar .hptext")
            hp = hp_text.text.strip("%")
            hp = int(hp)
        else:
            hp = 0
        return hp

if __name__ == "__main__":
    pass
