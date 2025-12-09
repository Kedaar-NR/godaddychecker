#!/usr/bin/env python3
"""
Streamlit Web App for Domain Availability Checker
Deploy this on Python hosting platforms like Streamlit Cloud, Heroku, etc.
"""

import streamlit as st
import pandas as pd
import time
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import io

# Page configuration
st.set_page_config(
    page_title="Domain Availability Checker",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stProgress > div > div > div {
        background-color: #1f77b4;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_driver():
    """Initialize and cache the Chrome driver"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(5)
        return driver
    except Exception as e:
        st.error(f"Error initializing browser: {e}")
        st.info("Make sure ChromeDriver is installed. On macOS: `brew install chromedriver`")
        return None

def check_domain_availability(driver, domain_name: str, extension: str) -> Dict:
    """Check if a domain is available on GoDaddy"""
    full_domain = f"{domain_name}{extension}"
    
    try:
        # Use GoDaddy's direct search URL
        search_url = f"https://www.godaddy.com/domainsearch/find?checkAvail=1&domainToCheck={full_domain}"
        driver.get(search_url)
        time.sleep(2)  # Wait for page to load
        
        # Get page content
        page_text = driver.page_source.lower()
        
        # Determine availability
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
                domain_elements = driver.find_elements(
                    By.XPATH, 
                    f"//*[contains(text(), '{full_domain}')]"
                )
                
                if domain_elements:
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
                            element_text = element.text.lower()
                            if any(ind in element_text for ind in available_indicators):
                                is_available = True
                                status = "Available"
                                break
                            elif any(ind in element_text for ind in taken_indicators):
                                is_available = False
                                status = "Taken"
                                break
                
                # Fallback: check page text
                if is_available is None:
                    if any(ind in page_text for ind in available_indicators):
                        if f"{full_domain}" in page_text:
                            is_available = True
                            status = "Available"
                    elif "domain taken" in page_text or f"{full_domain} is taken" in page_text:
                        is_available = False
                        status = "Taken"
                        
            except Exception:
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
            "Status": f"Error: {str(e)[:50]}"
        }

def main():
    # Header
    st.markdown('<h1 class="main-header">🌐 Domain Availability Checker</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Check domain availability on GoDaddy for .com, .dev, and .ai extensions</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        extensions = st.multiselect(
            "Select Extensions",
            [".com", ".dev", ".ai"],
            default=[".com", ".dev", ".ai"]
        )
        
        delay = st.slider(
            "Delay between checks (seconds)",
            min_value=1,
            max_value=5,
            value=2,
            help="Increase if you encounter rate limiting"
        )
        
        st.markdown("---")
        st.markdown("### 📝 Instructions")
        st.markdown("""
        1. Enter domain names (one per line) in the text area
        2. Or upload a .txt file with domain names
        3. Click "Check Domains" to start
        4. Results will appear in a table below
        5. Download results as CSV when done
        """)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Domain Names Input")
        input_method = st.radio(
            "Input Method",
            ["Text Input", "File Upload"],
            horizontal=True
        )
        
        domain_names = []
        
        if input_method == "Text Input":
            domain_text = st.text_area(
                "Enter domain names (one per line)",
                height=200,
                placeholder="example\ntest\nmydomain",
                help="Enter one domain name per line (without extensions)"
            )
            if domain_text:
                domain_names = [line.strip().lower() for line in domain_text.split('\n') if line.strip()]
        else:
            uploaded_file = st.file_uploader(
                "Upload domains.txt file",
                type=['txt'],
                help="Upload a text file with one domain name per line"
            )
            if uploaded_file:
                content = uploaded_file.read().decode('utf-8')
                domain_names = [line.strip().lower() for line in content.split('\n') if line.strip()]
    
    with col2:
        st.subheader("📊 Quick Stats")
        if 'results' in st.session_state and st.session_state.results:
            df = pd.DataFrame(st.session_state.results)
            available = len(df[df['Available'] == 'Yes'])
            taken = len(df[df['Available'] == 'No'])
            unknown = len(df[df['Available'] == 'Unknown'])
            
            st.metric("✅ Available", available)
            st.metric("❌ Taken", taken)
            st.metric("❓ Unknown", unknown)
            st.metric("📈 Total Checked", len(df))
        else:
            st.info("No results yet. Run a check to see stats.")
    
    # Check button
    if st.button("🚀 Check Domains", type="primary", use_container_width=True):
        if not domain_names:
            st.warning("⚠️ Please enter at least one domain name")
            return
        
        if not extensions:
            st.warning("⚠️ Please select at least one extension")
            return
        
        # Initialize driver
        driver = init_driver()
        if driver is None:
            return
        
        # Calculate total checks
        total_checks = len(domain_names) * len(extensions)
        st.info(f"🔍 Checking {len(domain_names)} domain(s) × {len(extensions)} extension(s) = {total_checks} total checks")
        
        # Initialize results
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Check domains
        check_count = 0
        for idx, domain_name in enumerate(domain_names):
            if not domain_name:
                continue
            
            for extension in extensions:
                check_count += 1
                status_text.text(f"Checking {domain_name}{extension}... ({check_count}/{total_checks})")
                
                result = check_domain_availability(driver, domain_name, extension)
                results.append(result)
                
                # Update progress
                progress_bar.progress(check_count / total_checks)
                
                # Small delay between checks
                time.sleep(delay)
        
        # Store results in session state
        st.session_state.results = results
        
        status_text.text("✅ Check complete!")
        progress_bar.empty()
        time.sleep(0.5)
        st.rerun()
    
    # Display results
    if 'results' in st.session_state and st.session_state.results:
        st.markdown("---")
        st.subheader("📊 Results")
        
        df = pd.DataFrame(st.session_state.results)
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_available = st.checkbox("Show Available", value=True)
        with col2:
            filter_taken = st.checkbox("Show Taken", value=True)
        with col3:
            filter_unknown = st.checkbox("Show Unknown", value=True)
        
        # Apply filters
        filtered_df = df[
            (df['Available'] == 'Yes') & filter_available |
            (df['Available'] == 'No') & filter_taken |
            (df['Available'] == 'Unknown') & filter_unknown
        ]
        
        # Display table with styling
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"domain_check_results_{int(time.time())}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # Summary statistics
        st.markdown("---")
        st.subheader("📈 Summary Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            available_count = len(df[df['Available'] == 'Yes'])
            st.metric("✅ Available", available_count, f"{available_count/len(df)*100:.1f}%")
        
        with col2:
            taken_count = len(df[df['Available'] == 'No'])
            st.metric("❌ Taken", taken_count, f"{taken_count/len(df)*100:.1f}%")
        
        with col3:
            unknown_count = len(df[df['Available'] == 'Unknown'])
            st.metric("❓ Unknown", unknown_count, f"{unknown_count/len(df)*100:.1f}%")
        
        with col4:
            st.metric("📊 Total", len(df))
        
        # Breakdown by extension
        st.markdown("### Breakdown by Extension")
        extension_stats = df.groupby('Extension')['Available'].value_counts().unstack(fill_value=0)
        st.bar_chart(extension_stats)

if __name__ == "__main__":
    main()

