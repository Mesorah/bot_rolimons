from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import threading
import winsound
import json
import time


class Configuration:
    def __init__(self):
        with open('infs.json', 'r') as json_file:
            self.data = json.load(json_file)

        (self.file_path_to_chrome, self.verification_time,
         self.deal, self.wait_to_close,
         self.automatic_mode) = self.data[0].values()

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


class RolimonsDealBot(BaseBot):
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

            try:
                self.first_item_price = int(self.first_item_price)
            except ValueError:
                self.first_item_price = 99999999999

            return (self.first_item_title, self.first_item,
                    self.number_of_items, self.first_item_price)

        return None, None, self.number_of_items, None


class BotBuyItem(BaseBot):
    def __init__(self, driver, allowed_itens,
                 first_item_title, first_item_price):

        super().__init__(driver)

        self.allowed_itens = allowed_itens
        self.first_item_title = first_item_title
        self.first_item_price = first_item_price

    def verify_if_windows_is_changed(self, original_window):
        for window_handle in self.driver.window_handles:
            if window_handle != original_window:
                self.driver.switch_to.window(window_handle)
                return

    def buy_button(self):
        self.click_element_with_delay(10,
                                      By.XPATH,
                                      "//button[contains(text(), 'Comprar')]",
                                      False)

        # text_robux = (self.driver.find_element(
        #        By.CSS_SELECTOR,
        #        ".text-robux"))

        # text_robux = text_robux.text.replace(",", "").replace(".", "")

        # last_item_price = int(text_robux)

        # print(last_item_price)

        # return last_item_price

    def close_window(self, first_item_title, first_item_price):
        window_handles = self.driver.window_handles

        self.driver.switch_to.window(window_handles[1])
        self.driver.close()
        self.driver.switch_to.window(window_handles[0])

        self.first_item_title = first_item_title
        self.first_item_price = first_item_price

    def buy_item(self):
        self.click_element_with_delay(
            10, By.XPATH, "//button[contains(text(), 'Comprar agora')]", False)

        return True

    def if_automatic_mode_is_true(self, first_item_title, first_item_price):
        for item_name, item_data in self.allowed_itens.items():
            self.min_robux = item_data.get('min_robux')
            if item_name != first_item_title:
                if first_item_price <= self.min_robux:
                    try:
                        self.buy_item()

                    except Exception as e:
                        print(f"Erro ao clicar no buy button: {e}")

    @staticmethod
    def play_sound():
        winsound.Beep(1000, 500)

    @staticmethod
    def play_sound_thread():
        thread = threading.Thread(target=BotBuyItem.play_sound)
        thread.start()


configuration = Configuration()

chrome_options = ConfigureChromeOptions(
    configuration.file_path_to_chrome).chrome_options

rolimons_deal_bot = RolimonsDealBot(configuration.deal, chrome_options)


first_item_title, _, _, first_item_price = rolimons_deal_bot.get_first_item()

bot_buy_item = BotBuyItem(rolimons_deal_bot.driver,
                          configuration.allowed_itens,
                          first_item_title,
                          first_item_price)


try:
    rolimons_deal_bot.click_to_deals_bellow()
    rolimons_deal_bot.click_on_specific_deals()

    (title, item, initial_number_of_items,
     first_item_price) = rolimons_deal_bot.get_first_item()

    while True:
        time.sleep(configuration.verification_time)

        try:
            (first_item_title,
             first_item_element,
             number_of_items,
             first_item_price) = rolimons_deal_bot.get_first_item()
        except StaleElementReferenceException:
            (first_item_title,
             first_item_element,
             number_of_items,
             first_item_price) = rolimons_deal_bot.get_first_item()
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
            continue

        if initial_number_of_items < number_of_items:
            initial_number_of_items = number_of_items

        else:
            if first_item_title:
                if first_item_title != title:
                    print('Robux lançado inicialmente', first_item_price)

                    try:
                        first_item_element.click()
                    except Exception as e:
                        print('erro no click', e)

                    original_window = (rolimons_deal_bot
                                       .driver.current_window_handle)

                    bot_buy_item.verify_if_windows_is_changed(original_window)

                    bot_buy_item.play_sound_thread()

                    try:
                        bot_buy_item.buy_button()

                        if configuration.automatic_mode:
                            bot_buy_item.if_automatic_mode_is_true(
                                first_item_title, first_item_price)

                        time.sleep(configuration.wait_to_close)

                        try:
                            bot_buy_item.close_window(first_item_title,
                                                      first_item_price)
                        except Exception as e:
                            print('erro ao fechar a janela', e)

                        (title, item, initial_number_of_items,
                            first_item_price) = (rolimons_deal_bot.
                                                 get_first_item())

                    except Exception as e:
                        print(f"Erro ao clicar no buy button: {e}")

                # print(f"O primeiro item é: {first_item_title}")

except Exception as e:
    print("Ocorreu um erro no bloco principal:", e)

finally:
    rolimons_deal_bot.driver.quit()
