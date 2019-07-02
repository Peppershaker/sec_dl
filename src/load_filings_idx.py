import datetime
import requests
import pandas as pd
import time
from io import StringIO
from scrape_all_filings import connect_db
from sqlalchemy import Integer, String, Date
from CONSTANTS import FILING_START_YR

def load_filings_table_via_sec():
    """Downloads the filing index file from SEC, which contains company information and filings url, and loads into database.
    All filings not set to keep in filign_types table and all companies not in companies table will be discarded"""
    # Init db connection
    engine, metadata, _, _, connection, _ = connect_db()
    
    start_year = FILING_START_YR
    current_year = datetime.date.today().year
    current_quarter = (datetime.date.today().month - 1) // 3 + 1

    # Construct a list of years-quarter to download
    years = list(range(start_year, current_year))
    quarters = ['QTR1', 'QTR2', 'QTR3', 'QTR4']
    history = [(y, q) for y in years for q in quarters]
    
    for i in range(1, current_quarter + 1):
        history.append((current_year, 'QTR%d' % i))
    urls = ['https://www.sec.gov/Archives/edgar/full-index/%d/%s/master.idx' % (x[0], x[1]) for x in history]
    urls.sort()

    # Download the index files
    with engine.connect() as connection:
        universe_of_ciks = pd.read_sql_table('companies', connection, columns=['cik'])
        filings_to_keep = pd.read_sql_table('filing_types', connection)
        filings_to_keep = filings_to_keep[filings_to_keep['keep'] == 1]
        
        for url in urls:
            all_rows = requests.get(url).content.decode("utf-8", "ignore")
            csv = StringIO(all_rows)
            records = pd.read_csv(csv, sep='|', skiprows=9)
            records = records.drop(labels=[0], axis='rows')
            records.columns = ['cik', 'business_name', 'type', 'date', 'path']

            # Drop all filings of stocks not in our cik universe
            records = records[records['cik'].isin(universe_of_ciks['cik'].values)]
            
            # Drop all filing types that we are not interested in
            records = records[records['type'].isin(filings_to_keep['type'])]
            
            # Write to database
            records.to_sql('filings', connection, if_exists='append',  chunksize=10000, index=False,
                                dtype={'filing_id' : Integer(),
                                    'cik' : Integer(),
                                    'business_name' : String(200),
                                    'type' : String(50),
                                    'path' : String(512),
                                    'date' : Date()})
            print(url, "Wrote to database")

def create_unscraped_table():
    """Create the unscraped filings table, which holds all filings that have yet to be downloaded.
    A trigger on filings is also created to delete filing_id from unscraped_filings once the filing
    has been successfully downloaded"""

    engine, metadata, _, _, connection, _ = connect_db()

    with engine.connect() as connection:
        stmt = """
        CREATE TABLE unscraped_filings AS
        SELECT filing_id FROM filings;
        """
        connection.execute(stmt)

        # Create a trigger to delete the filing_id from unscraped_filings after successful download
        stmt = """
        CREATE OR REPLACE FUNCTION function_delete_filing_id() RETURNS TRIGGER AS
        $BODY$
        BEGIN
            DELETE FROM
                unscraped_filings
                where filing_id = NEW.filing_id;

                RETURN NEW;
        END;
        $BODY$
        language plpgsql;

        CREATE TRIGGER trigger_update_unscraped
        AFTER UPDATE ON filings
        FOR EACH ROW
        EXECUTE PROCEDURE function function_delete_filing_id();
        """
        connection.execute(stmt)

if __name__ == "__main__":
    load_filings_table_via_sec()
    create_unscraped_table()