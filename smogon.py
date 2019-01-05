from lxml import html
from selenium import webdriver
import tqdm
import json
import os
import collections
import itertools

num_gen=7

def makehash():
    return collections.defaultdict(makehash)

def makehash_update(dictt,keys,value):
    if len(keys)==1:
        dictt[keys[0]]=value
    else:
        currentkey=keys[0]
        keys.pop(0)
        makehash_update(dictt[currentkey], keys, value)

def write_json_dict(folder,filename,data):
    with open(os.path.join(folder, filename), 'w') as outfile:
        json.dump(data, outfile)

def isplit(iterable,splitters):
    return [list(g) for k,g in itertools.groupby(iterable,lambda x:x in splitters) if not k]

def split_pkmn_form(string,char,index):
    try:
        return string.rsplit(char,1)[index]
    except IndexError:
        return ""

class Smogon():
    BASE_URL = "https://www.smogon.com"
    def __init__(self, url=BASE_URL, browser='chrome',
                 driver_dir="D:/projetsIA/pokeIA/driver/chromedriver.exe"):
        self.url = url
        self.browser = browser
        assert self.browser in ["firefox",
                                "chrome"], "please choose a valid browser (only chrome or firefox are supported)"
        self.tree = None
        if browser == "firefox":
            self.driver = webdriver.Firefox(executable_path=driver_dir)
        elif browser == "chrome":
            self.driver = webdriver.Chrome(executable_path=driver_dir)

    def parse_table(self, table, multi=False):
        keys = table.xpath('.//th/descendant-or-self::*/text()')
        if multi == True:
            values = table.xpath('.//td')
            values = [value.xpath('./descendant-or-self::*/text()') for value in values if len(value) > 0]
        else:
            values = table.xpath('.//td/descendant-or-self::*/text()')
        return dict(zip(keys, values))

    def get_all_moves(self,folder):
        all_moves=dict()
        if os.path.exists(os.path.join(folder, 'moves.json')):
            os.remove(os.path.join(folder, 'moves.json'))
        url = self.url +"/dex/"
        self.driver.get(url)
        self.tree = html.fromstring(self.driver.page_source)
        gens=self.tree.xpath('//div[@id="body"]/div[@id="front_top"]/following-sibling::ul//a/@href')
        gens=[['gen'+str(num_gen-i),gen.replace('/pokemon/','')] for i,gen in enumerate(gens)]
        [all_moves.update({gen[0]:self.get_moves(gen[1])}) for gen in tqdm.tqdm(gens, desc='Getting moves for all gens')]
        write_json_dict(folder, 'moves.json',all_moves)

    def get_moves(self,genurl):
        res = dict()
        url = self.url + genurl + "/moves/"
        self.driver.get(url)
        max_height = self.driver.execute_script("return document.body.scrollHeight")
        previous = 0
        moves=[]
        for y in tqdm.tqdm(range(0,max_height,100),desc='Listing all moves for current gen'):
            self.driver.execute_script("window.scrollTo(" + str(previous) + ", " + str(y) + ")")
            self.tree = html.fromstring(self.driver.page_source)
            moves = moves + [x for x in self.tree.xpath(
                '//div[contains(@class,"DexTable")]/div[contains(@class,"MoveRow")]/div[contains(@class,"MoveRow-name")]/a')
                             if x.xpath('text()')[0] not in [move.xpath('text()')[0] for move in moves]]
            previous=y

        [res.update({move.xpath('text()')[0]: self.get_move_info(self.url + move.xpath('@href')[0])}) for move in
         tqdm.tqdm(moves, desc='Getting move information for current gen')]
        return res

    def get_move_info(self, url):
        move_info = dict()
        self.driver.get(url)
        self.tree = html.fromstring(self.driver.page_source)
        table = self.tree.xpath('//table[contains(@class,"MoveInfo")]')[0]
        move_info.update(self.parse_table(table))
        move_info.update({'Desc': self.tree.xpath('//main[contains(@class,"DexContent")]/div/p[1]/text()')[0]})
        flags=self.tree.xpath('//main[contains(@class,"DexContent")]/div/p[2]/span[contains(text(),":")]/following-sibling::span/text()')
        if len(flags)>0:
            move_info.update({'Flags': flags[0].split(", ")})
        else:
            move_info.update({'Flags': []})
        return (move_info)

    def get_all_items(self,folder):
        all_items=dict()
        if os.path.exists(os.path.join(folder, 'items.json')):
            os.remove(os.path.join(folder, 'items.json'))
        url = self.url +"/dex/"
        self.driver.get(url)
        self.tree = html.fromstring(self.driver.page_source)
        gens=self.tree.xpath('//div[@id="body"]/div[@id="front_top"]/following-sibling::ul//a/@href')
        gens=[['gen'+str(num_gen-i),gen.replace('/pokemon/','')] for i,gen in enumerate(gens)]
        [all_items.update({gen[0]:self.get_items(gen[1])}) for gen in tqdm.tqdm(gens, desc='Getting items for all gens')]
        write_json_dict(folder, 'items.json',all_items)

    def get_items(self,genurl):
        res = dict()
        url = self.url + genurl + "/items/"
        self.driver.get(url)
        max_height = self.driver.execute_script("return document.body.scrollHeight")
        previous = 0
        items=[]
        for y in tqdm.tqdm(range(0,max_height,100),desc='Listing all items for current gen'):
            self.driver.execute_script("window.scrollTo(" + str(previous) + ", " + str(y) + ")")
            self.tree = html.fromstring(self.driver.page_source)
            items = items + [x for x in self.tree.xpath(
                '//div[contains(@class,"DexTable")]/div[contains(@class,"ItemRow")]')
                             if x.xpath('./div[contains(@class,"ItemRow-name")]/a/span/span[not(contains(@class,"ItemSprite"))]/text()')[0] not in [item.xpath('./div[contains(@class,"ItemRow-name")]/a/span/span[not(contains(@class,"ItemSprite"))]/text()')[0] for item in items]]
            previous=y

        [res.update({item.xpath('./div[contains(@class,"ItemRow-name")]/a/span/span[not(contains(@class,"ItemSprite"))]/text()')[0]: item.xpath('./div[contains(@class,"ItemRow-description")]/text()')[0]}) for item in
         tqdm.tqdm(items, desc='Getting item information for current gen')]
        return res

    def get_all_abilities(self,folder):
        all_abilities=dict()
        if os.path.exists(os.path.join(folder, 'abilities.json')):
            os.remove(os.path.join(folder, 'abilities.json'))
        url = self.url +"/dex/"
        self.driver.get(url)
        self.tree = html.fromstring(self.driver.page_source)
        gens=self.tree.xpath('//div[@id="body"]/div[@id="front_top"]/following-sibling::ul//a/@href')
        gens=[['gen'+str(num_gen-i),gen.replace('/pokemon/','')] for i,gen in enumerate(gens)]
        [all_abilities.update({gen[0]:self.get_abilities(gen[1])}) for gen in tqdm.tqdm(gens, desc='Getting abilities for all gens')]
        write_json_dict(folder, 'abilities.json',all_abilities)

    def get_abilities(self,genurl):
        res = dict()
        url = self.url + genurl + "/abilities/"
        self.driver.get(url)
        max_height = self.driver.execute_script("return document.body.scrollHeight")
        previous = 0
        abilities=[]
        for y in tqdm.tqdm(range(0,max_height,100),desc='Listing all abilities for current gen'):
            self.driver.execute_script("window.scrollTo(" + str(previous) + ", " + str(y) + ")")
            self.tree = html.fromstring(self.driver.page_source)
            abilities = abilities + [x for x in self.tree.xpath(
                '//div[contains(@class,"DexTable")]/div[contains(@class,"AbilityRow")]')
                             if x.xpath('./div[contains(@class,"AbilityRow-name")]/a/text()')[0] not in [ability.xpath('./div[contains(@class,"AbilityRow-name")]/a/text()')[0] for ability in abilities]]
            previous=y

        [res.update({ability.xpath('./div[contains(@class,"AbilityRow-name")]/a/text()')[0]: ability.xpath('./div[contains(@class,"AbilityRow-description")]/text()')[0]}) for ability in
         tqdm.tqdm(abilities, desc='Getting ability information for current gen')]
        return res

    def get_pkmn_info(self,url, battle_form=''):
        pkmn_info=dict()
        if battle_form=="":
            battle_form="Base"
        self.driver.get(url)
        self.tree = html.fromstring(self.driver.page_source)
        pkmn_stat_div = self.tree.xpath('//div/section/section/div[contains(@class,"PokemonAltInfo")]')
        if len(pkmn_stat_div)>1:
            pkmn_stat_div=self.tree.xpath('//div/section/section/h1[contains(text(),"'+battle_form+'")]/following-sibling::div[contains(@class,"PokemonAltInfo")]')
            if len(pkmn_stat_div) == 0:
                battle_form = "Base"
                pkmn_stat_div = self.tree.xpath(
                    '//div/section/section/h1[contains(text(),"' + battle_form + '")]/following-sibling::div[contains(@class,"PokemonAltInfo")]')[
                    0]
            else:
                pkmn_stat_div = pkmn_stat_div[0]
        else:
            pkmn_stat_div=pkmn_stat_div[0]
        table = pkmn_stat_div.xpath('.//table[contains(@class,"PokemonSummary")]')[0]
        pkmn_info.update(self.parse_table(table, True))
        table = pkmn_stat_div.xpath('.//table[contains(@class,"PokemonStats")]')[0]
        pkmn_info.update(self.parse_table(table))
        pkmn_info["Type"]=isplit(pkmn_info["Type"],("Immune to:","Strongly resists:","Resists:","Weak to:","Very weak to:"))[0]
        pkmn_info.update({'Movepool': self.tree.xpath('//div[contains(@class,"DexTable")]/div[contains(@class,"MoveRow")]/div[contains(@class,"MoveRow-name")]/a/text()')})
        return pkmn_info

    def get_pkmn_tier(self,tier_div):
        tier=tier_div.xpath('./ul/li/a/text()')
        if len(tier)!=1:
            return 'Untiered'
        else:
            return tier[0]

    def get_pkmns(self,genurl):
        res = makehash()
        url = self.url + genurl + "/pokemon/"
        self.driver.get(url)
        max_height = self.driver.execute_script("return document.body.scrollHeight")
        previous = 0
        pkmns=[]
        for y in tqdm.tqdm(range(0,max_height,100),desc='Listing all pokemons for current gen'):
            self.driver.execute_script("window.scrollTo(" + str(previous) + ", " + str(y) + ")")
            self.tree = html.fromstring(self.driver.page_source)
            pkmns = pkmns + [x for x in self.tree.xpath(
                '//div[contains(@class,"DexTable")]/div[contains(@class,"PokemonAltRow")]')
                             if x.xpath(
                    './div[contains(@class,"PokemonAltRow-name")]/a/span/span[not(contains(@class,"PokemonSprite"))]/text()')[
                                 0] not in [pkmn.xpath(
                    './div[contains(@class,"PokemonAltRow-name")]/a/span/span[not(contains(@class,"PokemonSprite"))]/text()')[0]
                                            for pkmn in pkmns]]
            previous = y

        [makehash_update(res, [self.get_pkmn_tier(pkmn.xpath(
            './div[contains(@class,"PokemonAltRow-tags")]')[0]), pkmn.xpath(
            './div[contains(@class,"PokemonAltRow-name")]/a/span/span[not(contains(@class,"PokemonSprite"))]/text()')[
                                   0]], self.get_pkmn_info(self.url + pkmn.xpath(
            './div[contains(@class,"PokemonAltRow-name")]/a/@href')[0], split_pkmn_form(pkmn.xpath(
            './div[contains(@class,"PokemonAltRow-name")]/a/span/span[not(contains(@class,"PokemonSprite"))]/text()')[
                                                                                            0], "-", 1))) for pkmn in
         tqdm.tqdm(pkmns, desc='Getting pokemon information for current gen')]

        return res

    def get_all_pkmns(self,folder):
        all_pkmns=dict()
        if os.path.exists(os.path.join(folder, 'pkmns.json')):
            os.remove(os.path.join(folder, 'pkmns.json'))
        url = self.url +"/dex/"
        self.driver.get(url)
        self.tree = html.fromstring(self.driver.page_source)
        gens=self.tree.xpath('//div[@id="body"]/div[@id="front_top"]/following-sibling::ul//a/@href')
        gens=[['gen'+str(num_gen-i),gen.replace('/pokemon/','')] for i,gen in enumerate(gens)]
        [all_pkmns.update({gen[0]:self.get_pkmns(gen[1])}) for gen in tqdm.tqdm(gens, desc='Getting pokemons for all gens')]
        write_json_dict(folder, 'pkmns.json',all_pkmns)