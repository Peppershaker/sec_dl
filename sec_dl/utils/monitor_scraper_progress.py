import time
from scrape_all_filings import connect_db 
from datetime import datetime

def get_rows_left():
    rows_left = session.query(filings.c.filing_id, filings.c.path).filter(filings.c.text == None).count()
    return rows_left

engine, metadata, Session, session, connection, filings = connect_db()
start_time = datetime.now() 
rows_left_at_start = get_rows_left()

print("Waiting to collect data")
time.sleep(10)

if __name__ == "__main__":
    while True:
        current_time = datetime.now()
        time_elapsed = current_time - start_time
        rows_left = get_rows_left()
        rows_completed_since_start = rows_left_at_start - rows_left
        seconds_per_iteration = time_elapsed.seconds / rows_completed_since_start
        mins_left = rows_left * seconds_per_iteration / 60
        print("Update On {}".format(datetime.now()))
        print("{} rows left, {:.2f} minutes to go".format(rows_left, mins_left )) 
        print()
        start_time = current_time
        rows_left_at_start = rows_left
        time.sleep(5*60)
