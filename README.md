# SEC dl

![sec_dl_graphic](https://user-images.githubusercontent.com/15576531/60568103-d6907980-9d39-11e9-806c-f5e64f6e3c97.jpg)


A fully automated and configurable solution to download SEC filings and stores it in a Posgresql database. The filing text is automatically tokenized and indexed, and therefore supports near real time full text search.
A dockerized adminer server is also spun up to provide some basic UI for the database

## Requirements
```
Docker
Python3
```

## Quick Start
This quick start guide supports downloading nearly all SEC filings for US listed stocks under $1B market cap based on ~ March 2019 valuation. Read the section on Stock Universe to change your stocks of interest.

First clone this repo and navigate to the root of the project director.

```
git clone git@github.com:Peppershaker/sec_dl.git
```

Config Docker Compose by specifying the database file path and optionally change the db credentials.

```
vim Docker/docker-compose.yml
```

Optionally change the database credentials

```
POSTGRES_USER:[set_username]
POSTGRES_PASSWORD:[set_password]	
POSTGRES_DB:[set_db_name]
```

Set the path to save the database files. The Postgres database runs in a docker container and is stateless, this means it mounts a directory from your host machine to the docker container in order to access the database files.
You will need to specify the path by replacing path_on_host_machine. Leave the second portion :/var/lib/... as is (unless you know what you're doing)

```
-volumes:
	- path_on_host_machine:/var/lib/postgresql/data
```

Set database credentials and other script settings.

```	
vim sec_dl/config/CONSTANTS.py
```

Populate database username, password, and name as per Docker Compose config. Leave **DB_HOST** as localhost.

Change the **FILING_START_YEAR** variable to specify the starting time of filings to download. The script will download all filings from **FILING_START_YEAR to now**. Depending on the size of your stock universe, you should allocate approximately 5GB of disk space per 1,000 tickers per year.

The variable **CONCURRENT_WORKERS** defines the number of downloads & text parsing jobs to run in parallel. However, you will likely be CPU bottle necked as opposed to network IO. 20 workers about maxes out my Skylake Dual Core CPU.

Run the startup script located in the project root folder to create the docker containers and execute the download script.

```
source run.sh
```

## Setting Stock Universe
To change the stocks of interest, you must make changes to the companies table in the database. If you are running this project for the first time, or don't mind downloading from scratch, then the easiest way of changing this table without writing SQL is to change the companies.csv file located in the data folder.
```
sec_dl/data/companies.csv
```

#### Company Identification: PERMNO vs CIK vs Ticker
There are two types of company identifiers, unique vs non-unique. A unique identifier is exclusive for one company, and is never recycled; whereas a non-unique identifier is recycled.

PERMNO is a **unique** company identifier mostly used by WRDS (Wharton Research Data Service).

CIK is a **unique** company identifier mostly used by the SEC, and is referenced in all filings released by the SEC. It is important to note that the SEC DOES NOT reference companies by their Ticker as they are non unique.

Ticker is a **non unique** company identifier mostly used by exchanges. This means if WXYZ goes bankrupt and gets delisted, a new company can now use WXYZ.

If this project is going to be used in live trading, I **strongly** recommand you to have an intense QA effort in making sure these identifiers are referenced to eachother correctly. There is currently no data source available to retail traders that compiles and updates this information, so the task is on your hands.

#### Tips on Joining Company Identifier Data
As discussed, tickers change over time, so when joing identifier data, pay special attention to the following as they have all been observed to change the Ticker.
* M&A
* Bankrupcy
* Delisting / Relisting
* Company Name Change / Ticker Change
* Restructuring

#### Changing the Universe of Stocks of Interest
The supplied companies.csv file contains ticker for nearly all US listed companies with under $1B capitalization as of ~ March 2019. Non operating companies such as ETFs and various financial asset holdings companies are removed.

To make changes to the stocks to grab filings for, you need to either edit `companies.csv` file and run `run.sh`, or modify the companies table in PostgreSQL.

The only mandatory field is CIK. SEC filings are refereced to CIK and all filings not in the CIK column on the companies table will be discarded.

## Setting Filing Types to Download
There are approximately 300 different filing types used by the SEC. Similarily, to change the type of filings to download you would need to change the filing_type table in PostgreSQL, or modify `filing_type.csv` file if running the project from scratch. 
```
vim sec_dl/data/filing_tyoe.csv
```

The default setting downloads pretty much all valuable filing types that can be data mined.

## Author

* **Victor Xu**

## License

This project is licensed under the MIT License
