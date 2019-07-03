from sec_dl.utils.init_tables import init_all_tables
from sec_dl.utils.scrape_all_filings import process_filings
from sec_dl.utils.load_filings_idx import load_filings

if __name__ == "__main__":
    init_all_tables()
    load_filings()
    process_filings()