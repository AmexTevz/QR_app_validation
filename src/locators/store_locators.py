from selenium.webdriver.common.by import By

class CommonLocators:
    POSTAL_CODE_LABEL = (By.XPATH, "//label[@for='PostalCode']")
    POSTAL_CODE_FIELD = (By.CSS_SELECTOR, 'input#PostalCode')
    GOOGLE_PAY_BUTTON = (By.CSS_SELECTOR, "div#googlePay")
    TIMER = (By.CSS_SELECTOR, "span#timerText")
    STORE_NAME = (By.CSS_SELECTOR, "h1.navbar-store")

class SafariLocators:
    APPLE_PAY_BUTTON = (By.CSS_SELECTOR, "div#applePay")






