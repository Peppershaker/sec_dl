# SEC dl

A fully automated and configurable solution to download SEC filings and stores it in a Posgresql database. The filing text is automatically tokenized and indexed, and therefore supports near real time full text search. A dockerized adminer server is also spun up to provide some basic UI for the database

## Deployment

1)	First clone this repo and navigate to the root of the project director.
```
git clone git@github.com:Peppershaker/sec_dl.git
```

2)	Config the **docker-compose.yml** file by specifying the location in which you want to store the database files.

```
vim Docker/docker-compose.yml
```

Optionally change the database credentials
```
POSTGRES_USER:[set_username]
POSTGRES_PASSWORD:[set_password]	
POSTGRES_DB:[set_db_name]
```

Set the path to save the database files. The Postgres database runs in a docker container and is stateless, this means it mounts a directory from your host machine to the docker container in order to access the database files. You will need to specify the path by replacing path_on_host_machine. Leave the second portion :/var/lib/... as is (unless you know what you're doing)

```
-volumes:
	- path_on_host_machine:/var/lib/postgresql/data
```

3)	Set database credentials and other script settings.

```	
vim sec_dl/config/CONSTANTS.py
```

Populate database username, password, and name as per step 2. Leave **DB_HOST** as localhost.

Change the **FILING_START_YEAR** variable to specify the time window of filings to download. The script will download all filings from **FILING_START_YEAR** to now. Depending on the size of your stock universe, you should allocate approximately 5GB of disk space per 1000 tickers per year.

The variable **CONCURRENT_WORKERS** defines the number of downloads & text parsing jobs to run in parallel. However, you will likely be CPU bottle necked, as opposed to network IO. 20 workers about maxes out my Skylake Dual Core CPU.

4)	Run the startup script located in the project root folder.
```
source run.sh
```

## Authors

* **Victor Xu** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details