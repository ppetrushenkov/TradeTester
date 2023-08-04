from tqdm import tqdm
from typing import Literal
from indicators import donchian_channel
import pandas as pd
import talib as ta


def get_update_count(data: pd.DataFrame, candles2use: pd.Series):
    """
    Calculates, how many times we have an update of max/min of specified candle
    data: OHLC data
    candles2use: if equal to 1 or -1, we use this candle
    """
    update_count = {-1: {1: 0, -1: 0},
                    1: {1: 0, -1: 0}}
    hi = data['high'].values
    lo = data['low'].values

    for idx in tqdm(range(data.shape[0])):
        hii = hi[idx]
        loi = lo[idx]
        filter_candle = candles2use[idx]

        if filter_candle == 0:
            continue

        for i in range(1, data.shape[0] - idx):
            hin = hi[idx + i]
            lon = lo[idx + i]

            if filter_candle == 1:
                if lon < loi:
                    update_count[1][-1] += 1
                    break
                elif hin > hii:
                    update_count[1][1] += 1
                    break

            elif filter_candle == -1:
                if hin > hii:
                    update_count[-1][1] += 1
                    break
                elif lon < loi:
                    update_count[-1][-1] += 1
                    break

    return update_count


def extremum_update(data: pd.DataFrame, period: int = 21, method: Literal['channel', 'bands'] = 'bands'):
    """
    Return 1, if the price updates the high border in PERIOD time
    -1, if the price updates the lower border
    and 0 if nothing was updated
    :param data: OHLC data. Columns must be named as 'open', 'high', 'low', 'close'
    :param period: the number of bars, that will be used
    :param method: Channel uses Donchian channel, bands uses Bollinger Bands method
    :return: pd.Series | np.array
    """
    if method == 'channel':
        up, low, mid = donchian_channel(data['high'], data['low'], period)
    elif method == 'bands':
        up, mid, low = ta.BBANDS(data['close'], period)
    else:
        raise ValueError("Choose either 'channel' or 'bands'")
    output = []

    for i in range(data.shape[0]):
        chunk_data = data.iloc[i:i + period, :]
        chunk_up = up[i]
        chunk_low = low[i]

        if any(chunk_data.high > chunk_up):
            output.append(1)
        elif any(chunk_data.low < chunk_low):
            output.append(-1)
        else:
            output.append(0)
    return output


def count_combinations(data, normalize: bool = True):
    """
    Calculate all combinations of 1, 0 and -1.
    Calculate, how many times after each value goes another. 
    """
    combinations = {}

    for i in range(len(data) - 1):
        current = data[i]
        next_value = data[i + 1]

        if current not in combinations:
            combinations[current] = {}

        combinations[current][next_value] = combinations[current].get(next_value, 0) + 1

    # Нормализация значений в процентном отношении
    if normalize:
        total_counts = {}
        for key in combinations:
            total_counts[key] = sum(combinations[key].values())

        for key in combinations:
            for subkey in combinations[key]:
                combinations[key][subkey] = combinations[key][subkey] / total_counts[key] * 100

    return combinations