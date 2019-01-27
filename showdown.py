import os, json, gc, re, random, time, shutil, string, unicodedata
from math import sqrt, floor
from selenium import webdriver
from lxml import html, etree
from itertools import combinations, chain
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from exceptions import *

# Global variables
battlelog="D:/projetsIA/pokeIA/battlelog"
download_dir="D:/projetsIA/pokeIA/download"
BASE_URL="https://play.pokemonshowdown.com"
default_home_value="gen7randombattle"
data_dir="D:/projetsIA/pokeIA/pkmn_data"
default_lvl=100
dwnld_foler="D:/Users/FERNANDES_CL/Downloads"
valid_filename_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
char_limit = 255

#If you want to add generations, put the new gens at the end of the list only
gen_list=['gen1','gen2','gen3','gen4','gen5','gen6','gen7']

#If you want to add types, put the new types at the end of the list only
types=['None','Bug','Dark','Dragon','Electric','Fairy','Fighting','Fire','Flying','Ghost','Grass','Ground','Ice','Normal','Poison','Psychic','Rock','Steel','Water']

#If you want to add tiers, put the new tiers at the end of the list only
tier_list=['Limbo','Untiered','OU','Uber','LC','UU','UUBL','NU','NUBL','RU','RUBL','PU','PUBL','AG']

status_list=['none','tox','par','brn','slp','psn','frz']

#The tier inclusion, if you add a new tier, please modify this list accordingly (a tier include all tiers behind him in index position)
tier_order=['LC','Untiered','PU','PUBL','NU','NUBL','RU','RUBL','UU','UUBL','OU','Uber','AG','Limbo']

#False form
fform=['Genesect-Burn','Genesect-Chill','Genesect-Douse','Genesect-Shock']

#A dict which map supported pokemon-showdown battle format to their smogon equivalent tier
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

#A dict which list all possible actions you can do while selecting a move, by gen
possible_on_move_selection_action={
    'gen7':['Zmove'],
    'gen6':['Mega'],
    'gen5':[],
    'gen4':[],
    'gen3':[],
    'gen2':[],
    'gen1':[]
}

#A dict which list all possible actions you can do while selecting switching pokemon, by gen
possible_on_switch_selection_action={
    'gen7':[],
    'gen6':[],
    'gen5':[],
    'gen4':[],
    'gen3':[],
    'gen2':[],
    'gen1':[]
}

#A dict which list all the main actions you can do in pokemon (select a move or switch) , by gen
possible_action_dict={
    'gen7':[],
    'gen6':[],
    'gen5':[],
    'gen4':[],
    'gen3':[],
    'gen2':[],
    'gen1':['Move1','Move2','Move3','Move4',
            'Switch1','Switch2','Switch3','Switch4','Switch5','Switch6']
}

# Utility functions
def clean_filename(filename, whitelist=valid_filename_chars, replace=' '):
    # replace spaces
    for r in replace:
        filename = filename.replace(r, '_')

    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()

    # keep only whitelisted chars
    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
    if len(cleaned_filename) > char_limit:
        print(
            "Warning, filename truncated because it was over {}. Filenames may no longer be unique".format(char_limit))
    return cleaned_filename[:char_limit]

def downloads_done():
    for i in os.listdir(download_dir):
        if ".crdownload" in i or ".tmp" in i:
            time.sleep(0.5)
            downloads_done()

def calc_min_max_stats(statname,lvl,s,gen):
    lvllist = [lvl]
    if lvl == 0:
        lvllist=range(1,101)
    aux=[]
    for lvl in lvllist:
        if gen_list.index(gen)>1:
            if statname == 'HP:':
                if s == 1:
                    aux=aux + [1,1]
                else:
                    aux = aux + [floor((2*s+31+(252/4))*(lvl/100)) + lvl +10, floor((2*s)*(lvl/100)) + lvl +10]
            else:
                aux = aux + [floor(((2*s+31+(252/4))*(lvl/100) + 5) *1.1),floor(((2*s)*(lvl/100) + 5) *0.9)]
        else:
            if statname == 'HP:':
                if s == 1:
                    aux = aux + [1, 1]
                else:
                    aux = aux + [floor(((s+31)*2+floor(sqrt(252)/4))*(lvl/100)) + lvl + 10,floor(((s)*2)*(lvl/100)) + lvl + 10]
            else:
                aux = aux + [floor(((s+31)*2+floor(sqrt(252)/4))*(lvl/100)) + 5,floor(((s)*2)*(lvl/100)) + 5]

    return [min(aux),max(aux)]

def calc_pkmn_stats(pokedict,gen):
    statkey= ['HP:','Attack:','Defense:','Sp. Atk:','Sp. Def:','Speed:']
    for k in statkey:
        pokedict[k]=[calc_min_max_stats(k,int(pokedict['Lvl']),int(s),gen) for s in pokedict[k]]

def write_json_dict(folder,filename,data):
    with open(os.path.join(folder, filename), 'w') as outfile:
        outfile.write(json.dumps(data))

def isincluded_tier(tier_list_order,tier):
    index=tier_list_order.index(tier)
    return [x for i,x in enumerate(tier_list_order) if i <=index]

def write_txt(folder,filename,data):
    if not os.path.exists(os.path.join(folder, filename)):
        with open(os.path.join(folder, filename), 'w') as outfile:
            outfile.write(data)
    else:
        with open(os.path.join(folder, filename), 'a') as outfile:
            outfile.write(data)

def merge_pkmn_dicts_same_key(ds):
    res = {}
    [res.update({k: [d[k] for d in ds]}) for k in ds[0].keys()]
    return res

def found_str_by_regex(string,regex):
    try:
        found = re.search(regex, string).group(0)
    except AttributeError:
        found = ""
    return found

def build_action_dict(actiondict,on_move_actiondict,on_switch_actiondict):
    res=dict()
    for key in actiondict:
        index = gen_list.index(key)
        included_gens = [x for i, x in enumerate(gen_list) if i <= index]
        actions=[]
        for genkey in included_gens:
            actions = actions + [[action] for action in actiondict[genkey]]
            actions=actions + [[[action, move[0]] for move in actions if len(move)==1 and move[0].startswith('Move')] for action in on_move_actiondict[genkey]]
            actions = actions + [[[action, switch[0]] for switch in actions if len(switch)==1 and switch[0].startswith('Switch')] for action in on_switch_actiondict[genkey]]
        res.update({key:actions})
    return res

def build_action_map(gen,actiondict):
    res=dict()
    return [res.update({i:action}) for i,action in enumerate(actiondict[gen])]

def get_moves_data(gen,listmoves=None):
    with open(os.path.join(data_dir, 'moves.json'), 'r') as moves_json:
        moves_data=json.load(moves_json)[gen]
    if listmoves is not None:
        return {l:moves_data[l] for l in listmoves}
    return moves_data

def get_items_data(gen,listitems=None):
    with open(os.path.join(data_dir, 'items.json'), 'r') as items_json:
        items_data=json.load(items_json)[gen]
    if listitems is not None:
        return {l: items_data[l] for l in listitems}
    return items_data

def get_items_key(gen):
    with open(os.path.join(data_dir, 'items.json'), 'r') as items_json:
        items_data=json.load(items_json)[gen]
    return list(items_data.keys())

def get_abilities_data(gen,listabilities=None):
    with open(os.path.join(data_dir, 'abilities.json'), 'r') as abilities_json:
        abilities_data=json.load(abilities_json)[gen]
    if listabilities is not None:
        return {l:abilities_data[l] for l in listabilities}
    return abilities_data

def get_pkmn_data(pkmn,gen,tier):
    tiers = isincluded_tier(tier_order, tier)
    f_data={}
    with open(os.path.join(data_dir, 'pkmns.json'), 'r') as pkmns_json:
        pkmn_data = json.load(pkmns_json)[gen]
        pkmn_data = [pkmn_data[key] for key in tiers]
        [f_data.update(d) for d in pkmn_data]
    if pkmn in f_data.keys():
        res_data=merge_pkmn_dicts_same_key([f_data[pkmn]])
    else:
        res_data=merge_pkmn_dicts_same_key([f_data[pkmn] for pkmn in f_data.keys()])
    return res_data

def parse_pkmn_id(identifier):
    res={}
    id=identifier.replace('|',' (').split(" (")
    id=[i.replace(')','') for i in id]
    active = [found_str_by_regex(i, 'active') for i in id if found_str_by_regex(i, 'active') != ""]
    fainted = [found_str_by_regex(i, 'fainted') for i in id if found_str_by_regex(i, 'fainted') != ""]
    health = [found_str_by_regex(i, '(\d+(\.\d+)?)%') for i in id if
              found_str_by_regex(i, '(\d+(\.\d+)?)%') != ""]
    status = [i for i in id if i in status_list]
    id = [i for i in id if i not in active and i not in health and i not in fainted and i not in status]
    if len(active)==1:
        res['Active']=1
    else:
        res['Active']=0
    if len(fainted)==1:
        res['Fainted']=1
    else:
        res['Fainted']=0
    if len(health)==1:
        res['Health'] = float(health[0].replace('%',''))
    if len(status)==1:
        res['Status']=status[0]
    else:
        res['Status']='none'
    if len(id)>1:
        pkmn=id[1]
    else:
        pkmn = id[0]
    return pkmn,res

def build_pokedict(poke_info,gen,tier):
    res={}
    res.update(poke_info[1])
    res['Health']=100
    res['Items']=get_items_key(gen)
    res['Gender']='none'
    res['Lvl']=default_lvl
    res['MoveSeen']=[]
    res.update(get_pkmn_data(poke_info[0],gen,tier))
    calc_pkmn_stats(res, gen)
    res['PP'] = [None, None, None, None]
    return {poke_info[0]:res}

def update_pokedict_with_icon(pokedict,poke_info,gen,tier):
    key=[key for key in pokedict.keys()][0]
    pokedict[key].update(poke_info[1])
    if key!=poke_info[0]:
        pokedict[poke_info[0]] = pokedict.pop(key)
        key=poke_info[0]
        pokedict[key].update(get_pkmn_data(poke_info[0], gen, tier))
        calc_pkmn_stats(pokedict[key], gen)

def update_my_pokedict_div(pokedict,poke_info):
    key=[key for key in pokedict.keys()][0]
    pokedict[key].update(poke_info[1])
    if key!=poke_info[0]:
        pokedict[poke_info[0]] = pokedict.pop(key)

def build_movepool(movepoollist):
    return [list(combinations(movepool,4)) for movepool in movepoollist]

def get_list_containing_sublist(alist, asublist):
    return [elem for elem in alist if elem[0:0+len(asublist)]==asublist]

def remove_empty_list_recusrsively(alist,index):
    for i,elem in enumerate(alist[index]):
        if isinstance(elem,list):
            remove_empty_list_recusrsively(alist,i)
    if len(alist[index]) == 0:
        alist.pop(index)

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
            options = webdriver.FirefoxOptions()
            prefs = {'download.default_directory': download_dir}
            options.add_experimental_option('prefs', prefs)
            self.driver = webdriver.Firefox(executable_path=driver_dir,firefox_options=options)
        elif browser == "chrome":
            options = webdriver.ChromeOptions()
            prefs = {'download.default_directory': download_dir}
            options.add_experimental_option('prefs', prefs)
            self.driver = webdriver.Chrome(executable_path=driver_dir,chrome_options=options)
        self.wait = WebDriverWait(self.driver, timeout)
        self.username=username
        self.password=password
        self.battles=dict()
        self.action_dict = build_action_dict(possible_action_dict,
                                             possible_on_move_selection_action,
                                             possible_on_switch_selection_action)
        print(self.action_dict)
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
            return True
        except TimeoutException:
            return False

    def start_timer(self):
        try:
            timer = self.wait.until(
                EC.presence_of_element_located((By.NAME, "openTimer"))
                )
            timer.click()
            timer = self.wait.until(
                EC.presence_of_element_located((By.NAME, "timerOn"))
                )
            timer.click()
            return True
        except TimeoutException:
            return False

    def stop_timer(self):
        try:
            timer = self.wait.until(
                EC.presence_of_element_located((By.NAME, "openTimer"))
            )
            timer.click()
            timer = self.wait.until(
                EC.presence_of_element_located((By.NAME, "timerOff"))
            )
            timer.click()
            return True
        except TimeoutException:
            return False

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
        return [gen,tier,format.replace(gen,'')]

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
                self.battles.update(
                    {battleid: {'gen': battle_info[0], 'tier': battle_info[1], 'format': battle_info[2],
                                'battle_situation': dict()}})
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
                self.battles.update(
                    {battleid: {'gen': battle_info[0], 'tier': battle_info[1], 'format': battle_info[2],
                                'battle_situation': dict()}})
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
                self.battles.update(
                    {battleid: {'gen': battle_info[0], 'tier': battle_info[1], 'format': battle_info[2],
                                'battle_situation': dict()}})
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

    def play_battle(self, battle_id, write=False):
        room = self.wait.until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@class,"roomtab") and @href="'+battle_id+'"]'))
        )
        if "cur" not in room.get_attribute("class"):
            room.click()
        self.initialize_battle_situation(battle_id)
        while not self.is_battle_finished():
            self.update_with_div_info(self.battles[battle_id]['battle_situation']['adv_poke_map'],
                                      self.get_adv_active_pkmn_info(battle_id))
            if self.is_time_to_select_action():
                self.update_battle_situation(battle_id)
                self.update_with_div_info(self.battles[battle_id]['battle_situation']['adv_poke_map'],
                                          self.get_adv_active_pkmn_info(battle_id))
                if write:
                    self.write_situation_history(battle_id)
                index=self.select_random_action(self.battles[battle_id]['gen'])
                self.apply_action(self.battles[battle_id]['gen'], index)

        if write:
            self.get_battle_html_file(battle_id)
        closeroom = self.wait.until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@class,"roomtab") and @href="' + battle_id + '"]/following-sibling::button'))
        )
        self.battles.pop(battle_id,None)
        gc.collect()
        closeroom.click()

    def initialize_battle_situation(self,battle_id):
        pkmns=self.wait.until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class,"teamicons")]/span[contains(@class,"picon")]'))
        )
        my_pkmns = [parse_pkmn_id(adv_pkmn.get_attribute('title')) for adv_pkmn in pkmns[:6]]
        my_poke_map = {index: build_pokedict(pkmn, self.battles[battle_id]['gen'], self.battles[battle_id]['tier']) for
                        index, pkmn in enumerate(my_pkmns)}
        self.battles[battle_id]['battle_situation'].update({'my_poke_map': my_poke_map})
        adv_pkmns = [parse_pkmn_id(adv_pkmn.get_attribute('title')) for adv_pkmn in pkmns[6:]]
        adv_poke_map = {index: build_pokedict(pkmn, self.battles[battle_id]['gen'], self.battles[battle_id]['tier']) for
                        index, pkmn in enumerate(adv_pkmns)}
        self.battles[battle_id]['battle_situation'].update({'adv_poke_map':adv_poke_map})

    def update_battle_situation(self,battle_id):

        pkmns = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, '//div[contains(@class,"teamicons")]/span[contains(@class,"picon")]'))
        )
        adv_pkmns = [parse_pkmn_id(adv_pkmn.get_attribute('title')) for adv_pkmn in pkmns[6:]]
        [update_pokedict_with_icon(self.battles[battle_id]['battle_situation']['adv_poke_map'][index],pkmn,self.battles[battle_id]['gen'], self.battles[battle_id]['tier']) for
                        index, pkmn in enumerate(adv_pkmns)]

        my_up_pkmns = self.driver.find_elements_by_css_selector(".switchmenu button")
        if len(my_up_pkmns)>0:
            [update_my_pokedict_div(self.battles[battle_id]['battle_situation']['my_poke_map'][index],
                                    self.get_pkmn_info_div(my_pkmn)) for
             index, my_pkmn in enumerate(my_up_pkmns)]
        else:
            self.update_with_div_info(self.battles[battle_id]['battle_situation']['my_poke_map'],
                                  self.get_my_active_pkmn_info(battle_id))
        self.get_current_boost(battle_id)
        self.get_terrain_info(battle_id)

    def get_adv_active_pkmn_info(self,battleid):
        iddiv="BattleTooltips.showTooltipFor('"+battleid.replace('/','')+"', 'your0','pokemon', this, true)"
        test=self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@onmouseover ="'+iddiv+'"]'))
        )
        return(self.get_pkmn_info_div(test))

    def get_my_active_pkmn_info(self,battleid):
        iddiv="BattleTooltips.showTooltipFor('"+battleid.replace('/','')+"', 'my0','pokemon', this, true)"
        test=self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@onmouseover ="'+iddiv+'"]'))
        )
        pkmn,res=self.get_pkmn_info_div(test)
        movediv = html.fromstring(self.driver.page_source).xpath('//div[@class="movemenu"]/button[@name="chooseMove"]')
        move_info=[self.parse_move_div(move) for move in movediv]
        res['MoveSeen']=[]
        for i, a in enumerate(move_info):
                res['MoveSeen'].append(a[0])
                res['PP'][i]=a[1]
        return pkmn,res

    def update_with_div_info(self,pkmn_dict,pkmn_info):
        for key in pkmn_dict.keys():
            if pkmn_info[0] in pkmn_dict[key].keys():
                pkmn_dict[key][pkmn_info[0]].update(pkmn_info[1])

    def get_pkmn_info_div(self,elem):
        res={}
        pkmn=""
        hover = ActionChains(self.driver).move_to_element(elem)
        hover.perform()
        div_info = html.fromstring(self.driver.page_source).xpath('//div[@id="tooltipwrapper"]')
        if len(div_info)>0:
            div_info = div_info[0]
            if ''.join([etree.tostring(child).decode('unicode_escape') for child in div_info.iterdescendants()])!='':
                pkmn=div_info.xpath('.//h2/text()')[0].rstrip()
                aux = div_info.xpath('.//h2/small/text()')
                for a in aux:
                    form = found_str_by_regex(a, '\(([^\)]+)\)').replace('(', '').replace(')', '')
                    if form !="" and form not in fform:
                        pkmn=form.rstrip()
                    lvl = found_str_by_regex(a, 'L[0-9][0-9]').replace('L', '')
                    if lvl != "":
                        res['Lvl'] = int(lvl)
                aux=div_info.xpath('.//img[contains(@src,"gender")]/@alt')
                if len(aux)>0:
                    res['Gender'] = aux[0]
                aux=div_info.xpath('.//span[contains(@class,"status")]/text()')
                if len(aux)>0:
                    res['Status']=aux[0].lower()
                #res['Type']=div_info.xpath('.//img[contains(@src,"types")]/@alt')
                aux = [str(t).replace('\xa0', '').replace('• ', '').split(' /') for t in
                       div_info.xpath('.//p[not(contains(@class, "section"))]/text()')]
                if found_str_by_regex(aux[0][0], '(\d+(\.\d+)?)%') != "":
                    res['Health'] = float(found_str_by_regex(aux[0][0], '(\d+(\.\d+)?)%').replace('%', ''))
                else:
                    res['Health'] = float(0)
                hp = found_str_by_regex(aux[0][0], '(?<![\d.])[0-9]+(?![\d.]).*?(?<![\d.])[0-9]+(?![\d.])')
                hp=hp.split("/")
                if len(hp) >1 and hp[1] != "":
                    res['HP:']=[[int(hp[1]),int(hp[1])]]
                if len(aux[1]) > 0:
                    if found_str_by_regex(aux[1][0], 'Ability: ') != "":
                        res['Abilities'] = [aux[1][0].replace('Ability: ', '')]
                    elif found_str_by_regex(aux[1][0], 'Possible abilities: ') != "":
                        res['Abilities'] = aux[1][0].replace('Possible abilities: ', '').split(', ')
                if len(aux[1]) > 1:
                    if found_str_by_regex(aux[1][1], ' Item: ') != "":
                        res['Items'] = [aux[1][1].replace(' Item: ', '')]
                for stat in aux[2]:
                    if found_str_by_regex(stat, 'Atk')!= "":
                        res['Attack:']=[int(s) for s in re.findall('(?<![\d.])[0-9]+(?![\d.])',stat)]
                        if len(res['Attack:'])==1:
                            res['Attack:']=[[res['Attack:'][0],res['Attack:'][0]]]
                    if found_str_by_regex(stat, 'Def')!= "":
                        res['Defense:']=[int(s) for s in re.findall('(?<![\d.])[0-9]+(?![\d.])',stat)]
                        if len(res['Defense:'])==1:
                            res['Defense:']=[[res['Defense:'][0],res['Defense:'][0]]]
                    if found_str_by_regex(stat, 'SpA')!= "":
                        res['Sp. Atk:']=[int(s) for s in re.findall('(?<![\d.])[0-9]+(?![\d.])',stat)]
                        if len(res['Sp. Atk:'])==1:
                            res['Sp. Atk:']=[[res['Sp. Atk:'][0],res['Sp. Atk:'][0]]]
                    if found_str_by_regex(stat, 'SpD')!= "":
                        res['Sp. Def:']=[int(s) for s in re.findall('(?<![\d.])[0-9]+(?![\d.])',stat)]
                        if len(res['Sp. Def:'])==1:
                            res['Sp. Def:']=[[res['Sp. Def:'][0],res['Sp. Def:'][0]]]
                    if found_str_by_regex(stat, 'Spe')!= "":
                        res['Speed:']=[int(s) for s in re.findall('(?<![\d.])[0-9]+(?![\d.])',stat)]
                        if len(res['Speed:'])==1:
                            res['Speed:']=[[res['Speed:'][0],res['Speed:'][0]]]

                aux = div_info.xpath('.//p[contains(@class, "section")]//text()')
                res['PP']=[None,None,None,None]
                res['MoveSeen']=[]
                id=0
                for a in aux:
                    test=[int(s) for s in re.findall('(?<![\d.])[0-9]+(?![\d.])',a)]
                    if len(test)>1:
                            if int(test[1]) == 1:
                                del res['MoveSeen'][-1]
                            else:
                                res['PP'][id] = int(test[0])
                    else:
                        res['MoveSeen'].append(a.replace('• ', '').rstrip())
                        id=len(res['MoveSeen'])-1
        return pkmn, res

    def parse_move_div(self,movediv):
        pp=movediv.xpath('./small[@class="pp"]/text()')[0]
        pp=pp.split('/')[0]
        return[movediv.xpath('./text()')[0],pp]

    def write_situation_history(self,battle_id):
        dir_user=clean_filename(self.username)
        if not os.path.exists(os.path.join(battlelog,dir_user)):
            os.makedirs(os.path.join(battlelog,dir_user))
        dir=battle_id.replace('/','')
        if not os.path.exists(os.path.join(battlelog,dir_user,dir)):
            os.makedirs(os.path.join(battlelog,dir_user,dir))
        i=len([x for x in os.listdir(os.path.join(battlelog,dir_user,dir)) if x.endswith('.json')])
        write_json_dict(os.path.join(battlelog,dir_user,dir), dir+'_'+str(i)+'.json',self.battles[battle_id])

    def get_battle_html_file(self,battle_id):
        dir_user = clean_filename(self.username)
        dir = battle_id.replace('/', '')
        dwnld_button=self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.button.replayDownloadButton'))
        )
        dwnld_button.click()
        downloads_done()
        filename = max([os.path.join(download_dir,f) for f in os.listdir(download_dir)], key=os.path.getctime)
        shutil.move(os.path.join(download_dir, filename), os.path.join(battlelog,dir_user,dir,dir+'.html'))

    def get_current_boost(self,battleid):
        my_boost_info = html.fromstring(self.driver.page_source).xpath(
            '//div[contains(@class,"statbar") and contains(@class,"rstatbar")]//span[@class="good" or @class="bad"]/text()')
        self.battles[battleid]['battle_situation']['my_boost']=[1.0,1.0,1.0,1.0,1.0,1.0,1.0]
        rm_list=[]
        for boost in my_boost_info:
            if found_str_by_regex(boost, 'Atk') != "":
                self.battles[battleid]['battle_situation']['my_boost'][0] = float(found_str_by_regex(boost, '(\d+(\.\d+)?)'))
                rm_list = rm_list + [boost]
            if found_str_by_regex(boost, 'Def') != "":
                self.battles[battleid]['battle_situation']['my_boost'][1] = float(found_str_by_regex(boost, '(\d+(\.\d+)?)'))
                rm_list = rm_list + [boost]
            if found_str_by_regex(boost, 'SpA') != "":
                self.battles[battleid]['battle_situation']['my_boost'][2] = float(found_str_by_regex(boost, '(\d+(\.\d+)?)'))
                rm_list = rm_list + [boost]
            if found_str_by_regex(boost, 'SpD') != "":
                self.battles[battleid]['battle_situation']['my_boost'][3] = float(found_str_by_regex(boost, '(\d+(\.\d+)?)'))
                rm_list = rm_list + [boost]
            if found_str_by_regex(boost, 'Spe') != "":
                self.battles[battleid]['battle_situation']['my_boost'][4] = float(found_str_by_regex(boost, '(\d+(\.\d+)?)'))
                rm_list = rm_list + [boost]
            if found_str_by_regex(boost, 'Accuracy') != "":
                self.battles[battleid]['battle_situation']['my_boost'][5] = float(found_str_by_regex(boost, '(\d+(\.\d+)?)'))
                rm_list = rm_list + [boost]
            if found_str_by_regex(boost, 'Evasion') != "":
                self.battles[battleid]['battle_situation']['my_boost'][6] = float(found_str_by_regex(boost, '(\d+(\.\d+)?)'))
                rm_list = rm_list + [boost]
        self.battles[battleid]['battle_situation']['my_state']=[elem for elem in my_boost_info if elem not in rm_list]

        adv_boost_info = html.fromstring(self.driver.page_source).xpath(
            '//div[contains(@class,"statbar") and contains(@class,"lstatbar")]//span[@class="good" or @class="bad"]/text()')
        self.battles[battleid]['battle_situation']['adv_boost'] = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        rm_list = []
        for boost in adv_boost_info:
            if found_str_by_regex(boost, 'Atk') != "":
                self.battles[battleid]['battle_situation']['adv_boost'][0] = float(
                    found_str_by_regex(boost, '(\d+(\.\d+)?)'))
                rm_list = rm_list + [boost]
            if found_str_by_regex(boost, 'Def') != "":
                self.battles[battleid]['battle_situation']['adv_boost'][1] = float(
                    found_str_by_regex(boost, '(\d+(\.\d+)?)'))
                rm_list = rm_list + [boost]
            if found_str_by_regex(boost, 'SpA') != "":
                self.battles[battleid]['battle_situation']['adv_boost'][2] = float(
                    found_str_by_regex(boost, '(\d+(\.\d+)?)'))
                rm_list = rm_list + [boost]
            if found_str_by_regex(boost, 'SpD') != "":
                self.battles[battleid]['battle_situation']['adv_boost'][3] = float(
                    found_str_by_regex(boost, '(\d+(\.\d+)?)'))
                rm_list = rm_list + [boost]
            if found_str_by_regex(boost, 'Spe') != "":
                self.battles[battleid]['battle_situation']['adv_boost'][4] = float(
                    found_str_by_regex(boost, '(\d+(\.\d+)?)'))
                rm_list = rm_list + [boost]
            if found_str_by_regex(boost, 'Accuracy') != "":
                self.battles[battleid]['battle_situation']['adv_boost'][5] = float(
                    found_str_by_regex(boost, '(\d+(\.\d+)?)'))
                rm_list = rm_list + [boost]
            if found_str_by_regex(boost, 'Evasion') != "":
                self.battles[battleid]['battle_situation']['adv_boost'][6] = float(
                    found_str_by_regex(boost, '(\d+(\.\d+)?)'))
                rm_list = rm_list + [boost]
        self.battles[battleid]['battle_situation']['adv_state'] = [elem for elem in adv_boost_info if elem not in rm_list]

    def get_terrain_info(self,battleid):
        weather = html.fromstring(self.driver.page_source).xpath('//div[@class="innerbattle"]//div[contains(@class, "weather")]/em//text()')
        id=0
        self.battles[battleid]['battle_situation']['weather']=[]
        for a in weather:
            test = [int(s) for s in re.findall('(?<![\d.])[0-9]+(?![\d.])', a)]
            if len(test) > 0:
                if len(test) != 2:
                    test=[test[0],test[0]]
                self.battles[battleid]['battle_situation']['weather'][id] =[self.battles[battleid]['battle_situation']['weather'][id],test]
            else:
                self.battles[battleid]['battle_situation']['weather'].append([a.rstrip()])
                id = len(self.battles[battleid]['battle_situation']['weather']) - 1
        self.battles[battleid]['battle_situation']['my_hasard']=[]
        my_rock=html.fromstring(self.driver.page_source).xpath(
            '//div[@class="innerbattle"]/div[@role="complementary"]/preceding-sibling::div[1]/div[3]/img[contains(@src, "rock")]')
        if len(my_rock)>0:
            self.battles[battleid]['battle_situation']['my_hasard'].append(['Stealth Rock',1])
        my_web = html.fromstring(self.driver.page_source).xpath(
            '//div[@class="innerbattle"]/div[@role="complementary"]/preceding-sibling::div[1]/div[3]/img[contains(@src, "web")]')
        if len(my_web) > 0:
            self.battles[battleid]['battle_situation']['my_hasard'].append(['Sticky Web', 1])
        my_spike=html.fromstring(self.driver.page_source).xpath(
            '//div[@class="innerbattle"]/div[@role="complementary"]/preceding-sibling::div[1]/div[3]/img[contains(@src, "caltrop") and not(contains(@src, "poisoncaltrop"))]')
        if len(my_spike)>0:
            self.battles[battleid]['battle_situation']['my_hasard'].append(['Spike',len(my_spike)])
        my_toxicspike=html.fromstring(self.driver.page_source).xpath(
            '//div[@class="innerbattle"]/div[@role="complementary"]/preceding-sibling::div[1]/div[3]/img[contains(@src, "poisoncaltrop")]')
        if len(my_toxicspike)>0:
            self.battles[battleid]['battle_situation']['my_hasard'].append(['Toxic Spike',len(my_toxicspike)])

        self.battles[battleid]['battle_situation']['adv_hasard'] = []
        adv_rock = html.fromstring(self.driver.page_source).xpath(
            '//div[@class="innerbattle"]/div[@role="complementary"]/preceding-sibling::div[1]/div[2]/img[contains(@src, "rock")]')
        if len(adv_rock) > 0:
            self.battles[battleid]['battle_situation']['adv_hasard'].append(['Stealth Rock', 1])
        adv_web = html.fromstring(self.driver.page_source).xpath(
            '//div[@class="innerbattle"]/div[@role="complementary"]/preceding-sibling::div[1]/div[2]/img[contains(@src, "web")]')
        if len(adv_web) > 0:
            self.battles[battleid]['battle_situation']['adv_hasard'].append(['Sticky Web', 1])
        adv_spike = html.fromstring(self.driver.page_source).xpath(
            '//div[@class="innerbattle"]/div[@role="complementary"]/preceding-sibling::div[1]/div[2]/img[contains(@src, "caltrop") and not(contains(@src, "poisoncaltrop"))]')
        if len(adv_spike) > 0:
            self.battles[battleid]['battle_situation']['adv_hasard'].append(['Spike', len(adv_spike)])
        adv_toxicspike = html.fromstring(self.driver.page_source).xpath(
            '//div[@class="innerbattle"]/div[@role="complementary"]/preceding-sibling::div[1]/div[2]/img[contains(@src, "poisoncaltrop")]')
        if len(adv_toxicspike) > 0:
            self.battles[battleid]['battle_situation']['adv_hasard'].append(['Toxic Spike', len(adv_toxicspike)])
