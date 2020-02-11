# Trading Bot

This project is a Q-learning based bot that uses historical data to make a working model. After a model has been made the bot uses sentiment analysis of news articles as an extra data point. The bot runs on the Alpaca Stock Trading API and uses the Polygon data from Alpaca as well.

## Results

I'll post some results after I do some more testing. WIP

## Downsides

I have no idea how to actually implement Q-learning correctly so it could be very wrong. Please consider reaching out if you have some experience and want to help with it! Also cannot train on old news articles, so sentiment only runs during realtime.

## Data

All data is automatically requested from the Alpaca Barset and Polygon News

## Getting Started

To use this script you have to go out and get a few API keys:

[Make a Funded Alpaca Brokerage Account](https://alpaca.markets/)

[Apply for the Natural Language API](https://cloud.google.com/natural-language/)

After you finish with these few steps, write down your API keys, you'll need them below.

The next thing you want to do is set up an Ubuntu server. I can write a detailed guide on how to set one up if it's requested enough. I would recommend [Google Cloud Compute VM](https://console.cloud.google.com/compute/) or [AWS EC2 Instance](https://aws.amazon.com/). Once you have that up and running you want to set your environmental variables you can do this by inputting this in console (Fill in your information).

```bash
# Were I you I would use the URL for paper-trading to start
export APCA_API_BASE_URL=BASE_API_URL
export APCA_API_KEY_ID=YOUR_API_KEY_ID
export APCA_API_SECRET_KEY=YOUR_SECRET_KEY
export GOOGLE_APPLICATION_CREDENTIALS=PATH_TO_CREDENTIALS_FILE
```

Install python

```bash
sudo apt-get update
sudo apt-get install python 3.6
sudo apt-get -y install python3-pip
sudo apt install python-pip
pip install --upgrade pip
sudo pip3 install -r requirements.txt
```

I tried to make the use of this project as simple as possible and you only need a few commands to set it up. Most of the packages you need to install are from the requirements.txt file

```bash
pip3 install -r requirements.txt
```

Now you can begin training. The bot automatically grabs the data in 15 minute periods. The basic structure is:

```bash
python3 train.py <years> [--window-size=<window-size>] [--batch-size=<batch-size>] [--episode-count=<episode-count>] [--model-name=<model-name>] [--pretrained] [--debug]
```


Example Usage:

```bash
python3 train.py 10 --window-size=10 --episode-count=10 --model-name=model_alpha --pretrained --debug
```

I think the rest is pretty self explanatory.

Once you're done training, run the eval script or just run the entire bot:

```bash
eval.py <eval-stock> [--window-size=<window-size>] [--model-name=<model-name>] [--run-bot=<y/n] [--stock-name=<stock-ticker>] [--debug]
```


Example Usage:

```bash
python3 eval.py test --window-size=10 --model-name=model_alpha --run-bot=y --stock-name=GOOGL --debug
```

Now everything should be good to go!

## Credits

All credit for the Q-learning aspect of this bot and general outline is directly forked from [pskrunner14's Bot](https://github.com/pskrunner14/trading-bot)

Using Google's Natural Language API for Sentiment Analysis a copy of their license can be found [here](http://www.apache.org/licenses/LICENSE-2.0)
