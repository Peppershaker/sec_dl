# db credentials
DB_USERNAME="tradinguser"
DB_PASSWORD="tradingpassword"
DB_NAME="sec_dl"
DB_HOST="localhost"

# Start and end year of filings to grab
FILING_START_YR=2012

# Number of parallel download. Recommand default value of 20. The script is text
# processing bottle necked
CONCURRENT_WORKERS=20