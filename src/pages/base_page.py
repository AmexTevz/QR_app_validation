from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import logging
from selenium.webdriver.remote.webelement import WebElement
from typing import Union, List, Tuple
import os



class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.actions = ActionChains(self.driver)
        self.logger = logging.getLogger(__name__)
        self.store_id = None

    def take_screenshot(self, store_id, item_name, sub_folder=None):

        try:
            from src.utils.constants import SCREENSHOTS_DIR

            timestamp = datetime.now().strftime('%H_%M')

            safe_store_id = str(store_id).replace('/', '_').replace('\\', '_')
            safe_item_name = "".join(c for c in str(item_name) if c.isalnum() or c in (' ', '-', '_')).strip()

            filename = f"{safe_store_id}_{safe_item_name}_{timestamp}.png"

            if sub_folder:
                directory = os.path.join(SCREENSHOTS_DIR, sub_folder)
                os.makedirs(directory, exist_ok=True)
            else:
                directory = SCREENSHOTS_DIR

            filepath = os.path.join(directory, filename)

            abs_filepath = os.path.abspath(filepath)

            self.driver.save_screenshot(abs_filepath)
            print(f"\nScreenshot saved: {abs_filepath}")
            
        except Exception as e:
            print(f"Failed to take screenshot: {str(e)}")


    def send_keys(self, locator, text, clear=True, name=None):
        logging.info(f"Attempting to send keys to element: {name if name else locator}")
        try:
            element = self.wait.until(EC.presence_of_element_located(locator))
            try:
                if clear:
                    element.clear()
                element.send_keys(text)
                logging.info(f"Successfully sent keys using regular method: {name if name else locator}")
                return element
            except Exception as e:
                logging.info(f"Regular send_keys failed: {str(e)}")

            try:
                if clear:
                    self.driver.execute_script("arguments[0].value = '';", element)
                self.driver.execute_script(f"arguments[0].value = arguments[1];", element, text)
                logging.info(f"Successfully sent keys using JavaScript: {name if name else locator}")
                return element
            except Exception as e:
                logging.info(f"JavaScript send_keys failed: {str(e)}")

            try:
                actions = ActionChains(self.driver)
                if clear:
                    actions.click(element).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(
                        Keys.BACK_SPACE)
                actions.send_keys(text).perform()
                logging.info(f"Successfully sent keys using ActionChains: {name if name else locator}")
                return element
            except Exception as e:
                logging.error(f"All send_keys attempts failed: {str(e)}")
                raise

        except Exception as e:
            logging.error(f"Failed to interact with element {name if name else locator}: {str(e)}")
            raise

    def get_text(self, locator, name=None, element=None):
        logging.info(f"Attempting to get text from element: {name if name else locator}")
        try:
            if element is None:
                element = self.wait.until(EC.presence_of_element_located(locator))

            try:
                text = element.text
                if text:
                    logging.info(f"Successfully got text using regular method: {text}")
                    return text
            except Exception as e:
                logging.info(f"Regular text failed: {str(e)}")

            try:
                text = element.get_attribute('textContent')
                if text:
                    logging.info(f"Successfully got text using textContent: {text}")
                    return text
            except Exception as e:
                logging.info(f"textContent failed: {str(e)}")

            try:
                text = self.driver.execute_script("return arguments[0].innerText;", element)
                if text:
                    logging.info(f"Successfully got text using JavaScript: {text}")
                    return text.strip()
            except Exception as e:
                logging.error(f"All text retrieval attempts failed: {str(e)}")
                raise

        except Exception as e:
            logging.error(f"Failed to get text from element {name if name else locator}: {str(e)}")
            raise

    def is_element_displayed(self, locator, timeout=3):
        try:
            elements = self.driver.find_elements(*locator)
            if elements and elements[0].is_displayed():
                return True

            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except:
            return False

    def wait_for_url_contains(self, partial_url, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.url_contains(partial_url)
            )
            logging.info(f"URL contains '{partial_url}'")
            return True
        except TimeoutException:
            logging.error(f"URL does not contain '{partial_url}' within {timeout} seconds")
            return False

    def get_elements(self, *locators):
        for locator in locators:
            elements = self.driver.find_elements(*locator)
            if elements:
                return elements
        return []

    def wait_for_elements(self, locator, timeout=3):
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_all_elements_located(locator))

    def click(self, target: Union[WebElement, Tuple[str, str]], name=None):
        try:
            if isinstance(target, tuple):
                element = self.wait.until(EC.presence_of_element_located(target))
            else:
                element = target
                
            try:
                element.click()
                return element
            except Exception as e:
                logging.info(f"Regular click failed, trying alternative methods: {str(e)}")

            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                self.driver.execute_script("arguments[0].click();", element)
                logging.info(f"Successfully clicked element using JavaScript: {name if name else target}")
                return element
            except Exception as e:
                logging.info(f"JavaScript click failed, trying ActionChains: {str(e)}")

            try:
                actions = ActionChains(self.driver)
                actions.move_to_element(element).click().perform()
                logging.info(f"Successfully clicked element using ActionChains: {name if name else target}")
                return element
            except Exception as e:
                logging.error(f"All click attempts failed for {name if name else target}: {str(e)}")
                raise

        except Exception as e:
            logging.error(f"Failed to interact with element {name if name else target}: {str(e)}")
            raise

    def wait_for_element_visible(self, locator: Tuple[str, str], timeout: int = 10) -> WebElement:

        wait = WebDriverWait(self.driver, timeout, poll_frequency=0.5)
        return wait.until(
            EC.visibility_of_element_located(locator)
        )

    def is_element_present(self, locator: Tuple[str, str]) -> bool:
        try:
            self.wait_for_element_visible(locator)
            return True
        except:
            return False

    def get_elements_alt(self, *locators: Tuple[str, str]) -> List[WebElement]:
        for locator in locators:
            elements = self.driver.find_elements(*locator)
            if elements:
                return elements
        return []

    def wait_for_element_to_disappear(self, locator, timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    def switch_to_frame(self, locator):
        frame = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located(locator))
        self.driver.switch_to.frame(frame)

    def switch_to_default_content(self):
        self.driver.switch_to.default_content()

