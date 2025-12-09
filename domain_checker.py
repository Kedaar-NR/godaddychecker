#!/usr/bin/env python3
"""
Domain Availability Checker for GoDaddy
Checks domain availability for .com, .dev, and .ai extensions
"""

import csv
import time
import sys
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def check_domain_availability(driver, domain_name: str, extension: str) -> Dict:
    """
    Check if a domain is available on GoDaddy
    Returns: dict with domain info and availability status
    """
    full_domain = f"{domain_name}{extension}"
    
    try:
        # Use GoDaddy's direct search URL (more reliable)
        search_url = f"https://www.godaddy.com/domainsearch/find?checkAvail=1&domainToCheck={full_domain}"
        driver.get(search_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Get page content
        page_text = driver.page_source.lower()
        page_title = driver.title.lower()
        
        # Determine availability based on page content
        is_available = None
        status = "Unknown"
        
        # Check for "taken" indicators
        taken_indicators = [
            "is taken",
            "domain taken",
            "already taken",
            "unavailable",
            "not available"
        ]
        
        # Check for "available" indicators
        available_indicators = [
            "add to cart",
            "buy now",
            "add to bag",
            "purchase"
        ]
        
        # Check if domain is taken
        for indicator in taken_indicators:
            if indicator in page_text:
                is_available = False
                status = "Taken"
                break
        
        # If not taken, check if available
        if is_available is None:
            # Look for the specific domain in results
            try:
                # Try to find the domain result card/row
                domain_elements = driver.find_elements(
                    By.XPATH, 
                    f"//*[contains(text(), '{full_domain}')]"
                )
                
                if domain_elements:
                    # Check for "Add to Cart" or price buttons near the domain
                    for element in domain_elements:
                        try:
                            parent = element.find_element(By.XPATH, "./ancestor::*[contains(@class, 'domain') or contains(@class, 'result')][1]")
                            parent_text = parent.text.lower()
                            
                            if any(ind in parent_text for ind in available_indicators):
                                is_available = True
                                status = "Available"
                                break
                            elif any(ind in parent_text for ind in taken_indicators):
                                is_available = False
                                status = "Taken"
                                break
                        except NoSuchElementException:
                            # If can't find parent, just use element text
                            element_text = element.text.lower()
                            if any(ind in element_text for ind in available_indicators):
                                is_available = True
                                status = "Available"
                                break
                            elif any(ind in element_text for ind in taken_indicators):
                                is_available = False
                                status = "Taken"
                                break
                
                # Fallback: check page text for availability indicators
                if is_available is None:
                    if any(ind in page_text for ind in available_indicators):
                        # Make sure it's not showing alternatives
                        if f"{full_domain}" in page_text:
                            is_available = True
                            status = "Available"
                    elif "domain taken" in page_text or f"{full_domain} is taken" in page_text:
                        is_available = False
                        status = "Taken"
                        
            except Exception as e:
                # Fallback to text-based detection
                if any(ind in page_text for ind in available_indicators):
                    is_available = True
                    status = "Available"
                elif any(ind in page_text for ind in taken_indicators):
                    is_available = False
                    status = "Taken"
        
        return {
            "Domain Name": domain_name,
            "Extension": extension,
            "Full Domain": full_domain,
            "Available": "Yes" if is_available else "No" if is_available is False else "Unknown",
            "Status": status
        }
        
    except Exception as e:
        return {
            "Domain Name": domain_name,
            "Extension": extension,
            "Full Domain": full_domain,
            "Available": "Unknown",
            "Status": f"Error: {str(e)}"
        }

def check_domains(domain_names: List[str], extensions: List[str] = [".com", ".dev", ".ai"]) -> List[Dict]:
    """
    Check multiple domains across multiple extensions
    Returns a list of dictionaries with results
    """
    # Setup Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')  # Run in background (new headless mode)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    results = []
    
    try:
        # Selenium 4.6+ automatically manages ChromeDriver
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(5)
        
        for domain_name in domain_names:
            domain_name = domain_name.strip().lower()
            if not domain_name:
                continue
                
            for extension in extensions:
                print(f"Checking {domain_name}{extension}...")
                result = check_domain_availability(driver, domain_name, extension)
                results.append(result)
                print(f"  Result: {result['Available']} - {result['Status']}")
                
                # Small delay between checks
                time.sleep(2)
        
    except Exception as e:
        print(f"Error setting up browser: {e}")
        print("Make sure you have ChromeDriver installed and in your PATH")
        print("Or install it with: brew install chromedriver (on macOS)")
    finally:
        if driver:
            driver.quit()
    
    return results

def save_to_csv(results: List[Dict], filename: str = "domain_check_results.csv"):
    """Save results to a CSV file"""
    if not results:
        print("No results to save.")
        return
    
    fieldnames = ["Domain Name", "Extension", "Full Domain", "Available", "Status"]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nResults saved to {filename}")

def main():
    """Main function to run the domain checker"""
    print("Domain Availability Checker for GoDaddy")
    print("=" * 50)
    
    # Check if domain names are provided as command line arguments
    if len(sys.argv) > 1:
        domain_names = sys.argv[1:]
    else:
        # If no arguments, read from domains.txt file if it exists
        try:
            with open("domains.txt", "r") as f:
                domain_names = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print("\nPlease provide domain names:")
            print("1. As command line arguments: python domain_checker.py name1 name2 name3")
            print("2. Or create a 'domains.txt' file with one domain per line")
            print("3. Or enter them now (one per line, press Ctrl+D when done):")
            
            domain_names = []
            try:
                while True:
                    name = input().strip()
                    if name:
                        domain_names.append(name)
            except EOFError:
                pass
    
    if not domain_names:
        print("No domain names provided. Exiting.")
        return
    
    print(f"\nChecking {len(domain_names)} domain name(s) for .com, .dev, and .ai extensions...")
    print(f"Total checks: {len(domain_names) * 3}\n")
    
    results = check_domains(domain_names)
    save_to_csv(results)
    
    # Print summary
    print("\n" + "=" * 50)
    print("Summary:")
    available_count = sum(1 for r in results if r["Available"] == "Yes")
    taken_count = sum(1 for r in results if r["Available"] == "No")
    unknown_count = sum(1 for r in results if r["Available"] == "Unknown")
    
    print(f"Available: {available_count}")
    print(f"Taken: {taken_count}")
    print(f"Unknown/Error: {unknown_count}")

if __name__ == "__main__":
    main()
