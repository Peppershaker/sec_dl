from sqlalchemy import create_engine, ForeignKey, Index
from sqlalchemy import MetaData, Table, String, Column, Text, Date, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.sql import text
from CONSTANTS import DB_USERNAME, DB_PASSWORD, DB_HOST, DB_NAME

import pandas as pd


def init_tables(): 
    """Initializes the filings and companies database tables"""
    # Ask for confirmation before dropping tables
    accept = False
    while not accept:
        usr_input = input(
            "Are you sure you want to reinitialize the db? THIS WILL WIPE THE CURRENT DB. ALL DATA WILL BE LOST! [Y/N]:")
        if usr_input == 'Y' or usr_input == 'y':
            accept = True
            db_cred = f"{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
            engine = create_engine(f"postgresql+psycopg2://{db_cred}")
            metadata = MetaData(bind=engine)

    with engine.connect() as connection:
        # Dropping the tables if they already exist
        for table in ['companies', 'filings']:
            connection.execute(
                "DROP TABLE IF EXISTS {} CASCADE;".format(table))

        # Init tables
        companies = Table('companies', metadata,
                          Column('permno', Integer(), primary_key=True),
                          Column('ticker', String(10), nullable=False),
                          Column('cik', Integer(), nullable=True),
                          Column('business_name', String(100), nullable=False))

        filing_types = Table('filing_types', metadata,
                             Column('type_id', Integer(), primary_key=True),
                             Column('type', Text(), nullable=False),
                             Column('keep', Integer(), nullable=False))

        filings = Table('filings', metadata,
                        Column('filing_id', Integer(), primary_key=True),
                        Column('cik', Integer(), nullable=False),
                        Column('business_name', Text(), nullable=True),
                        Column('type', Text(), nullable=True),
                        Column('path', Text(), nullable=True),
                        Column('date', Date(), nullable=True),
                        Column('text', Text(), nullable=True),
                        Column('token', TSVECTOR(), nullable=True))

        metadata.create_all(engine)

        # Enable full text search
        # Create Gin Index
        stmt = """CREATE INDEX idx_filing ON filings USING gin(token);"""
        connection.execute(stmt)

        stmt = """
        CREATE TRIGGER update_index
        BEFORE UPDATE OR INSERT
        ON filings
        FOR EACH ROW
        EXECUTE PROCEDURE
        tsvector_update_trigger(token, 'pg_catalog.english', text)
        """
        connection.execute(stmt)

        return engine


def load_companies(engine):
    """Loads the companies table from CSV to the database"""
    with engine.connect() as connection:
        companies_df = pd.read_csv('../data/companies.csv')
        companies_df.to_sql(
            'companies',
            connection,
            if_exists='append',
            chunksize=100,
            index=False)


def load_filing_types(engine):
    """Loads the SEC filing type table which contains a list of filing types 
    to download from CSV to the database"""
    with engine.connect() as connection:
        filing_types_df = pd.read_csv('../data/filing_types.csv')
        filing_types_df.index.names = ['type_id']
        filing_types_df.to_sql(
            'filing_types',
            connection,
            if_exists='append',
            index=True)


if __name__ == "__main__":
    engine = init_tables()
    load_companies(engine)
    load_filing_types(engine)
