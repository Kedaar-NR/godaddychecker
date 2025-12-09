# GoDaddy Domain Checker

A Python tool to check domain availability on GoDaddy for multiple domain names across .com, .dev, .ai, and .org extensions. Available as both a command-line script and a Streamlit web application.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install ChromeDriver (required for Selenium):
   - **macOS**: `brew install chromedriver`
   - **Linux**: Download from https://chromedriver.chromium.org/
   - **Windows**: Download from https://chromedriver.chromium.org/ and add to PATH

## Usage

### Option 1: Command line arguments
```bash
python domain_checker.py name1 name2 name3
```

### Option 2: Create a domains.txt file
Create a file named `domains.txt` with one domain name per line:
```
example
test
mydomain
```

Then run:
```bash
python domain_checker.py
```

### Option 3: Interactive input
Just run the script and enter domain names when prompted:
```bash
python domain_checker.py
```

## Web UI (Streamlit)

Run the Streamlit web application:

```bash
streamlit run app.py
```

The web UI allows you to:
- Paste a list of domain names (one per line)
- Select which extensions to check (.com, .dev, .ai, .org)
- View real-time progress and results
- Filter and download results as CSV

## Output

The script will:
1. Check each domain name for .com, .dev, .ai, and .org extensions
2. Save results to `domain_check_results.csv`
3. Display a summary of available/taken/unknown domains

## CSV Output Format

The CSV file contains:
- Domain Name: The base domain name
- Extension: The TLD (.com, .dev, .ai, .org)
- Full Domain: The complete domain name
- Available: Yes/No/Unknown
- Status: Detailed status message

## Notes

- The script uses Selenium to automate browser interactions with GoDaddy
- There's a 2-second delay between checks to avoid rate limiting
- Results are based on GoDaddy's domain search page

