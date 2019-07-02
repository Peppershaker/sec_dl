import datetime
import time
import numpy as np
from scrape_all_filings import connect_db, html_to_text, remove_words_over_length_n, remove_extra_white_spaces

def recheck_filings(engine, metadata, Session, session, connection, filings, filing_id_to_check = 184559, 
                    save_files=False, debug=False):
    i = 1
    start_time = datetime.datetime.now()
    # First get all the filings that still needs to be scraped
    still_has_filings = True
    while still_has_filings:
        if i % 100 == 0 and calc_time_left == True:
            time_left(i, start_time)
        # Quary the db to get a row
        if debug:
            stmt = """
                   SELECT filing_id, text FROM filings WHERE
                   filing_id = {};
            """.format(filing_id_to_check)
        else:    
            stmt = """
                   SELECT A.filing_id, B.text FROM (
                      SELECT filing_id FROM to_check TABLESAMPLE BERNOULLI (1)
                      LIMIT 1) A 
                      INNER JOIN filings B on A.filing_id = B.filing_id
            """
        rows_to_build = connection.execute(stmt)
        # Selecting an random row to avoid collisions with other scripts
        row_count = rows_to_build.rowcount
        if row_count == 0:
            print('Finished!')
            import sys
            sys.exit()
        else:
            random_row_number = np.random.randint(0, row_count)
        
        # Fetching the results and closing the connection
        result_list = rows_to_build.fetchall()

        row_filing_id, text = result_list[random_row_number]
        print("LOG: working on {}".format(row_filing_id))
        
        text_to_insert = text

        if debug:
            pass

        # Sanitize the text again
        start_len = len(text_to_insert)
        # 1) Sanitize HTML again
        text_to_insert = html_to_text(text_to_insert)   
        
        # 2) Remove super long string
        text_to_insert = remove_words_over_length_n(text_to_insert, n=20)

        # 3) Remove extra white spaces
        text_to_insert = remove_extra_white_spaces(text_to_insert)
        
        end_len = len(text_to_insert)
        
        if end_len < start_len:
            # Text was modified, update the filing text inside the database
            if save_files and end_len/start_len < 0.6:
                old_text = open('debug/old_text.txt', 'w')
                old_text.write(text)
                old_text.close()
                new_text = open('debug/new_text.txt', 'w')
                new_text.write(text_to_insert)
                new_text.close()
                print("Start len: ", start_len)
                print("End len: ", end_len)
                import sys
                sys.exit('SIGNIFICANT DIFF FOUND')

            if debug:
                import sys
                sys.exit('DEBUG MODE, DONE ITERATION')
            else:
                stmt = filings.update().where(filings.c.filing_id == row_filing_id).values({'text':text_to_insert})
                connection.execute(stmt)
                print("LOG: Commited new text on ", datetime.datetime.now())
        else:
            print("LOG: No work needed")
            if debug:
                import sys
                sys.exit('DEBUG MODE, DONE ITERATION')
            else:
                # Remove the filing_id from the to_do database
                connection.execute("""
                                   DELETE FROM to_check
                                   WHERE filing_id = {}
                                   """.format(row_filing_id))

if __name__ == "__main__":
    debug_ = False

    if debug_:
        engine, metadata, Session, session, connection, filings = connect_db()
        recheck_filings(engine, metadata, Session, session, connection, filings, filing_id_to_check=100246, 
                        save_files=True, debug=True)

    else:
        while True:
            try:
                engine, metadata, Session, session, connection, filings = connect_db()
                recheck_filings(engine, metadata, Session, session, connection, filings, save_files=False, debug=False)
            except ValueError:
                print("ERROR:{}: CONNECTION ERROR".format(datetime.datetime.now()))
                print("LOG: SLEEPING 20")
                time.sleep(20)
                try:
                    engine.dispose()
                    print("LOG: ENGINE DISPOSED")
                    connection.close()
                    print("LOG: CONNECTION CLOSED")
                except:
                    print("LOG: ERROR DISPOSING ENGINE OR CLOSING CONNECTIONS")
                    pass

