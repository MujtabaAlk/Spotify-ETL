# Spotify-ETL
Extract your Spotify recently played songs (last 30 days) and store in database


## Installation
run ```pip install -r requirements.txt```

## Usage
Create an app on the Spotify developer dashbord. 


Create a config file ```config.json``` with the following content:
```json
{
    "client_id": "<YOUR SPOTIFY APP CLIENT ID>",
    "client_secret": "<YOUR SPOTIFY APP CLIENT SECRET>",
    "database_url": "<YOUR DATABASE URL>"
}
```
_the app client id and secret can be coppid from the Spotify developer dashbord when you create an app._

run ```python src/create_db.py``` once to create the database

run ```python src/main.py``` to get the data (accept the authentication propt)
