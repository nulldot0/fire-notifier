# Fire Notifier

## Introduction
This is a simple python script that sends a notification to your phone when a fire is reported to [TxtFire Philippines](https://txtfire.net/).
This uses the [Pushover API](https://pushover.net/) to send notifications to your phone.

## Requirements
- Python 3.6+
- A [Pushover](https://pushover.net/) account. You can get a free account [here](https://pushover.net/). After creating an account, you will need to the user key and create an application to get an API token.
- Setup your device to receive notifications from Pushover. You can download the app from the [App Store](https://apps.apple.com/us/app/pushover-notifications/id506088175) or [Google Play](https://play.google.com/store/apps/details?id=net.superblock.pushover&hl=en&gl=US).
- Docker (optional)


## Installation
1. Just clone this repository.

## To run the script
1. Create an virtual environment and activate it.
```bash
python -m venv venv
source venv/bin/activate
```
2. Install the required packages
```bash
pip install -r requirements.txt
```
3. Create a `.env` file in the root directory of the project and add the following environment variables.
```bash
DELAY=30
SEARCH_TERM=Quezon City
PUSHOVER_TOKEN=your_pushover_api_token
PUSHOVER_USER=your_pushover_user_key
```
3. Run the script
```bash
python fire_notifier.py
```

## To run as a docker container
1. Build the docker image
```bash
docker build -t fire_notifier .
```
2. Create a `.env` file in the root directory follow step 2 above.
3. Run the docker container
```bash
docker run --name fire-notifier --env-file .env fire_notifier
```
#### To keep running even if your system restarts
```bash
docker run -d --name fire-notifier --env-file .env --restart always fire_notifier
```
#### To have persistent data
```bash
docker run -d --name fire-notifier --env-file .env --restart always -v fire_notifier_data:/app/db fire_notifier
``` 

## Environment Variables
- **`DELAY`** - The delay in seconds between each check for new fires. Default is 30 seconds.
- **`SEARCH_TERM`** - The search term to use to filter the fire data.  Example: `Holy Spirit`, `Quezon City`, `Manila`, etc... 
The default is empty string meaning it will send notification if it's a dangerous alert type regardless of the location.
- **`PUSHOVER_TOKEN`** - Your Pushover API token.
- **`PUSHOVER_USER`** - Your Pushover user key.
