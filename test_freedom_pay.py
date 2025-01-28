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

def read_store_data(csv_path: str) -> List[Tuple[str, str, str, str, str, str, str, str]]:
    store_data = []
    with open(csv_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header row
        for row in csv_reader:
            try:
                if len(row) >= 8:  # Check we have all required columns
                    batch = row[0].strip()  # Batch is now first column
                    store_id = str(int(float(row[1].strip())))  # Store ID is second column
                    terminal_id = str(int(float(row[2].strip())))  # Terminal ID is third column
                    property_id = row[3].strip()
                    revenue_center_id = row[4].strip()
                    location_name = row[5].strip()
                    revenue_center_name = row[6].strip()
                    dba_name = row[7].strip()
                    
                    print(f"\nValidating store data:")
                    print(f"Batch: {batch}")
                    print(f"Store ID: {store_id} (original: {row[1]})")
                    print(f"Terminal ID: {terminal_id} (original: {row[2]})")
                    
                    store_data.append((
                        store_id,
                        terminal_id,
                        property_id,
                        revenue_center_id,
                        location_name,
                        revenue_center_name,
                        dba_name,
                        batch
                    ))
            except Exception as e:
                print(f"Error processing row: {row}")
                print(f"Error: {str(e)}")
                continue
                
    if not store_data:
        raise ValueError("No valid data found in stores.csv")
        
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
    
    print(f"\nMaking API request for Store {store_id}:")
    print(f"URL: {url}")
    print(f"Payload: {payload}")
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    
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
        if "Store not configured" in failure_message:
            f.write("Type: Store Configuration Error\n")
            f.write(f"Details: {failure_message}\n")
        elif "Store name mismatch" in failure_message:
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

    timer_status = "PASS" if timer_value in ('05:00', '04:59') else "FAIL"
    
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

def write_results_to_csv(store_id: str, terminal_id: str, property_id: str, revenue_center_id: str, 
                        location_name: str, revenue_center_name: str, dba_name: str, 
                        results: Dict[str, bool], timer_value: str, batch: str):
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        
    timestamp = datetime.now().strftime('%Y-%m-%d')
    filepath = os.path.join(results_dir, f"test_results_{timestamp}.csv")
    
    # Define headers
    headers = [
        'Batch',
        'Store ID',
        'Terminal ID',
        'Property ID',
        'RVC ID',
        'Location Name',
        'RVC Name',
        'DBA Name',
        'Timer',
        'Timer at Launch',
        'GooglePay',
        'ApplePay',
        'DB Name Match',
        'Postal Code'
    ]
    
    # Write headers if file doesn't exist
    if not os.path.exists(filepath):
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    if not dba_name or dba_name.strip() == "" or dba_name.strip() == "N/A":
        dba_name_value = "N/A"
        db_name_status = "N/A"
    else:
        dba_name_value = dba_name
        db_name_status = "PASS" if results.get('store_name_match', False) else "FAIL"

    # Special handling for invalid URL cases
    if "Invalid URL" in timer_value:
        row = [
            batch,  # Batch number is first
            store_id,
            terminal_id,
            property_id,
            revenue_center_id,
            location_name,
            revenue_center_name,
            dba_name_value,
            'FAIL',
            timer_value,
            'N/A',
            'N/A',
            db_name_status,
            'N/A'
        ]
    else:
        row = [
            batch,  # Batch number is first
            store_id,
            terminal_id,
            property_id,
            revenue_center_id,
            location_name,
            revenue_center_name,
            dba_name_value,
            'PASS' if results.get('timer_present', False) else 'FAIL',
            timer_value,
            'PASS' if results.get('googlepay_present', False) else 'FAIL',
            'PASS' if results.get('applepay_present', False) else 'FAIL',
            db_name_status,
            'PASS' if results.get('postal_code_present', False) else 'FAIL'
        ]
    
    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row)

class TestFreedomPayAPI:
    # Class variables instead of instance variables
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    name_mismatch_count = 0
    critical_failures = 0

    @pytest.fixture(autouse=True)
    def _setup_class(self):
        """Reset counters before each test session"""
        TestFreedomPayAPI.total_tests = 0
        TestFreedomPayAPI.passed_tests = 0
        TestFreedomPayAPI.failed_tests = 0
        TestFreedomPayAPI.name_mismatch_count = 0
        TestFreedomPayAPI.critical_failures = 0
    
    @pytest.fixture
    def store_data(self) -> List[Tuple[str, str, str, str, str, str, str, str]]:
        return read_store_data('src/data/stores.csv')
    
    @pytest.mark.parametrize("store_tuple", read_store_data('src/data/stores.csv'))
    def test_create_transaction(self, store_tuple, driver):
        TestFreedomPayAPI.total_tests += 1
        store_id, terminal_id, property_id, revenue_center_id, location_name, revenue_center_name, dba_name, batch = store_tuple
        base_page = BasePage(driver)
        is_safari = is_mac()
        failures = []
        timer_value = "Not Found"
        
        # Dictionary to track test results
        results = {
            'timer_present': False,
            'timer_correct': False,
            'googlepay_present': False,
            'applepay_present': False,
            'store_name_match': False,
            'postal_code_present': False
        }
        
        try:
            response = create_freedom_pay_transaction(store_id, terminal_id)
            checkout_url = response['CheckoutUrl']

            # Check for null/None URL first
            if not checkout_url or not checkout_url.startswith("https://"):
                error_msg = f"Store not configured. API Response: {response.get('ResponseMessage', 'No message')}"
                write_failure_to_file(store_id, terminal_id, dba_name, property_id, revenue_center_id, error_msg)
                
                # Set all results to N/A for CSV
                results = {
                    'timer_present': False,
                    'timer_correct': False,
                    'googlepay_present': False,
                    'applepay_present': False,
                    'store_name_match': False,
                    'postal_code_present': False
                }
                timer_value = "Invalid URL - Unable to access"
                
                # Write to CSV before skipping
                write_results_to_csv(store_id, terminal_id, property_id, revenue_center_id, 
                                   location_name, revenue_center_name, dba_name, results, timer_value, batch)
                
                TestFreedomPayAPI.critical_failures += 1
                TestFreedomPayAPI.failed_tests += 1
                pytest.skip(error_msg)  # Skip without screenshot since we can't load the page

            # URL format validation
            assert checkout_url.startswith('https://'), f"Invalid URL format received: {checkout_url}"
            assert isinstance(checkout_url, str), f"Invalid checkout URL format. Expected string, got {type(checkout_url)}"

            driver.get(checkout_url)

            # Timer check - moved to top after page load
            try:
                timer_element = base_page.wait_for_element_visible(CommonLocators.TIMER)
                results['timer_present'] = True
                timer_text = timer_element.get_attribute('textContent')
                
                if timer_text is None:
                    timer_value = "No timer text found"
                    results['timer_correct'] = False
                    failures.append(f"Timer text is empty")
                else:
                    timer_value = timer_text.strip()
                    results['timer_correct'] = timer_value.startswith(('05:00', '04:59', '04:58'))
                    if not results['timer_correct']:
                        failures.append(f"Timer started with incorrect value: {timer_value}. Expected: 05:00 or 04:59")
                        
            except Exception as e:
                results['timer_present'] = False
                results['timer_correct'] = False
                timer_value = "Timer not found"
                failures.append(f"Timer check failed: {str(e)}")
            
            # Google Pay check
            try:
                results['googlepay_present'] = base_page.is_element_present(CommonLocators.GOOGLE_PAY_BUTTON)
                if not results['googlepay_present']:
                    failures.append("Google Pay button not found")
            except Exception as e:
                results['googlepay_present'] = False
                failures.append(f"Google Pay check failed: {str(e)}")

            # Apple Pay check (Safari only)
            if is_safari:
                try:
                    results['applepay_present'] = base_page.is_element_present(SafariLocators.APPLE_PAY_BUTTON)
                    if not results['applepay_present']:
                        failures.append("Apple Pay button not found")
                except Exception as e:
                    results['applepay_present'] = False
                    failures.append(f"Apple Pay check failed: {str(e)}")

            # Store name check
            if dba_name:
                try:
                    base_page.wait_for_element_visible(CommonLocators.STORE_NAME)
                    actual_store_name = base_page.get_text(CommonLocators.STORE_NAME)
                    results['store_name_match'] = dba_name in actual_store_name
                    if not results['store_name_match']:
                        failures.append(f"Store name mismatch. Expected: {dba_name}, Got: {actual_store_name}")
                except Exception as e:
                    results['store_name_match'] = False
                    failures.append(f"Store name check failed: {str(e)}")

            # Postal code check
            try:
                base_page.switch_to_frame((By.CSS_SELECTOR, "iframe#hpc--card-frame"))
                results['postal_code_present'] = base_page.is_element_present(CommonLocators.POSTAL_CODE_FIELD)
                if not results['postal_code_present']:
                    failures.append("Postal code field not found")
                base_page.switch_to_default_content()
            except Exception as e:
                results['postal_code_present'] = False
                failures.append(f"Postal code check failed: {str(e)}")
                base_page.switch_to_default_content()

            # Write results to files
            write_timer_to_file(store_id, terminal_id, dba_name, property_id, revenue_center_id, timer_value)
            write_results_to_csv(store_id, terminal_id, property_id, revenue_center_id, 
                               location_name, revenue_center_name, dba_name, results, timer_value, batch)
            
            if failures:
                # Determine failure type for counting
                if any("Store name mismatch" in failure for failure in failures):
                    TestFreedomPayAPI.name_mismatch_count += 1
                    prefix = "name_mismatch"
                else:
                    TestFreedomPayAPI.critical_failures += 1
                    prefix = "critical"
                
                # Create screenshot name
                if dba_name:
                    screenshot_name = f"{prefix}_{dba_name}"
                else:
                    screenshot_name = f"{prefix}_store_{store_id}"
                
                take_screenshot(driver, store_id, screenshot_name)
                
                for failure in failures:
                    write_failure_to_file(store_id, terminal_id, dba_name, property_id, revenue_center_id, failure)
                
                TestFreedomPayAPI.failed_tests += 1
                pytest.fail(f"Store {store_id} failed")
            else:
                TestFreedomPayAPI.passed_tests += 1

        except AssertionError as e:
            write_timer_to_file(store_id, terminal_id, dba_name, property_id, revenue_center_id, timer_value)
            write_results_to_csv(store_id, terminal_id, property_id, revenue_center_id, 
                               location_name, revenue_center_name, dba_name, results, timer_value, batch)
            write_failure_to_file(store_id, terminal_id, dba_name, property_id, revenue_center_id, str(e))
            
            screenshot_name = f"critical_{store_id}_assertion_error"
            take_screenshot(driver, store_id, screenshot_name)
            pytest.skip(str(e))
            
        except Exception as e:
            screenshot_name = f"critical_store_{store_id}_error"
            try:
                driver.save_screenshot(os.path.join("results", "screenshots", f"{screenshot_name}.png"))
            except Exception as screenshot_error:
                print(f"Failed to take screenshot: {str(screenshot_error)}")

            write_failure_to_file(store_id, terminal_id, dba_name, property_id, revenue_center_id, str(e))
            raise

    @pytest.fixture(scope="session", autouse=True)
    def _print_summary(self, request):
        """Print summary after all tests are done"""
        def print_summary():
            print("\n" + "="*50)
            print("TEST SUMMARY")
            print("="*50)
            print(f"Total Tests Run: {TestFreedomPayAPI.total_tests}")
            print(f"Tests Passed: {TestFreedomPayAPI.passed_tests}")
            print(f"Tests Failed: {TestFreedomPayAPI.failed_tests}")
            print(f"Name Mismatches: {TestFreedomPayAPI.name_mismatch_count}")
            print(f"Critical Failures: {TestFreedomPayAPI.critical_failures}")
            print("="*50 + "\n")
        
        request.addfinalizer(print_summary)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
