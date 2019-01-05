import time
import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from exceptions import *

BASE_URL="https://play.pokemonshowdown.com"
default_home_value="gen7randombattle"
tier_list_order=['LC','Untiered','PU','PUBL','NU','NUBL','RU','RUBL','UU','UUBL','OU','Uber','AG']
supported_format_eq = {
    'randombattle':'Uber',
    'unratedrandombattle':'Uber',
    'uber':'Uber',
    'ou':'OU',
    'uu':'UU',
    'ru':'RU',
    'nu':'NU',
    'pu':'PU',
    'lc':'LC'
}

def isincluded_tier(tier_list_order,tier):
    index=tier_list_order.index(tier)
    return [x for i,x in enumerate(tier_list_order) if i <=index]

def found_str_by_regex(string,regex):
    try:
        found = re.search(regex, string).group(0)
    except AttributeError:
        found = ""
    return found

class check_if_connected(object):

  def __init__(self,username):
    self.username = username

  def __call__(self, driver):
    user = driver.find_element(*(By.CLASS_NAME, "username"))   # Finding the referenced element
    if self.username in user.get_attribute('innerHTML'):
        return True
    else:
        return False

class check_homepage_loaded(object):

    def __init__(self):
        pass

    def __call__(self, driver):
        if driver.find_element_by_css_selector(".select.formatselect").get_attribute('value') == default_home_value:
            return True
        else:
            return False

class check_password_needed(object):

    def __init__(self, username):
        self.username = username

    def __call__(self, driver):
        if len(driver.find_elements(*(By.CLASS_NAME, "username"))) > 0:
            user = driver.find_element(*(By.CLASS_NAME, "username"))
            if self.username in user.get_attribute('innerHTML'):
                return True
            return False
        elif len(driver.find_elements(*(By.NAME, "password"))) > 0:
            return driver.find_element(*(By.NAME, "password"))
        else:
            return False

class check_if_battle_started(object):

    def __init__(self):
        pass

    def __call__(self, driver):
        button=driver.find_element_by_css_selector(".button.big")
        if 'disabled' not in button.get_attribute("class"):
            return True
        else:
            return False

class get_battle_launcher(object):

    def __init__(self):
        pass

    def __call__(self, driver):



class ShowdownBot():

    def __init__(self,username,password, url=BASE_URL, timer_on=False, time=100, browser='chrome', driver_dir="D:/projetsIA/pokeIA/driver/chromedriver.exe"):
        self.url = url
        self.timer_on = timer_on
        self.browser = browser
        assert self.browser in ["firefox",
                                "chrome"], "please choose a valid browser (only chrome or firefox are supported)"
        if browser == "firefox":
            self.driver = webdriver.Firefox(executable_path=driver_dir)
        elif browser == "chrome":
            self.driver = webdriver.Chrome(executable_path=driver_dir)
        self.wait = WebDriverWait(self.driver, time)
        self.username=username
        self.password=password
        self.gen = None
        self.format = None
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
        try:
            self.wait.until(
                check_homepage_loaded()
            )
        except TimeoutException as e:
            raise e

    def wait_logged(self):
        try:
            self.wait.until(
            check_if_connected(self.username)
            )
        except TimeoutException as e:
            raise e

    def wait_battle_start(self):
        try:
            self.wait.until(
                check_if_battle_started()
            )
        except TimeoutException as e:
            raise e

    def login(self):
        self.wait_home_page()
        elem = self.wait.until(
            EC.presence_of_element_located((By.NAME, "login"))
        )
        elem.click()
        user = self.wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        user.send_keys(self.username)
        user.send_keys(Keys.RETURN)
        passwd = self.wait.until(
            check_password_needed(self.username)
            )
        if not isinstance(passwd,bool):
            passwd.send_keys(self.password)
            passwd.send_keys(Keys.RETURN)
        self.wait_logged(self.username)

    def choose_tier(self, tier='gen7ou'):
        try:
            form = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".select.formatselect"))
            )
            form.click()
            tier = self.driver.find_element_by_css_selector("[name='selectFormat'][value='%s']" % tier)
            format_string=tier.get_attribute("value")
            self.gen=found_str_by_regex(format_string,'gen[0-9]')
            self.format=format_string.replace(self.gen,'')
            tier.click()
        except:
            raise TierException()


    def start_ladder_battle(self):
        url1 = self.driver.current_url
        battle = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".button.big"))
        )
        battle.click()
        self.wait_battle_start()

        if url1 == self.driver.current_url and self.check_exists_by_name("username"):
            ps_overlay = self.driver.find_element_by_xpath("/html/body/div[4]")
            ps_overlay.click()
            battle_click = False
        if url1 == self.driver.current_url and not battle_click:
            battle = self.driver.find_element_by_css_selector(".button.big")
            battle.click()


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
        new_team = self.driver.find_element_by_css_selector("[name='new']")
        new_team.click()
        time.sleep(3)
        import_button = self.driver.find_element_by_css_selector(".majorbutton[name='import']")
        import_button.click()
        textfield = self.driver.find_element_by_css_selector(".teamedit .textbox")
        textfield.send_keys(team)
        save = self.driver.find_element_by_css_selector(".savebutton[name='saveImport']")
        save.click()
        close_button = self.driver.find_element_by_css_selector(".closebutton[href='/teambuilder']")
        close_button.click()
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
