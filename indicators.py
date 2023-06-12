import talib as ta
import numpy as np
import pandas as pd


def donchian_channel(high: pd.Series, low: pd.Series, period: int = 21) -> pd.DataFrame(columns=['upper', 'lower', 'middle']):
    upper = ta.MAX(high, period)
    lower = ta.MIN(low, period)
    middle = (upper + lower) / 2
    return pd.concat([upper, lower, middle], keys=['upper', 'lower', 'middle'], axis=1)


def channel_trend(data: pd.DataFrame):
    hi = data['high'].values
    lo = data['low'].values

    hi_channel = data['upper'].values
    lo_channel = data['lower'].values

    flag = 0
    trend = []

    for i in range(len(hi)):
        if flag != 1 and hi[i] >= hi_channel[i]:
            flag = 1

        elif flag != -1 and lo[i] <= lo_channel[i]:
            flag = -1

        trend.append(flag)

    return np.array(trend)


def chande_kroll_stop(high: pd.Series, low: pd.Series, close: pd.Series, p, x, q):
    channel = donchian_channel(high, low, p)
    atr = ta.ATR(high, low, close, p)
    upper = channel['lower'] + atr * x
    lower = channel['upper'] - atr * x
    return pd.concat([upper, lower], keys=['up_kroll', 'dn_kroll'], axis=1)


def impulse_candle(op, hi, lo, cl, period: int = 21, n_split: int = 4):
    """
    Impulse candle is the candle, that have their range greater than average true range and closes around its MAX/MIN values
    """
    atr = ta.ATR(hi, lo, cl, period)
    candle_range = hi - lo
    return np.where((candle_range > atr) & (cl > op) & (cl > hi - candle_range / n_split),  1,
           np.where((candle_range > atr) & (cl < op) & (cl < lo + candle_range / n_split), -1, 
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


def level_crossover(current: pd.Series, level: int = 50) -> np.array:
    """
    :returns True if prev value was under specified level and current value is over
    otherwise False
    """
    previous = current.shift(1)
    return (current >= level) & (previous < level)


def level_crossunder(current: pd.Series, level: int = 50) -> np.array:
    """
    :returns True if prev value was over specified level and current value is under
    otherwise False
    """
    previous = current.shift(1)
    return (current <= level) & (previous > level)


def level_crosses(series: pd.Series, level: int = 50) -> np.array:
    """
    Return 1 if series crosses specified level from bottom to top
    Return -1 if crosses from top to bottom
    Otherwise 0
    """
    return np.where(level_crossover(series, level), 1,
                    np.where(level_crossunder(series, level), -1, 0))

def lowest_value(series: pd.Series, period: int) -> int:
    """Return lowest value for specified period"""
    return series[-period:].min()

def highest_value(series: pd.Series, period: int) -> int:
    """Return highest value for specified period"""
    return series[-period:].max()

def drawdown(profit: pd.Series):
    profit = profit.cumsum() + 100
    rolling_max = profit.cummax()
    drawdown = profit / rolling_max - 1.0
    max_drawdown = drawdown.cummin()
    return drawdown, max_drawdown

def sharp_ratio(profit: pd.Series) -> pd.Series:
    return profit.mean() / profit.std()
