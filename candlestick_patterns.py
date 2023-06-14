import pandas as pd
import numpy as np
import talib as ta


def impulse_candle(op, hi, lo, cl, period: int = 21, n_split: int = 4):
    """
    Impulse candle is the candle, that have their range greater than average true range and closes around its MAX/MIN values
    """
    atr = ta.ATR(hi, lo, cl, period)
    bar_range = hi - lo
    chunk = bar_range / n_split
    return np.where((bar_range > atr) & (cl > op) & (cl > hi - chunk),  1,
           np.where((bar_range > atr) & (cl < op) & (cl < lo + chunk), -1, 
                                                                                  0))


def pinbar(op, hi, lo, cl):
    bar_range = hi - lo
    chunk = bar_range / 3
    if cl > hi - chunk and op > hi - chunk:
        return 1
    elif cl < lo + chunk and op < lo + chunk:
        return -1
    else:
        return 0


def kangaroo(op, hi, lo, cl, period: int = 21):
    bar_range = hi - lo
    atr = ta.ATR(hi, lo, cl, period)
    if bar_range > atr:
        body = abs(op - cl)
        pb = pinbar(op, hi, lo, cl)
        pass
    # TODO: continue kangaroo!