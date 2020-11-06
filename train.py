# """
# Script for training Stock Trading Bot.
#
# Usage:
#   train.py <months> [--window-size=<window-size>]
#     [--batch-size=<batch-size>] [--episode-count=<episode-count>]
#     [--model-name=<model-name>] [--pretrained] [--debug] [--stock-name=<stock-name>]
#
# Options:
#   --window-size=<window-size>       Size of the n-day window stock data representation used as the feature vector. [default: 10]
#   --batch-size=<batch-size>         Number of samples to train on in one mini-batch during training. [default: 16]
#   --episode-count=<episode-count>   Number of trading episodes to use for training. [default: 50]
#   --model-name=<model-name>         Name of the pretrained model to use (will eval all models in `models/` if unspecified). [default: model_debug]
#   --pretrained                      Specifies whether to continue training a previously trained model (reads `model-name`).
#   --debug                           Specifies whether to use verbose logs during eval operation.
#   --stock-name=<stock-name>         Specifies the specific stock to train
# """
#
# import logging
# import datetime
# import time
#
# import coloredlogs
#
# from docopt import docopt
#
# import alpaca_trade_api as tradeapi
# from trading_bot.agent import Agent
# from trading_bot.methods import train_model, evaluate_model
# from trading_bot.utils import (
#     get_stock_data,
#     format_currency,
#     format_position,
#     show_train_result,
#     switch_k_backend_device
# )
#
#
# def main(window_size, batch_size, ep_count, model_name, pretrained, debug):
#     """ Trains the stock trading bot using Deep Q-Learning.
#     Please see https://arxiv.org/abs/1312.5602 for more details.
#
#     Args: [python train.py --help]
#     """
#     agent = Agent(window_size, pretrained=pretrained, model_name=model_name)
#
#     train_data = get_stock_data('data/training.csv')
#     val_data = get_stock_data('data/test.csv')
#
#     initial_offset = val_data[1] - val_data[0]
#
#     for episode in range(1, ep_count + 1):
#         train_result = train_model(agent, episode, train_data, ep_count=ep_count,
#                                    batch_size=batch_size, window_size=window_size)
#         val_result, _ = evaluate_model(agent, val_data, window_size, debug)
#         show_train_result(train_result, val_result, initial_offset)
#
#     agent.soft_save()
#
#
# if __name__ == "__main__":
#     args = docopt(__doc__)
#
#     months = args["<months>"]
#     window_size = int(args["--window-size"])
#     batch_size = int(args["--batch-size"])
#     ep_count = int(args["--episode-count"])
#     model_name = args["--model-name"]
#     pretrained = args["--pretrained"]
#     debug = args["--debug"]
#     stock_name = args["--stock-name"]
#
#     api = tradeapi.REST()
#     today = datetime.datetime.today()
#
#     coloredlogs.install(level="DEBUG")
#     switch_k_backend_device()
#
#     ticker = stock_name
#     tickerInput = []
#
#     # Iterate over past
#     past = datetime.date.today() - datetime.timedelta(days=10)
#
#     # Open training file
#     file = open('data/training.csv', 'w')
#
#     file.write('Adj Close\n')
#
#     # Iterate every ticker through the number of months
#     for iterations in range(int(months)*3):
#
#         # Check for connection errors and retry 30 times
#         cnt = 0
#         while cnt <= 30:
#
#             try:
#                 # Grabs three days worth of data
#                 data = api.polygon.historic_agg_v2(stock_name, 1, 'hour', _from=past - datetime.timedelta(days=10),
#                                                    to=past, limit=5000).df
#                 break
#
#             except:
#                 logging.debug("Error connecting to Polygon, retrying in 30s (" + str(cnt) + "/30)")
#                 time.sleep(30)
#                 cnt += 1
#                 continue
#
#         past = past - datetime.timedelta(days=10)
#         # print(data)
#         # Writes c-values
#         for group in data['close']:
#             tickerInput.append(group)
#             # file.write(str(group) + '\n')
#
#     for i in range(len(tickerInput) - 1, 0, -1):
#         file.write(str(tickerInput[i]) + "\n")
#     file.close()
#
#     # Open test file
#     file = open('data/test.csv', 'w')
#
#     file.write('Adj Close\n')
#
#     # Check for connection errors and retry 30 times
#     cnt = 0
#     while cnt <= 30:
#
#         try:
#             # 3 days of info
#             data = api.polygon.historic_agg_v2(stock_name, 1, 'hour',
#                                                _from=str(today.date() - datetime.timedelta(days=10)),
#                                                to=str(today.date())).df
#             break
#
#         except:
#             logging.debug("Error connecting to Polygon, retrying in 30s (" + str(cnt) + "/30)")
#             time.sleep(30)
#             cnt += 1
#             continue
#
#     # Writes c-values
#     for group in data['close']:
#         file.write(str(group) + '\n')
#     file.close()
#
# try:
#     main(window_size, batch_size, ep_count, model_name, pretrained, debug)
# except KeyboardInterrupt:
#     print("Aborted!")

"""
Script for training Stock Trading Bot.

Usage:
  train.py <months> [--strategy=<strategy>]
    [--window-size=<window-size>] [--batch-size=<batch-size>]
    [--episode-count=<episode-count>] [--model-name=<model-name>]
    [--stock-name=<stock-name>] [--pretrained] [--debug]

Options:
  --strategy=<strategy>             Q-learning strategy to use for training the network. Options:
                                      `dqn` i.e. Vanilla DQN,
                                      `t-dqn` i.e. DQN with fixed target distribution,
                                      `double-dqn` i.e. DQN with separate network for value estimation. [default: t-dqn]
  --window-size=<window-size>       Size of the n-day window stock data representation
                                    used as the feature vector. [default: 10]
  --batch-size=<batch-size>         Number of samples to train on in one mini-batch
                                    during training. [default: 32]
  --episode-count=<episode-count>   Number of trading episodes to use for training. [default: 50]
  --model-name=<model-name>         Name of the pretrained model to use. [default: model_debug]
  --stock-name=<stock-name>         Name of Stock
  --pretrained                      Specifies whether to continue training a previously
                                    trained model (reads `model-name`).
  --debug                           Specifies whether to use verbose logs during eval operation.
"""

import logging
import coloredlogs
import datetime
import time

from docopt import docopt
import alpaca_trade_api as tradeapi

from trading_bot.agent import Agent
from trading_bot.methods import train_model, evaluate_model
from trading_bot.utils import (
    get_stock_data,
    format_currency,
    format_position,
    show_train_result,
    switch_k_backend_device
)


def main(train_stock, val_stock, window_size, batch_size, ep_count,
         strategy="t-dqn", model_name="model_debug", pretrained=False,
         debug=False):
    """ Trains the stock trading bot using Deep Q-Learning.
    Please see https://arxiv.org/abs/1312.5602 for more details.

    Args: [python train.py --help]
    """
    agent = Agent(window_size, strategy=strategy, pretrained=pretrained, model_name=model_name)

    train_data = get_stock_data(train_stock)
    val_data = get_stock_data(val_stock)

    initial_offset = val_data[1] - val_data[0]

    for episode in range(1, ep_count + 1):
        train_result = train_model(agent, episode, train_data, ep_count=ep_count,
                                   batch_size=batch_size, window_size=window_size)
        val_result, _ = evaluate_model(agent, val_data, window_size, debug)
        show_train_result(train_result, val_result, initial_offset)


if __name__ == "__main__":
    args = docopt(__doc__)

    months = args["<months>"]
    strategy = args["--strategy"]
    window_size = int(args["--window-size"])
    batch_size = int(args["--batch-size"])
    ep_count = int(args["--episode-count"])
    model_name = args["--model-name"]
    pretrained = args["--pretrained"]
    debug = args["--debug"]
    stock_name = args["--stock-name"]

    api = tradeapi.REST()
    today = datetime.datetime.today()

    coloredlogs.install(level="DEBUG")
    switch_k_backend_device()

    ticker = stock_name
    tickerInput = []

    # Iterate over past
    past = datetime.date.today() - datetime.timedelta(days=10)

    # Open training file
    file = open('data/training.csv', 'w')

    file.write('Adj Close\n')

    # Iterate every ticker through the number of months
    for iterations in range(int(months) * 3):

        # Check for connection errors and retry 30 times
        cnt = 0
        while cnt <= 30:

            try:
                # Grabs three days worth of data
                data = api.polygon.historic_agg_v2(stock_name, 1, 'hour', _from=past - datetime.timedelta(days=10),
                                                   to=past, limit=5000).df
                break

            except:
                logging.debug("Error connecting to Polygon, retrying in 30s (" + str(cnt) + "/30)")
                time.sleep(30)
                cnt += 1
                continue

        past = past - datetime.timedelta(days=10)
        # print(data)
        # Writes c-values
        for group in data['close']:
            tickerInput.append(group)
            # file.write(str(group) + '\n')

    for i in range(len(tickerInput) - 1, 0, -1):
        file.write(str(tickerInput[i]) + "\n")
    file.close()

    # Open test file
    file = open('data/test.csv', 'w')

    file.write('Adj Close\n')

    # Check for connection errors and retry 30 times
    cnt = 0
    while cnt <= 30:

        try:
            # 3 days of info
            data = api.polygon.historic_agg_v2(stock_name, 1, 'hour',
                                               _from=str(today.date() - datetime.timedelta(days=10)),
                                               to=str(today.date())).df
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

coloredlogs.install(level="DEBUG")
switch_k_backend_device()

try:
    main("data/training.csv", "data/test.csv", window_size, batch_size,
         ep_count, strategy=strategy, model_name=model_name,
         pretrained=pretrained, debug=debug)
except KeyboardInterrupt:
    print("Aborted!")
