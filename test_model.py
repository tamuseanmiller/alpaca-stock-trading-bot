"""
Script for evaluating Stock Trading Bot.

Usage:
  test_model.py [--model-name=<model-name>] [--debug]

Options:
  --model-name=<model-name>     Name of the pretrained model to use (will eval all models in `models/` if unspecified).
  --debug                       Specifies whether to use verbose logs during eval operation.
"""

import os
import coloredlogs

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
import os

from trading_bot.utils import (
    get_stock_data,
    format_currency,
    format_position,
    show_eval_result,
    switch_k_backend_device,
    format_sentiment)

from trading_bot.ops import get_state


def main(model_name, debug):
    """ Evaluates the stock trading bot.
    Please see https://arxiv.org/abs/1312.5602 for more details.

    Args: [python test_model.py --help]
    """
    global profit
    data = get_stock_data("data/test_model.csv")
    initial_offset = data[1] - data[0]

    # Single Model Evaluation
    if model_name is not None:
        agent = Agent(10, pretrained=True, model_name=model_name)
        profit, _ = evaluate_model(agent, data, 10, debug)
        show_eval_result(model_name, profit, initial_offset)

    return profit


if __name__ == "__main__":
    args = docopt(__doc__)

    # Arguments
    model_name = args["--model-name"]
    debug = args["--debug"]

    api = tradeapi.REST()
    coloredlogs.install(level="DEBUG")
    switch_k_backend_device()

    stocks = ['AAPL', 'MSFT', 'AMZN', 'GOOG', 'GOOGL', 'BABA', 'FB', 'V']

    profit = 0.0

    for i in stocks:

        # Open test file
        file = open('data/test_model.csv', 'w')
        file.write('Adj Close\n')

        # Check for connection errors and retry 30 times
        cnt = 0
        while cnt <= 30:

            try:
                # 3 days of info
                data = api.polygon.historic_agg_v2(i, 1, 'minute',
                                                   _from=str(
                                                       datetime.datetime.today().date() - datetime.timedelta(days=5)),
                                                   to=str(datetime.datetime.today().date()), limit=50).df
                break

            except:
                logging.debug("Error connecting to Polygon, retrying in 30s (" + str(cnt) + "/30)")
                time.sleep(30)
                cnt += 1
                continue

        # Writes c-values
        for group in data['close']:
            file.write(str(group) + '\n')
        file.close()

        try:
            profit += main(model_name, debug)
        except KeyboardInterrupt:
            print("Aborted")

    profit /= len(stocks)

    logging.info('Average Profit: {}\n'.format(format_position(profit)))
