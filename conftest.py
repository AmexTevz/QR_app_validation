import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.safari.service import Service as SafariService
from webdriver_manager.chrome import ChromeDriverManager
import platform

# Move necessary constants here
BROWSER_OPTIONS = {
    'chrome': {
        'default': [
            '--start-maximized',
            '--disable-extensions',
            '--disable-popup-blocking',
            '--disable-infobars'
        ]
    }
}

TIMEOUTS = {
    'implicit': 10,
    'page_load': 30
}

def is_mac():
    return platform.system() == 'Darwin'

@pytest.fixture(scope="session")
def driver():
    if is_mac():
        # Safari setup
        service = SafariService()
        driver = webdriver.Safari(service=service)
        driver.maximize_window()
    else:
        # Chrome setup with webdriver manager
        options = ChromeOptions()
        for option in BROWSER_OPTIONS['chrome']['default']:
            options.add_argument(option)
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()), 
            options=options
        )
    
    # Set common timeouts
    driver.implicitly_wait(TIMEOUTS['implicit'])
    driver.set_page_load_timeout(TIMEOUTS['page_load'])
    driver.set_script_timeout(TIMEOUTS['page_load'])
    driver.maximize_window()
    yield driver
    
    driver.quit()


