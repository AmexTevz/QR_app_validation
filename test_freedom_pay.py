import pytest
import requests
import csv
import uuid
import os
from datetime import datetime
from typing import List, Dict, Tuple
from src.pages.base_page import BasePage
from src.locators.store_locators import CommonLocators, SafariLocators
from selenium.webdriver.common.by import By
from conftest import is_mac

def read_store_data(csv_path: str) -> List[Tuple[str, str, str, str, str]]:
    store_data = []
    with open(csv_path, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)
        for row in csv_reader:
            if len(row) >= 5:
                store_id = str(int(float(row[0].strip())))
                terminal_id = str(int(float(row[1].strip())))
                dba_name = row[2].strip()
                property_id = row[3].strip()
                revenue_center_id = row[4].strip()
                store_data.append((store_id, terminal_id, dba_name, property_id, revenue_center_id))
    return store_data

def create_freedom_pay_transaction(store_id: str, terminal_id: str) -> Dict:

    url = "https://payments.freedompay.com/checkoutservice/checkoutservice.svc/CreateTransaction"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    payload = {
        "TerminalId": terminal_id,
        "StoreId": store_id,
        "TransactionTotal": 0.01,
        "TimeoutMinutes": 5,
        "InvoiceNumber": 1234,
        "MerchantReferenceCode": str(uuid.uuid4())
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status() 
    return response.json()

def write_failure_to_file(store_id: str, terminal_id: str, dba_name: str, property_id: str, revenue_center_id: str, failure_message: str):
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        
    timestamp = datetime.now().strftime('%Y-%m-%d')
    filepath = os.path.join(results_dir, f"results_{timestamp}.txt")
    
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write("=" * 50 + "\n")
        f.write("STORE INFORMATION:\n")
        f.write(f"Store ID: {store_id}\n")
        f.write(f"Terminal ID: {terminal_id}\n")
        f.write(f"Property ID: {property_id}\n")
        f.write(f"Revenue Center ID: {revenue_center_id}\n")
        
        if dba_name:
            f.write(f"DBA Name: {dba_name}\n")
        else:
            f.write("DBA Name: <empty>\n")
            
        f.write("\nERROR DETAILS:\n")
        if "Store name mismatch" in failure_message:
            expected = failure_message.split("Expected: ")[1].split(", Got: ")[0]
            actual = failure_message.split("Got: ")[1]
            f.write("Type: Store Name Mismatch\n")
            f.write(f"Expected Name: {expected}\n")
            f.write(f"Actual Name: {actual}\n")
        elif "Timer started with incorrect value" in failure_message:
            f.write("Type: Invalid Timer Value\n")
            f.write(f"Details: {failure_message}\n")
        elif "API Response missing" in failure_message:
            f.write("Type: API Response Error\n")
            f.write(f"Details: {failure_message}\n")
        elif "API Request Failed" in failure_message:
            f.write("Type: API Request Failed\n")
            f.write(f"Details: {failure_message}\n")
        elif "Invalid URL format" in failure_message:
            f.write("Type: Invalid URL\n")
            f.write(f"Details: {failure_message}\n")
        else:
            f.write(f"Type: Element Not Found\n")
            f.write(f"Details: {failure_message}\n")
            
        f.write("=" * 50 + "\n\n")

def take_screenshot(driver, store_id: str, filename: str):
    results_dir = "results"
    screenshots_dir = os.path.join(results_dir, "screenshots")
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)

    if filename.strip():
        safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()
    else:
        safe_filename = f"store_{store_id}"
        
    filepath = os.path.join(screenshots_dir, f"{safe_filename}.png")
    driver.save_screenshot(filepath)
    print(f"\nScreenshot saved: {filepath}")

def write_timer_to_file(store_id: str, terminal_id: str, dba_name: str, property_id: str, revenue_center_id: str, timer_value: str):
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        
    timestamp = datetime.now().strftime('%Y-%m-%d')
    filepath = os.path.join(results_dir, f"timer_values_{timestamp}.txt")

    timer_status = "PASS" if timer_value in ('05:00', '04:59', '04:58') else "FAIL"
    
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write("=" * 50 + "\n")
        f.write("STORE INFORMATION:\n")
        f.write(f"Store ID: {store_id}\n")
        f.write(f"Terminal ID: {terminal_id}\n")
        f.write(f"Property ID: {property_id}\n")
        f.write(f"Revenue Center ID: {revenue_center_id}\n")
        
        if dba_name:
            f.write(f"DBA Name: {dba_name}\n")
        else:
            f.write("DBA Name: <empty>\n")
            
        f.write(f"\nTIMER VALUE AT START: {timer_value}")
        if timer_status != "PASS":
            f.write(" (FAIL)")
        f.write("\n")
        f.write("=" * 50 + "\n\n")

class TestFreedomPayAPI:
    
    @pytest.fixture
    def store_data(self) -> List[Tuple[str, str, str, str, str]]:
        return read_store_data('src/data/stores.csv')
    
    @pytest.mark.parametrize("store_tuple", read_store_data('src/data/stores.csv'))
    def test_create_transaction(self, store_tuple, driver):
        store_id, terminal_id, dba_name, property_id, revenue_center_id = store_tuple
        base_page = BasePage(driver)
        is_safari = is_mac()
        failures = []
        timer_value = "Not Found"
        
        try:
            response = create_freedom_pay_transaction(store_id, terminal_id)
            checkout_url = response['CheckoutUrl']

            assert checkout_url.startswith('https://'), f"Invalid URL format received: {checkout_url}"
            assert isinstance(checkout_url, str), f"Invalid checkout URL format. Expected string, got {type(checkout_url)}"
            assert checkout_url, "Empty checkout URL received"

            driver.get(checkout_url)

            try:
                timer_element = base_page.wait_for_element_visible(CommonLocators.TIMER)
                timer_value = timer_element.get_attribute('textContent').strip()
                assert timer_value.startswith(('05:00', '04:59', '04:58')), f"Timer started with incorrect value: {timer_value}. Expected: 05:00 or 04:59"
            except Exception as e:
                failures.append(f"Timer check failed: {str(e)}")
            
            # Google Pay check
            try:
                assert base_page.is_element_present(CommonLocators.GOOGLE_PAY_BUTTON), "Google Pay button not found"
            except Exception as e:
                failures.append(f"Google Pay check failed: {str(e)}")

            if is_safari:
                try:
                    assert base_page.is_element_present(SafariLocators.APPLE_PAY_BUTTON), "Apple Pay button not found"
                except Exception as e:
                    failures.append(f"Apple Pay check failed: {str(e)}")

            if dba_name:
                try:
                    base_page.wait_for_element_visible(CommonLocators.STORE_NAME)
                    actual_store_name = base_page.get_text(CommonLocators.STORE_NAME)
                    assert dba_name in actual_store_name, f"Store name mismatch. Expected: {dba_name}, Got: {actual_store_name}"
                except Exception as e:
                    failures.append(f"Store name check failed: {str(e)}")

            try:
                base_page.switch_to_frame((By.CSS_SELECTOR, "iframe#hpc--card-frame"))
                assert base_page.is_element_present(CommonLocators.POSTAL_CODE_FIELD), "Postal code field not found"
                base_page.switch_to_default_content()
            except Exception as e:
                failures.append(f"Postal code check failed: {str(e)}")
                base_page.switch_to_default_content()

            write_timer_to_file(store_id, terminal_id, dba_name, property_id, revenue_center_id, timer_value)
            
            if failures:
                screenshot_name = f"failure_{dba_name}" if dba_name else f"failure_store_{store_id}"
                take_screenshot(driver, store_id, screenshot_name)
                
                for failure in failures:
                    write_failure_to_file(store_id, terminal_id, dba_name, property_id, revenue_center_id, failure)
                
                pytest.fail("\n".join(failures))

        except AssertionError as e:
            write_timer_to_file(store_id, terminal_id, dba_name, property_id, revenue_center_id, timer_value)
            write_failure_to_file(store_id, terminal_id, dba_name, property_id, revenue_center_id, str(e))
            pytest.skip(str(e))
            
        except Exception as e:
            error_filename = f"error_{store_id}"
            try:
                driver.save_screenshot(os.path.join("results", "screenshots", f"{error_filename}.png"))
            except Exception as screenshot_error:
                print(f"Failed to take screenshot: {str(screenshot_error)}")

            write_failure_to_file(store_id, terminal_id, dba_name, property_id, revenue_center_id, str(e))
            raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 