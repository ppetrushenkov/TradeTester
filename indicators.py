from candlestick_patterns import impulse_candles
import talib as ta
import numpy as np
import pandas as pd


def donchian_channel(high: pd.Series, low: pd.Series, period: int = 21):
    upper = ta.MAX(high, period)
    lower = ta.MIN(low, period)
    middle = (upper + lower) / 2
    return upper, middle, lower


def channel_trend(high: pd.Series, low: pd.Series, upper: pd.Series, middle: pd.Series, lower: pd.Series):
    hi = high.values
    lo = low.values

    hi_channel = upper.values
    lo_channel = lower.values
    mi_channel = middle.values

    flag = 0
    trend = []

    for i in range(len(hi)):
        if flag != 1 and hi[i] >= hi_channel[i]:
            if lo[i] > mi_channel[i]:
                flag = 1
            else:
                flag = 0

        elif flag != -1 and lo[i] <= lo_channel[i]:
            if hi[i] < mi_channel[i]:
                flag = -1
            else:
                flag = 0

        trend.append(flag)

    return np.array(trend)

def trend_based_on_impulse_candles(op: np.ndarray, hi: np.ndarray, lo: np.ndarray, cl: np.ndarray, imp: np.ndarray):
    flag = 0
    current_level = 0
    trend = []

    for i in range(len(op)):
        if imp[i] == 1:  # if current candle is impulse
            current_level == lo[i]
            flag = 1
        elif imp[i] == -1:
            current_level == hi[i]
            flag = -1
        else:
            if flag == 1 and cl[i] < current_level and imp[i] == -1:
                flag = -1
            elif flag == -1 and cl[i] > current_level and imp[i] == 1:
                flag = 1
            elif flag == 1 and cl[i] < current_level:
                flag = 0
            elif flag == -1 and cl[i] > current_level:
                flag = 0
        trend.append(flag)
    return trend

def trend_on_sessions(dt_data: pd.Series, close: pd.Series, session_hour: int = 9):
    close.resample('1h')

def chande_kroll_stop(high: pd.Series, low: pd.Series, close: pd.Series, p, x, q):
    channel = donchian_channel(high, low, p)
    atr = ta.ATR(high, low, close, p)
    upper = channel['lower'] + atr * x
    lower = channel['upper'] - atr * x
    return pd.concat([upper, lower], keys=['up_kroll', 'dn_kroll'], axis=1)


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
    return drawdown * 100, max_drawdown * 100

def sharp_ratio(profit: pd.Series) -> pd.Series:
    return profit.mean() / profit.std()

def linreg_trend(ma, angle: int = 30):
    ma = ma * 1e4
    return np.where(ma > angle, 1,
                    np.where(ma < angle, -1, 0))

def ma_trend(ma, thresh: int = 1):
    trend = np.where(ma > ma.shift(thresh),  1,
            np.where(ma < ma.shift(thresh), -1,
                                        0))
    return trend
