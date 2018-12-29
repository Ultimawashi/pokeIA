import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException


#220
#messagebar message

class if_elem_is_not_value(object):

  def __init__(self,value,elem):
    self.value = value
    self.elem = elem
  def __call__(self, driver):
    turn = self.elem.find_element(*(By.CLASS_NAME, "turn"))   # Finding the referenced element
    if self.value != turn.get_attribute('innerHTML'):
        return True
    else:
        return False

class if_connected_search_battle(object):

  def __init__(self,username):
    self.username = username

  def __call__(self, driver):
    user = driver.find_element(*(By.CLASS_NAME, "username"))   # Finding the referenced element
    button = driver.find_element(*(By.NAME, "search"))
    if self.username in user.get_attribute('innerHTML'):
        return button
    else:
        return False

class get_launched_battle(object):
  """An expectation for checking that an element has a particular css class.

  locator - used to find the element
  returns the WebElement once it has the particular css class
  """
  def __init__(self):
    self.css_class1 = 'disabled'
    self.css_class2 = 'inner'

  def __call__(self, driver):
    panel = driver.find_element(*(By.NAME, "search"))   # Finding the referenced element
    if self.css_class1 not in panel.get_attribute("class"):
        battlerooms = ((driver.find_element_by_class_name(self.css_class2)).find_elements_by_tag_name("ul")[1]).find_elements_by_tag_name("li")
        current_battle_panel = (battlerooms[len(battlerooms)-1]).find_element_by_tag_name("button")
        battle_id = current_battle_panel.get_attribute('value')
        current_battle = driver.find_element_by_id('room-'+battle_id)
        return [current_battle_panel,current_battle]
    else:
        return False

driver = webdriver.Chrome('D:/projetsIA/pokeIA/driver/chromedriver.exe')
driver.get("https://play.pokemonshowdown.com")


elem = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, "login"))
)
elem.send_keys(Keys.RETURN)
elem = driver.find_element_by_name("username")
elem.send_keys("iamabot447")
elem.submit()

elem = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, "password"))
)
elem.send_keys("projectia21")
elem.submit()
elem = WebDriverWait(driver, 10).until(
    if_connected_search_battle("iamabot447")
)
elem.click()
elem = WebDriverWait(driver, 10).until(
    get_launched_battle()
)
timer = WebDriverWait(elem[1], 10).until(
        EC.presence_of_element_located((By.NAME, "openTimer"))
    )
timer.click()
timer = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "timerOn"))
    )
timer.click()

while not elem[1].find_element_by_class_name("message").find_element_by_tag_name("p").get_attribute('innerHTML').endswith('won the battle!<br>'):
    turn = WebDriverWait(elem[1], 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "turn"))
    )
    turn = turn.get_attribute('innerHTML')
    try:
        moves = WebDriverWait(elem[1], 20).until(
            EC.presence_of_all_elements_located((By.NAME, "chooseMove"))
        )
    except TimeoutException:
        moves=[]
    try:
        switches = WebDriverWait(elem[1], 20).until(
            EC.presence_of_all_elements_located((By.NAME, "chooseSwitch"))
        )
    except TimeoutException:
        switches=[]

    actions = moves + switches

    if len(actions) > 0:
        actions[random.randint(0,len(actions)-1)].click()

    try:
        moves = WebDriverWait(elem[1], 20).until(
            EC.presence_of_all_elements_located((By.NAME, "chooseMove"))
        )
    except TimeoutException:
        moves=[]
    try:
        switches = WebDriverWait(elem[1], 20).until(
            EC.presence_of_all_elements_located((By.NAME, "chooseSwitch"))
        )
    except TimeoutException:
        switches=[]

    actions = moves + switches

    if len(actions) > 0:
        actions[random.randint(0,len(actions)-1)].click()

    try:
        WebDriverWait(elem[1], 220).until(
            if_elem_is_not_value(turn,elem[1])
        )
    except TimeoutException:
        pass


elem[0].click()

