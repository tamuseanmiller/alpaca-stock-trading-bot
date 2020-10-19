import os
import math
import logging

import numpy as np

global block

def sigmoid(x):
    """Performs sigmoid operation
    """
    try:
        if x < 0:
            return 1 - 1 / (1 + math.exp(x))
        return 1 / (1 + math.exp(-x))
    except Exception as err:
        print("Error in sigmoid: " + err)


def get_state(data, t, n_days):
    """Returns an n-day state representation ending at time t
    """
    global block
    d = t - n_days + 1
    try:
        block = data[d: t + 1] if d >= 0 else -d * [data[0]] + data[0: t + 1]  # pad with t0
    except IndexError:
        print('Hmmmmm... Right now im getting an IndexError. Which means its either the stock market is not open, in which case i would ask you to wait until the markets open, or its an internal error, which you have to investigate, [Line 26, File trading_bot/ops]')
        #block = -d * [data[0]] + data[0: t + 1]
    res = []
    for i in range(n_days - 1):
        res.append(sigmoid(block[i + 1] - block[i]))
    return np.array([res])
