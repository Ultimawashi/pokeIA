from lxml import html
from selenium import webdriver
from exceptions import *
import time
import tqdm
import json
import os

num_gen=7

def write_json_dict(folder,filename,data):
    if os.path.exists(os.path.join(folder, filename)):
        flag='a'
    else:
        flag='w'
    with open(os.path.join(folder, filename), flag) as outfile:
        json.dump(data, outfile)

class Smogon():
    BASE_URL = "https://www.smogon.com"
    def __init__(self, url=BASE_URL, browser='chrome',
                 driver_dir="D:/projetsIA/Pokai/driver/chromedriver.exe"):
        self.url = url
        self.browser = browser
        assert self.browser in ["firefox",
                                "chrome"], "please choose a valid browser (only chrome or firefox are supported)"
        self.tree = None
        if browser == "firefox":
            self.driver = webdriver.Firefox(executable_path=driver_dir)
        elif browser == "chrome":
            self.driver = webdriver.Chrome(executable_path=driver_dir)


    def get_all_moves(self,folder):
        url = self.url +"/dex/"
        self.driver.get(url)
        self.tree = html.fromstring(self.driver.page_source)
        gens=self.tree.xpath('//div[@id="body"]/div[@id="front_top"]/following-sibling::ul//a/@href')
        gens=[['gen'+str(num_gen-i),gen.replace('/pokemon/','')] for i,gen in enumerate(gens)]
        [write_json_dict(folder,'moves.json',{gen[0]:self.get_moves(gen[1])}) for gen in tqdm.tqdm(gens, desc='Getting moves for all gens')]

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
        keys = self.tree.xpath('//table[contains(@class,"MoveInfo")]//th/text()')
        [move_info.update(self.get_following(key)) for key in keys]
        move_info.update({'Desc': self.tree.xpath('//main[contains(@class,"DexContent")]/div/p[1]/text()')[0]})
        flags=self.tree.xpath('//main[contains(@class,"DexContent")]/div/p[2]/span[contains(text(),":")]/following-sibling::span/text()')
        if len(flags)>0:
            move_info.update({'Flags': flags[0].split(", ")})
        else:
            move_info.update({'Flags': ""})
        return (move_info)

    def get_following(self,key):
        value = self.tree.xpath(
            '//th[contains(text(),"' + key + '")]/following-sibling::td/*/text()|//th[contains(text(),"' + key + '")]/following-sibling::td/text()')
        return {key: value[0]}

    def get_all_items(self,folder):
        url = self.url +"/dex/"
        self.driver.get(url)
        self.tree = html.fromstring(self.driver.page_source)
        gens=self.tree.xpath('//div[@id="body"]/div[@id="front_top"]/following-sibling::ul//a/@href')
        gens=[['gen'+str(num_gen-i),gen.replace('/pokemon/','')] for i,gen in enumerate(gens)]
        [write_json_dict(folder,'items.json',{gen[0]:self.get_items(gen[1])}) for gen in tqdm.tqdm(gens, desc='Getting items for all gens')]

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
        url = self.url +"/dex/"
        self.driver.get(url)
        self.tree = html.fromstring(self.driver.page_source)
        gens=self.tree.xpath('//div[@id="body"]/div[@id="front_top"]/following-sibling::ul//a/@href')
        gens=[['gen'+str(num_gen-i),gen.replace('/pokemon/','')] for i,gen in enumerate(gens)]
        [write_json_dict(folder,'abilities.json',{gen[0]:self.get_abilities(gen[1])}) for gen in tqdm.tqdm(gens, desc='Getting abilities for all gens')]

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
