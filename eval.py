"""
Script for evaluating Stock Trading Bot.

Usage:
  eval.py <eval-stock> [--window-size=<window-size>] [--model-name=<model-name>] [--run-bot] [--db-name=<db-name>] [--stock-name=<stock-ticker>] [--natural-lang] [--debug] [--mongo]

Options:
  --window-size=<window-size>   Size of the n-day window stock data representation used as the feature vector. [default: 10]
  --model-name=<model-name>     Name of the pretrained model to use (will eval all models in `models/` if unspecified).
  --run-bot                     Whether you wish to run the trading bot
  --stock-name=<stock-ticker>   The name of the stock (eg. AMD, GE)
  --db-name=<db-name>           The name of the database being used on MongoDB
  --natural-lang                Specifies whether to use Google's Natural Language API or not
  --debug                       Specifies whether to use verbose logs during eval operation.
  --mongo                       Specifies whether to use MongoDB to save trading data

"""

import os
import coloredlogs
import pymongo

from docopt import docopt

import logging

import numpy as np

from tqdm import tqdm
from time import process_time

from trading_bot.agent import Agent
from trading_bot.methods import evaluate_model
import alpaca_trade_api as tradeapi
import time
import datetime

from trading_bot.sentiment import runNewsAnalysis, decide_stock
from trading_bot.utils import (
    get_stock_data,
    format_currency,
    format_position,
    show_eval_result,
    switch_k_backend_device,
    format_sentiment)

from trading_bot.ops import get_state
import creds


# Method to run script for each minute
def decisions(agent, data, api):
    # Initialize Variables
    total_profit = 0
    global orders, collection
    orders = []
    history = []
    agent.inventory = []
    action = None
    sentiments = runNewsAnalysis(stock_name, api, natural_lang)
    state = get_state(data, 0, window_size + 1)

    if mongo:

        # Check for connection errors and retry 30 times
        cnt = 0
        while cnt <= 30:
            try:
                client = creds.getClient()
                db = client[db_name]
                collection = db.get_collection(stock_name)
                break

            except:
                logging.warning("Unable to connect to MongoDB, retrying in 30s (" + str(cnt) + "/30)")
                time.sleep(30)
                cnt += 1
                continue

    # decide_stock()
    t = 0

    # Main While Loop
    while True:

        data_length = len(data) - 1
        is_open = True

        # Checks for if the original 1000 data points were tested
        if t == data_length - 1:

            # Check for connection errors and retry 30 times
            cnt = 0
            while cnt <= 30:

                try:
                    # Wait for market to open.
                    is_open = api.get_clock().is_open
                    break

                except:
                    logging.warning("Error in checking market status, retrying in 30s (" + str(cnt) + "/30)")
                    time.sleep(30)
                    cnt += 1
                    continue

        # Checks for if Market is open
        while not is_open:
            logging.info("Waiting for market to open...")

            # Check for connection errors and retry 30 times
            cnt = 0
            while cnt <= 30:
                try:
                    clock = api.get_clock()
                    opening_time = clock.next_open.replace(tzinfo=datetime.timezone.utc).timestamp()
                    curr_time = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
                    time_to_open = int((opening_time - curr_time) / 60)
                    logging.info("Last days profit: {}".format(format_currency(str(total_profit))))

                    # Countdown timer until market opens
                    while time_to_open > -1:
                        print(str(time_to_open) + " minutes til market open.", end='\r')
                        time.sleep(60)
                        time_to_open -= 1

                    # Alternative timer here
                    # time.sleep(time_to_open * 60)
                    is_open = api.get_clock().is_open
                    break

                except:
                    logging.warning("Error in checking market status, retrying in 30s (" + str(cnt) + "/30)")
                    time.sleep(30)
                    cnt += 1
                    continue

            # Initialization of new day, we only want this to happen once at the beginning of each day
            if is_open:
                logging.info("Market opened.")

                # Runs Analysis on all new sources
                try:
                    sentiments = runNewsAnalysis(stock_name, api, natural_lang)
                except:
                    logging.info("Error Collecting Sentiment")

                if mongo:

                    # Check for connection errors and retry 30 times
                    cnt = 0
                    while cnt <= 30:
                        try:
                            collection2 = db.get_collection(stock_name + "_profit")
                            collection2.insert_one({"Datetime": datetime.date.today() - datetime.timedelta(days=1),
                                                    "Profit": total_profit})
                            break

                        except:
                            logging.warning("Unable to connect to MongoDB, retrying in 30s (" + str(cnt) + "/30)")
                            time.sleep(30)
                            cnt += 1
                            continue

                # Save last day's data
                if action is not None:
                    agent.memory.append((state, action, reward, next_state, True))
                    agent.soft_save()

                # Reinitialize for new day
                total_profit = 0
                orders = []
                history = []
                qty = 0
                agent.inventory = []

                # ****COMMENT THIS OUT IF YOU DON'T WANT TO SELL ALL OF THE STOCKS AT THE BEGINNING OF NEW DAY****
                # Sell all stock using Alpaca API at the beginning of the new day
                if t == data_length - 1:

                    try:
                        qty = api.get_position(stock_name).qty

                    except:
                        logging.warning("Error fetching stock position, may not exist.")

                    # Just checks to see if I'm trying to sell zero or a negative number of stock
                    if int(qty) > 0:
                        submit_order_helper(int(qty), stock_name, 'sell', api)

        # Checks for if the original 1000 data points were tested, if they were it retrieves realtime data
        if t == data_length - 1:
            time.sleep(60)

            # Check for connection errors and retry 30 times
            cnt = 0
            while cnt <= 30:
                try:
                    date = api.get_barset(timeframe='minute', symbols=stock_name, limit=1, end=datetime.datetime.now())
                    break

                except:
                    logging.warning("Unable to retrieve barset, retrying in 30s (" + str(cnt) + "/30)")
                    time.sleep(30)
                    cnt += 1
                    continue

            data.append(date.get(stock_name)[0].c)

        reward = 0
        next_state = get_state(data, t + 1, window_size + 1)

        # select an action
        action = agent.act(state, is_eval=True)

        # BUY
        if action == 1 and sentiments >= 0:

            # Buy using Alpaca API, only if it is realtime data
            if t == data_length - 1:

                agent.inventory.append(data.get(stock_name)[0].c)
                orders.append(submit_order_helper(1, stock_name, 'buy'))
                history.append((date.get(stock_name)[0].c, "BUY"))
                if debug:
                    logging.debug(
                        "Buy at: {}  | Sentiment: {} | Total Profit: {}".format(
                            format_currency(date.get(stock_name)[0].c),
                            format_sentiment(sentiments),
                            format_currency(total_profit)))

            else:
                agent.inventory.append(data[t])

                # Appends and logs
                history.append((data[t], "BUY"))
                if debug:
                    logging.debug(
                        "Buy at: {}  | Sentiment: {} | Total Profit: {}".format(format_currency(data[t]),
                                                                                format_sentiment(sentiments),
                                                                                format_currency(total_profit)))

        # SELL
        elif (action == 2 or sentiments < 0) and len(agent.inventory) > 0:

            # Sell's one stock using Alpaca's API if it is in realtime
            if t == data_length - 1:

                bought_price = agent.inventory.pop(0)
                reward = max(date.get(stock_name)[0].c - bought_price, 0)
                total_profit += date.get(stock_name)[0].c - bought_price

                submit_order_helper(1, stock_name, 'sell')

                history.append((date.get(stock_name)[0].c, "SELL"))

                if debug:
                    logging.debug("Sell at: {} | Sentiment: {} | Position: {}".format(
                        format_currency(date.get(stock_name)[0].c), format_sentiment(sentiments),
                        format_position(date.get(stock_name)[0].c - bought_price)))

            else:
                bought_price = agent.inventory.pop(0)
                reward = max(data[t] - bought_price, 0)
                total_profit += data[t] - bought_price

                # Appends and logs
                history.append((data[t], "SELL"))

                if debug:
                    logging.debug("Sell at: {} | Sentiment: {} | Position: {}".format(
                        format_currency(data[t]), format_sentiment(sentiments),
                        format_position(data[t] - bought_price)))


        # HOLD
        else:

            if t == data_length - 1:

                # Add trading data either in file or in mongo
                if mongo:

                    # Check for connection errors and retry 30 times
                    cnt = 0
                    while cnt <= 30:
                        try:
                            collection.insert_one({"Datetime": datetime.datetime.now(),
                                                   "Action": "HOLD",
                                                   "Price": date.get(stock_name)[0].c})
                            break
                        except:
                            logging.warning(
                                "Unable to insert trade into MongoDB, retrying in 30s (" + str(cnt) + "/30)")
                            time.sleep(30)
                            cnt += 1
                            continue

                else:
                    file = open('data/' + stock_name + "_trading_data.csv", 'a')
                    file.write(str(datetime.datetime.now().strftime("%m/%d/%Y,%H:%M:%S")) + ',HOLD,$' + str(
                        date.get(stock_name)[0].c) + '\n')
                    file.close()

                history.append((date.get(stock_name)[0].c, "HOLD"))

                if debug:
                    logging.debug("Hold at: {} | Sentiment: {} | Total Profit: {}".format(
                        format_currency(date.get(stock_name)[0].c), format_sentiment(sentiments),
                        format_currency(total_profit)))

            else:
                # Appends and logs
                history.append((data[t], "HOLD"))

                if debug:
                    logging.debug("Hold at: {} | Sentiment: {} | Total Profit: {}".format(
                        format_currency(data[t]), format_sentiment(sentiments), format_currency(total_profit)))

        agent.remember(state, action, reward, next_state, False)
        if len(agent.memory) > 32:
            agent.train_experience_replay(32)

        state = next_state
        t += 1


# Submit an order if quantity is above 0.
def submit_order_helper(qty, side, api):
    if int(qty) > 0:
        try:
            api.submit_order(stock_name, qty, side, "market", "day")
            logging.info("Market order of | " + str(qty) + " " + stock_name + " " + side + " | completed.")

            if side == "sell":

                # Add trading data either in file or in mongo
                if mongo:

                    # Check for connection errors and retry 30 times
                    cnt = 0
                    while cnt <= 30:
                        try:
                            collection.insert_one({"Datetime": datetime.datetime.now(),
                                                   "Action": "SELL",
                                                   "Price": date.get(stock_name)[0].c})
                            break

                        except:
                            logging.warning(
                                "Unable to insert trade into MongoDB, retrying in 30s (" + str(cnt) + "/30)")
                            time.sleep(30)
                            cnt += 1
                            continue

                else:
                    file = open('data/' + stock_name + "_trading_data.csv", 'a')
                    file.write(str(datetime.datetime.now().strftime("%m/%d/%Y,%H:%M:%S")) + ',SELL,$' + str(
                        date.get(stock_name)[0].c) + '\n')
                    file.close()

            elif side == "buy":
                # Add trading data either in file or in mongo
                if mongo:

                    # Check for connection errors and retry 30 times
                    cnt = 0
                    while cnt <= 30:
                        try:
                            collection.insert_one({"Datetime": datetime.datetime.now(),
                                                   "Action": "BUY",
                                                   "Price": date.get(stock_name)[0].c})
                            break

                        except:
                            logging.warning(
                                "Unable to insert trade into MongoDB, retrying in 30s (" + str(cnt) + "/30)")
                            time.sleep(30)
                            cnt += 1
                            continue

                else:
                    file = open('data/' + stock_name + "_trading_data.csv", 'a')
                    file.write(str(datetime.datetime.now().strftime("%m/%d/%Y,%H:%M:%S")) + ',BUY,$' + str(
                        date.get(stock_name)[0].c) + '\n')
                    file.close()

        except:
            logging.warning("Order of | " + str(qty) + " " + stock_name + " " + side + " | did not go through.")
    else:
        logging.info("Quantity is 0, order of | " + str(qty) + " " + stock_name + " " + side + " | not completed.")


# Method to actually run the script
def alpaca_trading_bot():
    # Alpaca API
    api = tradeapi.REST()

    # Create Agent Object
    agent = Agent(window_size, pretrained=True, model_name=model_name)

    # Get Ticker from last intraday times from Polygon
    file = open('ticker.csv', 'w')
    file.write('Adj Close\n')

    # Check for connection errors and retry 30 times
    cnt = 0
    while cnt <= 30:
        try:
            # Get date for ticker
            date = api.polygon.historic_agg_v2(stock_name, 1, timespan='minute',
                                               _from=str(datetime.date.today() - datetime.timedelta(days=3)),
                                               to=str(datetime.date.today()), limit=1000).df

            # date = api.get_barset(timeframe='minute', symbols=stock_name, limit=1000, end=datetime.datetime.now())
            break

        except:
            logging.warning("Error retrieving initial 1000 prices, retrying in 30s (" + str(cnt) + "/30)")
            time.sleep(30)
            cnt += 1
            continue

    # Write ticker csv
    for minutes in date['close']:
        file.write(str(minutes))
        file.write('\n')

    file.close()

    data = get_stock_data('ticker.csv')

    # Call actual buy/sell/hold decisions and print result forever
    decisions(agent, data, api)


def main():
    """ Evaluates the stock trading bot.
    Please see https://arxiv.org/abs/1312.5602 for more details.

    Args: [python eval.py --help]
    """
    data = get_stock_data(eval_stock)
    initial_offset = data[1] - data[0]

    # Single Model Evaluation
    if model_name is not None:
        agent = Agent(window_size, pretrained=True, model_name=model_name)
        profit, _ = evaluate_model(agent, data, window_size, debug)
        show_eval_result(model_name, profit, initial_offset)

    # Multiple Model Evaluation
    else:
        for model in os.listdir("models"):
            if os.path.isfile(os.path.join("models", model)):
                agent = Agent(window_size, pretrained=True, model_name=model)
                profit = evaluate_model(agent, data, window_size, debug)
                show_eval_result(model, profit, initial_offset)
                del agent


if __name__ == "__main__":
    args = docopt(__doc__)

    # Arguments
    eval_stock = 'data/' + str(args["<eval-stock>"]) + '.csv'
    window_size = int(args["--window-size"])
    model_name = args["--model-name"]
    run_bot = args['--run-bot']
    stock_name = str(args['--stock-name'])
    natural_lang = args['--natural-lang']
    debug = args["--debug"]
    mongo = args['--mongo']
    db_name = args['--db-name']

    coloredlogs.install(level="DEBUG")
    switch_k_backend_device()

    try:
        main()
    except KeyboardInterrupt:
        print("Aborted")

    # Run the Actual bot
    if run_bot:
        alpaca_trading_bot()
