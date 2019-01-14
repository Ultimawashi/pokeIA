import time
import re
import random
from selenium import webdriver
from lxml import html
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from exceptions import *


# Global variables
BASE_URL="https://play.pokemonshowdown.com"
default_home_value="gen7randombattle"
tier_list_order=['LC','Untiered','PU','PUBL','NU','NUBL','RU','RUBL','UU','UUBL','OU','Uber','AG','Limbo']
supported_format_eq = {
    'anythinggoes':'AG',
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
num_gen=7
num_pkmn_team=6
possible_on_move_selection_action={
    'gen7':['Zmove', 'Mega'],
    'gen6':['Mega'],
    'gen5':[],
    'gen4':[],
    'gen3':[],
    'gen2':[],
    'gen1':[]
}
possible_on_switch_selection_action={
    'gen7':[],
    'gen6':[],
    'gen5':[],
    'gen4':[],
    'gen3':[],
    'gen2':[],
    'gen1':[]
}
possible_action_dict={
    'gen7':['Move1','Move2','Move3','Move4',
            'Switch1','Switch2','Switch3','Switch4','Switch5','Switch6'],
    'gen6':['Move1','Move2','Move3','Move4',
            'Switch1','Switch2','Switch3','Switch4','Switch5','Switch6'],
    'gen5':['Move1','Move2','Move3','Move4',
            'Switch1','Switch2','Switch3','Switch4','Switch5','Switch6'],
    'gen4':['Move1','Move2','Move3','Move4',
            'Switch1','Switch2','Switch3','Switch4','Switch5','Switch6'],
    'gen3':['Move1','Move2','Move3','Move4',
            'Switch1','Switch2','Switch3','Switch4','Switch5','Switch6'],
    'gen2':['Move1','Move2','Move3','Move4',
            'Switch1','Switch2','Switch3','Switch4','Switch5','Switch6'],
    'gen1':['Move1','Move2','Move3','Move4',
            'Switch1','Switch2','Switch3','Switch4','Switch5','Switch6']
}

# Utility functions

def isincluded_tier(tier_list_order,tier):
    index=tier_list_order.index(tier)
    return [x for i,x in enumerate(tier_list_order) if i <=index]

def found_str_by_regex(string,regex):
    try:
        found = re.search(regex, string).group(0)
    except AttributeError:
        found = ""
    return found

def build_action_dict(actiondict,on_move_actiondict,on_switch_actiondict):
    res=dict()
    for key in actiondict:

        move_action_list = []
        for action in on_move_actiondict[key]:
            move_action_list=move_action_list+[[action, move] for move in actiondict[key] if move.startswith('Move')]

        switch_action_list = []
        for action in on_switch_actiondict[key]:
            switch_action_list=switch_action_list+[[action, switch] for switch in actiondict[key] if switch.startswith('Switch')]

        res.update({key:move_action_list+switch_action_list+[[action] for action in actiondict[key]]})
    return res

def build_action_map(gen,actiondict):
    res=dict()
    return [res.update({i:action}) for i,action in enumerate(actiondict[gen])]

# Custom selenium wait class
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
        elif len(driver.find_elements(*(By.NAME, "password"))) > 0:
            return driver.find_element(*(By.NAME, "password"))
        else:
            return False

class check_if_ladder_battle_started(object):

    def __init__(self):
        pass

    def __call__(self, driver):
        button=driver.find_element_by_css_selector(".button.big")
        if 'disabled' not in button.get_attribute("class"):
            return True
        else:
            return False

class check_if_challenge_battle_started(object):

    def __init__(self):
        pass

    def __call__(self, driver):

        if len(driver.find_elements_by_class_name("challenge")) ==0:
            return True
        else:
            return False

class get_battle_launcher(object):

    def __init__(self):
        pass

    def __call__(self, driver):
        if len(driver.find_elements(*(By.NAME, "showSearchGroup"))) > 0:
            addbattle=driver.find_element(*(By.NAME, "showSearchGroup"))
            if addbattle.is_displayed() and addbattle.is_enabled():
                return addbattle
        elif len(driver.find_elements(*(By.CSS_SELECTOR, ".button.big"))) > 0:
            button = driver.find_element_by_css_selector(".button.big")
            if 'disabled' not in button.get_attribute("class"):
                return button
        else:
            return False

class tierwindows_select(object):

    def __init__(self,menu):
        self.menu=menu

    def __call__(self, driver):
        if len(self.menu.find_elements_by_css_selector(".select.formatselect")) > 0:
            return self.menu.find_element_by_css_selector(".select.formatselect")
        else:
            return False

class wait_to_see_state_of_user(object):

    def __init__(self):
        pass

    def __call__(self, driver):
        offline=len(driver.find_elements_by_class_name("offline"))
        online=len(driver.find_elements_by_class_name("rooms"))
        if offline > 0:
            return 2
        elif online > 0:
            return 1
        else:
            return False

# Class API for website pokemon showdown
class ShowdownBot():

    def __init__(self,username,password, url=BASE_URL, timeout=10, browser='chrome',
                 driver_dir="D:/projetsIA/pokeIA/driver/chromedriver.exe"):
        self.url = url
        self.browser = browser
        assert self.browser in ["firefox",
                                "chrome"], "please choose a valid browser (only chrome or firefox are supported)"
        if browser == "firefox":
            self.driver = webdriver.Firefox(executable_path=driver_dir)
        elif browser == "chrome":
            self.driver = webdriver.Chrome(executable_path=driver_dir)
        self.wait = WebDriverWait(self.driver, timeout)
        self.username=username
        self.password=password
        self.battles=dict()
        self.action_dict = build_action_dict(possible_action_dict,
                                             possible_on_move_selection_action,
                                             possible_on_switch_selection_action)
        self.teams=dict()

    def start_driver(self):
        self.driver.get(self.url)

    def close_driver(self):
        self.driver.close()

    def clear_cookies(self):
        self.driver.execute_script("localStorage.clear();")

    def wait_home_page(self):
        try:
            self.wait.until(
                check_homepage_loaded()
            )
            return True
        except TimeoutException:
            return False

    def wait_logged(self):
        try:
            self.wait.until(
            check_if_connected(self.username)
            )
            return True
        except TimeoutException:
            return False

    def wait_ladder_battle_start(self):
        try:
            self.wait.until(
                check_if_ladder_battle_started()
            )
            return True
        except TimeoutException:
            return False

    def wait_challenge_battle_start(self,expiration):
        try:
            WebDriverWait(self.driver, expiration).until(
                check_if_challenge_battle_started()
            )
            return True
        except TimeoutException:
            return False

    def turn_off_sound(self):
        try:
            sound = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".icon[name='openSounds']"))
            )
            sound.click()
            mute=self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[name='muted']"))
            )
            mute.click()
        except TimeoutException:
            return 1

    def start_timer(self):

        timer = self.wait.until(
            EC.presence_of_element_located((By.NAME, "openTimer"))
            )
        timer.click()
        timer = self.wait.until(
            EC.presence_of_element_located((By.NAME, "timerOn"))
            )
        timer.click()

    def stop_timer(self):

        timer = self.wait.until(
            EC.presence_of_element_located((By.NAME, "openTimer"))
        )
        timer.click()
        timer = self.wait.until(
            EC.presence_of_element_located((By.NAME, "timerOff"))
        )
        timer.click()

    def import_teams(self, teamtxt_path):
        builder =self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".button[value='teambuilder']"))
        )
        builder.click()
        import_txt = self.wait.until(
            EC.presence_of_element_located((By.NAME, "backup"))
        )
        import_txt.click()
        textfield = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "textbox"))
        )
        with open(teamtxt_path, 'r') as team:
            teamdata = team.read()
        textfield.send_keys(teamdata)
        save = self.wait.until(
            EC.presence_of_element_located((By.NAME, "saveBackup"))
        )
        save.click()
        teams=html.fromstring(self.driver.page_source).xpath('//div[@class="team"]')
        [self.teams.setdefault(team.xpath("./text()")[0].replace('"','').replace('[','').replace(']','').replace(' ',''), []).append(team.xpath("./strong/text()")[0]) for team in teams]
        close_button = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".closebutton[value='teambuilder']"))
        )
        close_button.click()

    def login(self):
        try:
            if not self.wait_home_page():
                return 1

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
            if not self.wait_logged():
                return 1
            return 0
        except TimeoutException:
            return 1

    def choose_tier(self, menu, format='gen7ou'):
        try:
            form = self.wait.until(
                tierwindows_select(menu)
            )
            form.click()
            format_input = self.driver.find_element_by_css_selector("[name='selectFormat'][value='%s']" % format)
            format_input.click()
            gen=found_str_by_regex(format,'gen[0-9]')
            tier=supported_format_eq[format.replace(gen,'')]
        except:
            raise TierException()
        return [gen,tier]

    def select_team(self,index,format):
        num_team=len(self.teams[format])
        if index < num_team:
            select_button = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".select.teamselect"))
            )
            if select_button.is_displayed() and select_button.is_enabled():
                select_button.click()
                team_popup_list = self.wait.until(
                    EC.presence_of_all_elements_located((By.NAME, "selectTeam"))
                )
                team_popup_list[index].click()

    def random_team_choise(self,format):
        return random.randrange(len(self.teams[format]))

    def start_ladder_battle(self, format='gen7ou'):
        try:
            room = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//a[contains(@class,"roomtab") and @href="/"]'))
            )
            if "cur" not in room.get_attribute("class"):
                room.click()
            battle = self.wait.until(
                get_battle_launcher()
            )
            if battle.get_attribute("name") == "showSearchGroup":
                battle.click()
                battle = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".button.big"))
                )
            menu=self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "mainmenu"))
                )
            battle_info=self.choose_tier(menu,format)
            team_select=self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".select.teamselect"))
                )
            if team_select.is_displayed() and team_select.is_enabled():
                try:
                    self.select_team(self.random_team_choise(format), format)
                except:
                    raise NoTeamException()

            battle.click()
            if not self.wait_ladder_battle_start():
                return 1
            battleid=self.driver.current_url.replace(self.url,'')
            if battleid != '':
                self.battles.update({battleid:battle_info})
                return battleid
            return 1
        except TimeoutException:
            return 1

    def start_challenge_battle(self, name, expiration, format='gen7ou'):
        try:
            room = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//a[contains(@class,"roomtab") and @href="/"]'))
            )
            if "cur" not in room.get_attribute("class"):
                room.click()
            finder=self.wait.until(
                EC.presence_of_element_located((By.NAME, 'finduser'))
            )
            finder.click()
            userinput = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@class,"ps-popup")]/form/p/label[text()="Username"]/input'))
            )
            userinput.send_keys(name)
            userinput.send_keys(Keys.RETURN)

            is_connected=self.wait.until(
                wait_to_see_state_of_user()
            )
            if is_connected > 1:
                return 1
            challenge=self.wait.until(
                EC.presence_of_element_located((By.NAME, 'challenge'))
            )
            challenge.click()
            challenge_window=self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'pm-window-'+name))
            )
            battle_info=self.choose_tier(challenge_window,format)
            team_select = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".select.teamselect"))
            )
            if team_select.is_displayed() and team_select.is_enabled():
                try:
                    self.select_team(self.random_team_choise(format), format)
                except:
                    raise NoTeamException()
            button=self.wait.until(
                EC.presence_of_element_located((By.NAME, 'makeChallenge'))
            )
            button.click()
            if not self.wait_challenge_battle_start(expiration):
                cancel = self.wait.until(
                    EC.presence_of_element_located((By.NAME, 'cancelChallenge'))
                )
                cancel.click()
                return 1
            battleid = self.driver.current_url.replace(self.url, '')
            if battleid != '':
                self.battles.update({battleid: battle_info})
                return battleid
            return 1
        except TimeoutException:
            return 1

    def accept_challenge_battle(self, user, expiration):
        try:
            room = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//a[contains(@class,"roomtab") and @href="/"]'))
            )
            if "cur" not in room.get_attribute("class"):
                room.click()
            challenge_window = WebDriverWait(self.driver, expiration).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'pm-window-'+user))
            )
            format=challenge_window.find_element_by_css_selector(".select.formatselect.preselected").get_attribute("value")
            gen = found_str_by_regex(format, 'gen[0-9]')
            tier = supported_format_eq[format.replace(gen, '')]
            battle_info=[gen,tier]
            team_select = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".select.teamselect"))
            )
            if team_select.is_displayed() and team_select.is_enabled():
                try:
                    self.select_team(self.random_team_choise(format), format)
                except:
                    raise NoTeamException()
            button=challenge_window.find_element_by_name("acceptChallenge")
            button.click()
            if not self.wait_challenge_battle_start(expiration):
                return 1
            battleid = self.driver.current_url.replace(self.url, '')
            if battleid != '':
                self.battles.update({battleid: battle_info})
                return battleid
            return 1
        except TimeoutException:
            return 1

    def is_time_to_select_action(self):
        if len(self.driver.find_elements_by_css_selector(".movemenu")) > 0 or len(self.driver.find_elements_by_css_selector(".switchmenu")) > 0:
            return True
        else:
            return False

    def is_battle_finished(self):
        if len(self.driver.find_elements_by_name("closeAndMainMenu")) > 0:
            return True
        return False

    def battle_chat(self, message):
        chatbox = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".chatbox .textbox"))[-1]
            )
        chatbox.send_keys(message)
        chatbox.send_keys(Keys.RETURN)

    def select_random_action(self, gen):
        return random.randrange(len(self.action_dict[gen]))

    def apply_action(self, gen, index):
        action=self.action_dict[gen][index]
        if len(self.driver.find_elements_by_name('zmove')) > 0:
            move_button_selector = ".movebuttons-noz button"
        else:
            move_button_selector =".movemenu button"

        if len(action) == 2:
            if action[0] == 'Zmove':
                if len(self.driver.find_elements_by_name('zmove')) > 0:
                    zmove_button = self.driver.find_element_by_name('zmove')
                    if zmove_button.is_displayed() and zmove_button.is_enabled():
                        zmove_button.click()

                    if action[1].startswith('Move'):
                        movenum = int(action[1].replace('Move', ''))
                        moves = self.driver.find_elements_by_css_selector(".movebuttons-z button")
                        if len(moves) > 0:
                            move = moves[movenum-1]
                            if move.is_displayed() and move.is_enabled() and 'disabled' not in move.get_attribute(
                                    'class'):
                                move.click()

            if action[0] == 'Mega':
                if len(self.driver.find_elements_by_name('megaevo')) > 0:
                    mega_button = self.driver.find_element_by_name('megaevo')
                    if mega_button.is_displayed() and mega_button.is_enabled():
                        mega_button.click()

                    if action[1].startswith('Move'):
                        movenum = int(action[1].replace('Move', ''))
                        moves = self.driver.find_elements_by_css_selector(move_button_selector)
                        if len(moves)>0:
                            move = moves[movenum-1]
                            if move.is_displayed() and move.is_enabled() and 'disabled' not in move.get_attribute('class'):
                                move.click()


        elif len(action) == 1:

            if action[0].startswith('Move'):
                movenum=int(action[0].replace('Move',''))
                moves = self.driver.find_elements_by_css_selector(move_button_selector)
                if len(moves) > 0:
                    move = moves[movenum - 1]
                    if move.is_displayed() and move.is_enabled() and 'disabled' not in move.get_attribute('class'):
                        move.click()

            elif action[0].startswith('Switch'):
                switchnum=int(action[0].replace('Switch',''))
                switches=self.driver.find_elements_by_css_selector(".switchmenu button")
                if len(switches)>0:
                    switch=switches[switchnum-1]
                    if switch.is_displayed() and switch.is_enabled() and 'disabled'not in switch.get_attribute('class'):
                        switch.click()

    def play_battle(self, battle_id):
        room = self.wait.until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@class,"roomtab") and @href="'+battle_id+'"]'))
        )
        if "cur" not in room.get_attribute("class"):
            room.click()
        gen,tier=self.battles[battle_id]
        while not self.is_battle_finished():
            if self.is_time_to_select_action():
                index=self.select_random_action(gen)
                self.apply_action(gen, index)
        closeroom = self.wait.until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@class,"roomtab") and @href="' + battle_id + '"]/following-sibling::button'))
        )
        closeroom.click()

    def initialize_battle_situation(self,battle_id):
        adv_pkmns=self.wait.until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class,"teamicons")]/span[contains(@class,"picon")]'))
        )
        self_pkmns=self.wait.until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class,"switchmenu")]/button'))
        )

    def update_battle_situation(self,battle_id):
        pass



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

    def check_alive(self):
        return self.check_exists_by_css_selector(".rstatbar")

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
