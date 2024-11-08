from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import time


class Configuration:
    def __init__(self):
        with open('bot_rolimons/bot_rolimons/infs.json', 'r') as json_file:
            self.data = json.load(json_file)

        (self.file_path_to_chrome, self.verification_time,
         self.deal, self.automatic_mode) = self.data[0].values()

        self.allowed_itens = self.data[1]['allowed_itens']


class ConfigureChromeOptions:
    def __init__(self, file_path_to_chrome):
        self.chrome_options = Options()
        self.chrome_options.add_argument(file_path_to_chrome)
        self.chrome_options.add_argument("profile-directory=Default")
        self.chrome_options.add_argument(
            "--blink-settings=imagesEnabled=false")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-gpu")


class BaseBot:
    def __init__(self, driver):
        self.driver = driver

    def click_element_with_delay(self, driver_time,
                                 by, item_name, sleep=False):
        dropdown = WebDriverWait(self.driver, driver_time).until(
            EC.element_to_be_clickable((by, item_name)))
        dropdown.click()
        if sleep:
            time.sleep(sleep)


class BotRolimons(BaseBot):
    def __init__(self, deal, chrome_options):
        self.driver = webdriver.Chrome(options=chrome_options)
        super().__init__(self.driver)
        self.deal = deal
        self.driver.get("https://www.rolimons.com/deals")

    def click_to_deals_bellow(self):
        self.click_element_with_delay(
            10, By.ID, 'filter-category-dropdown-text', 0.01)

    def click_on_specific_deals(self):
        self.click_element_with_delay(
            10, By.XPATH,
            f"//a[@class='dropdown-item' and text()='{self.deal}%']", 0.25)

    def get_first_item(self):
        self.items = self.driver.find_elements(By.CSS_SELECTOR, ".mix_item")
        self.number_of_items = len(self.items)

        if self.items:
            self.first_item = self.items[0]
            self.first_item_title = self.first_item.find_element(
                By.CLASS_NAME, "deal-title").text

            self.first_item_price = (self.driver.find_element(
                By.CSS_SELECTOR,
                ".stat-data.text-light.text-truncate").text.replace(",", ""))

            return (self.first_item_title, self.first_item,
                    self.number_of_items, int(self.first_item_price))

        return None, None, self.number_of_items, None


class BotBuyItem(BaseBot):
    def __init__(self, driver, allowed_itens,
                 first_item_title, first_item_price):

        super().__init__(driver)

        self.allowed_itens = allowed_itens
        self.first_item_title = first_item_title
        self.first_item_price = first_item_price

    def click_element_with_delay(self,
                                 driver_time, by, item_name, sleep=False):

        self.dropdown = WebDriverWait(self.driver, driver_time).until(
            EC.element_to_be_clickable((by, item_name)))
        self.dropdown.click()

        if sleep:
            return time.sleep(sleep)

        return

    def verify_if_windows_is_changed(self, original_window):
        for window_handle in self.driver.window_handles:
            if window_handle != original_window:
                self.driver.switch_to.window(window_handle)
                return

    def buy_button(self):
        self.click_element_with_delay(
            10, By.XPATH, "//button[contains(text(), 'Comprar')]", False)

        return True

    def buy_item(self):
        self.click_element_with_delay(
            10, By.XPATH, "//button[contains(text(), 'Comprar agora')]", False)

        return True

    def if_automatic_mode_is_true(self):
        for item_name, item_data in self.allowed_itens.items():
            self.min_robux = item_data.get('min_robux')
            if item_name != self.first_item_title:
                if self.first_item_price <= self.min_robux:
                    try:
                        self.buy_item()

                    except Exception as e:
                        print(f"Erro ao clicar no buy button: {e}")


configuration = Configuration()

chrome_options = ConfigureChromeOptions(
    configuration.file_path_to_chrome).chrome_options

bot_rolimons = BotRolimons(configuration.deal, chrome_options)


first_item_title, _, _, first_item_price = bot_rolimons.get_first_item()

bot_buy_item = BotBuyItem(bot_rolimons.driver,
                          configuration.allowed_itens,
                          first_item_title,
                          first_item_price)

try:
    bot_rolimons.click_to_deals_bellow()
    bot_rolimons.click_on_specific_deals()

    (title, item, initial_number_of_items,
     first_item_price) = bot_rolimons.get_first_item()

    while True:
        time.sleep(configuration.verification_time)
        (first_item_title, first_item_element,
         number_of_items, first_item_price) = bot_rolimons.get_first_item()

        if initial_number_of_items < number_of_items:
            initial_number_of_items = number_of_items

        else:
            if first_item_title:
                if first_item_title != title:
                    first_item_element.click()

                    original_window = bot_rolimons.driver.current_window_handle

                    bot_buy_item.verify_if_windows_is_changed(original_window)

                    try:
                        bot_buy_item.buy_button()

                        if configuration.automatic_mode:
                            bot_buy_item.if_automatic_mode_is_true(
                                first_item_title, first_item_price)

                    except Exception as e:
                        print(f"Erro ao clicar no buy button: {e}")

                print(f"O primeiro item é: {first_item_title}")

except Exception as e:
    print("Ocorreu um erro no bloco principal:", e)

finally:
    bot_rolimons.driver.quit()
