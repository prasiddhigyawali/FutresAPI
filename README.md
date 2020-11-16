# FutresAPI

# Installation
  * Copy dbtemp.ini to db.ini and update credentials locally
  * Ensure you are running python 3.6.8  Reccomend using pyenv to manage your environment, see https://github.com/pyenv/pyenv-virtualenv
  * pip install -r requirements.txt 

# Running the Script
Run the fetch.py command to fetch data from GEOME and it will populate
JSON files in the data directory.  This repository populates lookup lists using the fetch.py 
script.  It also populates the elasticsearch backend database using the loader.py script.

The FuTRES dynamic data is hosted by the plantphenology nodejs proxy service at:
https://github.com/biocodellc/ppo-data-server/blob/master/docs/es_futres_proxy.md

See api.md for the API documentation

When running properties the properties file copy the contents of the dbtemp.ini file to a db.ini file and change the password. 
