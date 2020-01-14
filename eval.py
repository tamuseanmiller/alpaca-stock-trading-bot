"""
Script for evaluating Stock Trading Bot.

Usage:
  eval.py <eval-stock> [--window-size=<window-size>] [--model-name=<model-name>] [--run-bot=<y/n] [--stock-name=<stock-ticker>] [--debug]

Options:
  --window-size=<window-size>   Size of the n-day window stock data representation used as the feature vector. [default: 10]
  --model-name=<model-name>     Name of the pretrained model to use (will eval all models in `models/` if unspecified).
  --run-bot=<y/n>               Whether you wish to run the trading bot
  --stock-name=<stock-ticker>   The name of the stock (eg. AMD, GE)
  --debug                       Specifies whether to use verbose logs during eval operation.
"""

import os
import coloredlogs

from docopt import docopt

import logging

import numpy as np

from tqdm import tqdm
from time import clock

from trading_bot.agent import Agent
from trading_bot.methods import evaluate_model
import alpaca_trade_api as tradeapi
import time
import datetime

from trading_bot.sentiment import runNewsAnalysis
from trading_bot.utils import (
    get_stock_data,
    format_currency,
    format_position,
    show_eval_result,
    switch_k_backend_device,
    format_sentiment)

from trading_bot.ops import get_state


# Method to run script for each minute
def decisions(agent, data, window_size, debug, stock, api):
    # Runs Analysis on all new sources
    sentiments = runNewsAnalysis(stock, api)

    total_profit = 0
    global orders
    orders = []
    data_length = len(data) - 1

    history = []
    agent.inventory = []

    state = get_state(data, 0, window_size + 1)

    for t in range(data_length):
        reward = 0
        next_state = get_state(data, t + 1, window_size + 1)

        # select an action
        action = agent.act(state, is_eval=True)

        # BUY
        if action == 1 and sentiments >= 0:
            # if action == 1:
            agent.inventory.append(data[t])

            # Buy using Alpaca API
            if t == data_length - 1:
                orders.append(submit_order_helper(1, stock, 'buy', api))

            history.append((data[t], "BUY"))
            if debug:
                logging.debug(
                    "Buy at: {} | Sentiment: {}".format(format_currency(data[t]), format_sentiment(sentiments)))
                # "Buy at: {}".format(format_currency(data[t])))

        # SELL
        elif (action == 2 and len(agent.inventory) > 0) or sentiments < 0:
            # elif action == 2 and len(agent.inventory) > 0:
            bought_price = agent.inventory.pop(0)
            reward = max(data[t] - bought_price, 0)
            total_profit += data[t] - bought_price

            # Sell all stock using Alpaca API
            if (t == data_length - 1) and len(orders) is not 0:
                qty = api.get_position(stock).qty
                submit_order_helper(qty, stock, 'sell', api)
                orders.pop()

            history.append((data[t], "SELL"))
            if debug:
                logging.debug("Sell at: {} | Sentiment: {} | Position: {}".format(
                    format_currency(data[t]), format_sentiment(sentiments), format_position(data[t] - bought_price)))
                # format_currency(data[t]), format_position(data[t] - bought_price)))


        # HOLD
        else:
            history.append((data[t], "HOLD"))
            if debug:
                logging.debug("Hold at: {} | Sentiment: {}".format(
                    format_currency(data[t]), format_sentiment(sentiments)))
                # format_currency(data[t])))

        done = (t == data_length - 1)
        agent.memory.append((state, action, reward, next_state, done))
        if len(agent.memory) > 32:
            agent.train_experience_replay(32)

        state = next_state
        if done:
            agent.soft_save()
            return total_profit, history


# Submit an order if quantity is above 0.
def submit_order_helper(qty, stock, side, api):
    if int(qty) > 0:
        try:
            api.submit_order(stock, qty, side, "market", "day")
            print("Market order of | " + str(qty) + " " + stock + " " + side + " | completed.")
        except:
            print("Order of | " + str(qty) + " " + stock + " " + side + " | did not go through.")
    else:
        print("Quantity is 0, order of | " + str(qty) + " " + stock + " " + side + " | not completed.")


# Method to actually run the script
def alpaca_trading_bot(stock_name, window_size=10, model_name='model_debug'):

    # Alpaca API
    api = tradeapi.REST()

    agent = Agent(window_size, pretrained=True, model_name=model_name)

    # Main while loop
    while True:

        # Wait for market to open.
        print("Waiting for market to open...")
        is_open = api.get_clock().is_open
        while not is_open:
            clock = api.get_clock()
            opening_time = clock.next_open.replace(tzinfo=datetime.timezone.utc).timestamp()
            curr_time = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            time_to_open = int((opening_time - curr_time) / 60)
            print(str(time_to_open) + " minutes til market open.")
            time.sleep(60)
            is_open = api.get_clock().is_open
        print("Market opened.")

        # Get Ticker from last intraday times from Polygon
        file = open('ticker.csv', 'w')
        file.write('Adj Close\n')

        # Get date for ticker
        today = datetime.date.today()
        days = datetime.date.today() - datetime.timedelta(days=500)
        date = api.get_barset(timeframe='15Min', symbols=stock_name, limit=1000, end=datetime.datetime.now())

        # print(date)

        # Write ticker csv
        for minutes in date.get(stock_name):
            file.write(str(minutes.c))
            file.write('\n')

        file.close()

        data = get_stock_data('ticker.csv')
        initial_offset = data[1] - data[0]

        # Call actual buy/sell/hold decisions and print result
        profit, history = decisions(agent, data, window_size, debug, stock_name, api)
        show_eval_result(model_name, profit, initial_offset)

        # Wait for next cycle
        time.sleep(1700)


def main(eval_stock, window_size, model_name, debug):
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
    run_bot = str(args['--run-bot'])
    stock_name = str(args['--stock-name'])
    debug = args["--debug"]

    coloredlogs.install(level="DEBUG")
    switch_k_backend_device()

    try:
        main(eval_stock, window_size, model_name, debug)
    except KeyboardInterrupt:
        print("Aborted")

    # Run the Actual bot
    if run_bot == 'y' or run_bot == 'Y':
        alpaca_trading_bot(stock_name, window_size, model_name)
