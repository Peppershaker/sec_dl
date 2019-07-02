import re
import datetime
import unicodedata
import requests
import time
import numpy as np
import multiprocessing
from sqlalchemy import create_engine
from sqlalchemy import MetaData, Table, String, Column, Text, DateTime, Boolean, Integer, Float, Date
from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup
from CONSTANTS import DB_USERNAME, DB_PASSWORD, DB_HOST, DB_NAME


def connect_db():
    """Make connection to the db"""

    engine = create_engine(
        f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}",
        echo=False)
    connection = engine.connect()
    metadata = MetaData(bind=engine)
    Session = sessionmaker()
    session = Session()

    print("LOG: SUCCESSFUL CONNECTION")
    # Make get requests to the SEC server to pull the data, and then once
    # received, append to database
    filings = Table('filings', metadata, autoload=True)

    # Enable the random select extension in Postgresql
    try:
        # tsm_system_rows extension returns random rows from the database
        connection.execute("CREATE EXTENSION tsm_system_rows;")
    except BaseException:
        print("tsm_system_rows extension already enabled")

    return engine, metadata, Session, session, connection, filings


def html_to_text(file_text):
    """Sanitizes HTML/XML by removing all tags"""
    pattern = re.compile(r'<.+?>')
    file_text = re.sub(pattern, ' ', file_text)
    file_test = re.sub(re.compile(r'\s+'), ' ', file_text)

    return file_text


def remove_extra_white_spaces(text):
    """Removes extra white spaces in string"""
    pattern = re.compile(r'\s+')
    return re.sub(pattern, ' ', text)


def remove_words_over_length_n(text_to_insert, n=20):
    """Removes words over a certain lengths from string"""
    text_to_insert_list = text_to_insert.split(" ")
    final_string = ""
    for word in text_to_insert_list:
        if len(word) < n:
            final_string += " " + word

    return final_string


def time_left(i, start_time):
    """Calculates the amount of time left needed to download and parse all the filings"""
    rows_left = session.query(
        filings.c.filing_id,
        filings.c.path).filter(
        filings.c.text is None).count()
    time_elapsed = datetime.datetime.now() - start_time
    seconds_per_iteration = time_elapsed.seconds / i
    mins_left = rows_left * seconds_per_iteration / 60
    print("=============================================================")
    print("{} rows left, {:.2f} minutes to go".format(rows_left, mins_left))
    print("=============================================================")


def remove_embedded_files(text_filing):
    """Delete embedded files in the text filings encoded in Base64"""
    soup = BeautifulSoup(text_filing, "lxml", from_encoding='latin-1')
    text_to_insert = ''
    files_in_filing = soup.find_all(name="filename")

    for file in files_in_filing:
        skip = False
        r = file.find(text=re.compile(
            r'(.pdf\s|.gif\s|.jpg\s|.zip\s|.rar\s|.jpeg\s|.bmp\s|.xlsx\s|.xls\s|.css\s|.js\s)'))
        if r is not None:
            r.parent.extract()
            skip = True

        else:
            file_text = file.get_text()
            file_text = unicodedata.normalize("NFKD", file_text)
            file_text = html_to_text(file_text)

        if not skip:
            text_to_insert += file_text

    text_to_insert = text_to_insert.replace('\n', ' ')
    text_to_insert = text_to_insert.replace('\t', ' ')
    text_to_insert = text_to_insert.replace('\x93', '\"')
    text_to_insert = text_to_insert.replace('\x94', '\"')
    text_to_insert = text_to_insert.replace('&#160;', ' ')
    text_to_insert = text_to_insert.replace('&nbsp;', ' ')
    text_to_insert = remove_words_over_length_n(text_to_insert, n=20)
    text_to_insert = remove_extra_white_spaces(text_to_insert)

    return text_to_insert

def dl_filing(arg_tup):
    """Looks up a filing_id from unscraped_filings table and updates the filings table"""

    # Quary the db to get a row, note that the Postgresql SYSTEM_ROWS function is fast but does not return truly random rows,
    # To avoid the probability of grabbing the same row as another process, we grab 10 rows and randomly pick one
    # Please refer to Postgresql documentation for more detail
    debug, engine = arg_tup
    
    with engine.connect() as connection:
        stmt = """
                    SELECT A.filing_id, B.path FROM (
                        SELECT filing_id FROM unscraped_filings TABLESAMPLE SYSTEM_ROWS (10)
                        ) A
                        INNER JOIN filings B on A.filing_id = B.filing_id
        """
        rows_to_build = connection.execute(stmt)

        # Selecting an random row to avoid collisions with other scripts
        row_count = rows_to_build.rowcount
        if row_count == 0:
            import sys
            sys.exit("Download complete")
        else:
            random_row_number = np.random.randint(0, row_count)

        # Fetching the results and closing the connection
        result_list = rows_to_build.fetchall()

        row_filing_id, path = result_list[random_row_number]
        print("LOG: working on {}".format(path))

        baseurl = 'https://www.sec.gov/Archives/'

        if debug:
            response = requests.get(baseurl + specified_path)
        else:
            response = requests.get(baseurl + path)

        text_filing = response.content.lower()

        # Remove embedded files
        text_to_insert = remove_embedded_files(text_filing)

        if debug:
            print(text_to_insert)
            debug_text_file = open("debug/parsing_filings.txt", "w")
            debug_text_file.write(text_to_insert)
            debug_text_file.close()

        else:
            stmt = filings.update().where(filings.c.filing_id ==
                                            row_filing_id).values({'text': text_to_insert})
            connection.execute(stmt)
            #print("LOG:", datetime.datetime.now(), "Done")
    

def process_filings(
        engine,
        metadata,
        Session,
        session,
        connection,
        filings,
        random_seed=2,
        sleep=False,
        debug=False,
        specified_path="edgar/data/826773/0001104659-13-062460.txt",
        calc_time_left=False):
    """Takes in filings URL to download and makes get request to the 
    SEC server. The downloaded text is then sanitized and loaded to the db"""
    i = 1
    start_time = datetime.datetime.now()

    pool = multiprocessing.Pool(20)

    # First get all the filings that still needs to be scraped
    still_has_filings = True
    while still_has_filings:
        if calc_time_left:
            # Calculates time left ever 100 filings downloaded
            time_left(i, start_time)

        pool.map(dl_filing, ((debug, engine) for x in range(100)) )
        i += 1



if __name__ == "__main__":
    while True:
        try:
            engine, metadata, Session, session, connection, filings = connect_db()
            process_filings(
                engine,
                metadata,
                Session,
                session,
                connection,
                filings,
                debug=False)
        except ValueError:
            print("ERROR:{}: CONNECTION ERROR".format(datetime.datetime.now()))
            print("LOG: SLEEPING 20")
            time.sleep(20)

            try:
                engine.dispose()
                print("LOG: ENGINE DISPOSED")
                connection.close()
                print("LOG: CONNECTION CLOSED")
            except BaseException:
                print("LOG: ERROR DISPOSING ENGINE OR CLOSING CONNECTIONS")
                pass
