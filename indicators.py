from candlestick_patterns import impulse_candles
from scipy import signal
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


def slow_adaptive_trend_line(data):
    weights = np.array([0.0982862174, 0.0975682269, 0.0961401078, 0.0940230544, 0.091243709, 0.0878391006, 
                        0.0838544303, 0.079340635, 0.0743569346, 0.0689666682, 0.0632381578, 0.0572428925, 
                        0.0510534242, 0.0447468229, 0.038395995, 0.0320735368, 0.0258537721, 0.0198005183, 
                        0.0139807863, 0.0084512448, 0.0032639979, -0.0015350359, -0.0059060082, -0.0098190256, 
                        -0.0132507215, -0.0161875265, -0.0186164872, -0.0205446727, -0.0219739146, -0.0229204861, 
                        -0.0234080863, -0.0234566315, -0.0231017777, -0.02237969, -0.0213300463, -0.0199924534, 
                        -0.0184126992, -0.0166377699, -0.0147139428, -0.0126796776, -0.0105938331, -0.008473677, 
                        -0.006384185, -0.0043466731, -0.0023956944, -0.000553518, 0.0011421469, 0.0026845693, 
                        0.0040471369, 0.0052380201, 0.0062194591, 0.0070340085, 0.0076266453, 0.0080376628, 
                        0.0083037666, 0.0083694798, 0.0082901022, 0.0080741359, 0.007754382, 0.0073260526, 
                        0.0068163569, 0.0062325477, 0.0056078229, 0.0049516078, 0.0161380976])
    weighted_avg = np.convolve(data, weights, mode='valid') / np.sum(weights)
    weighted_avg = np.insert(weighted_avg, 0, np.repeat(np.nan, len(weights)-1))
    return weighted_avg

def fast_adaptive_trend_line(data):
    weights = np.array([0.436040945, 0.3658689069, 0.2460452079, 0.1104506886, -0.0054034585, -0.0760367731, -0.0933058722,
                        -0.0670110374, -0.0190795053, 0.0259609206, 0.0502044896, 0.0477818607, 0.0249252327, -0.0047706151,
                        -0.0272432537, -0.0338917071, -0.0244141482, -0.0055774838, 0.0128149838, 0.0226522218, 0.0208778257, 
                        0.0100299086, -0.0036771622, -0.013674485, -0.0160483392, -0.0108597376, -0.0016060704, 0.0069480557, 
                        0.0110573605, 0.0095711419, 0.0040444064, -0.0023824623, -0.0067093714, -0.00720034, -0.004771771, 
                        0.0005541115, 0.000786016, 0.0130129076, 0.0040364019])
    weighted_avg = np.convolve(data, weights, mode='valid') / np.sum(weights)
    weighted_avg = np.insert(weighted_avg, 0, np.repeat(np.nan, len(weights)-1))
    return weighted_avg

def apply_lowpass_filter(data, cutoff_frequency, sampling_frequency):
    nyquist_frequency = 0.5 * sampling_frequency
    normalized_cutoff = cutoff_frequency / nyquist_frequency
    b, a = signal.butter(4, normalized_cutoff, btype='low', analog=False)
    filtered_data = signal.filtfilt(b, a, data)
    return filtered_data