# FutresAPI

# Installation
  * Copy dbtemp.ini to db.ini and update credentials locally
  * Ensure you are running python 3.6.8  Reccomend using pyenv to manage your environment, see https://github.com/pyenv/pyenv-virtualenv
  * pip install -r requirements.txt 

# Running the Script
The fetch.py script gets data from GEOME and looks in the vertnet directory for 
processed Vertnet scripts and populates JSON files in the data directory as well
as a gzipped `data/futres_data_processed.csv.gz` which we will use in the loader script.
script.  

The loader.py script populates the elasticsearch backend database using the loader.py script
See the Loading into ElasticSearch section below.

The FuTRES dynamic data is hosted by the plantphenology nodejs proxy service at:
https://github.com/biocodellc/ppo-data-server/blob/master/docs/es_futres_proxy.md

See api.md for the API documentation

When running properties the properties file copy the contents of the dbtemp.ini file to a db.ini file and change the password. 

# Loading into ElasticSearch
the loader.py script recurses all *.csv files in the data directory
 * scp data/futres_data_processed.csv.gz to biscicol which has port 80 access to tarly, a cyverse server. Another option is to just run the processing pipeline on biscicol.org
 * gunzip data/futres_data_processed.csv.gz
 * python loader.py
