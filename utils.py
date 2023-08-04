from typing import Literal

import MetaTrader5 as mt5
from datetime import datetime
from indicators import donchian_channel
import numpy as np
import talib as ta
import pandas as pd


def get_data(pair: str,
             timeframe=mt5.TIMEFRAME_H1,
             from_date: str = '2015-01-01',
             to_date: str = datetime.today().isoformat(),
             date_as_index: bool = True):
    """
    Return data from MetaTrader5
    :param pair: Symbol name (EURUSD)
    :param timeframe: TimeFrame (mt5.TIMEFRAME_H1)
    :param from_date: start date (ISO FORMAT)
    :param to_date: last date (can be just datetime.today()) (ISO FORMAT)
    :param date_as_index: if True, sets column 'time' as index
    :return: price data as Pandas DataFrame
    """
    if not mt5.initialize():
        print('[INFO] Initialize() failed')
        mt5.shutdown()

    from_date = datetime.fromisoformat(from_date)
    to_date = datetime.fromisoformat(to_date)
    data = mt5.copy_rates_range(pair, timeframe, from_date, to_date)
    mt5.shutdown()

    if data is not None:
        data = pd.DataFrame(data)
        data['time'] = pd.to_datetime(data['time'], unit='s')
        data.drop('real_volume', axis=1, inplace=True)
        data.rename(columns={'tick_volume': 'volume'}, inplace=True)
        if date_as_index:
            data.set_index(data['time'], inplace=True)
        return data

    else:
        raise ValueError("It seems MT5 doesn't have such data. Try to pass the closer date to today.")


def get_candle_form(op: pd.Series, hi: pd.Series, lo: pd.Series, cl: pd.Series,
                    atr_period: int = 24, scale_values: bool = True):
    bull = cl > op
    body_size = abs(op - cl)
    candle_size = hi - lo
    upper_wick = np.where(bull, hi - cl, hi - op)
    lower_wick = np.where(bull, op - lo, cl - lo)

    if scale_values:
        atr = ta.ATR(hi, lo, cl, atr_period)
        body_size = body_size / atr
        candle_size = candle_size / atr
        upper_wick = upper_wick / atr
        lower_wick = lower_wick / atr

    return pd.concat([body_size, candle_size, upper_wick, lower_wick],
                     axis=1, keys='body_size, candle_size, upper_wick, lower_wick'.split(', '))


def expand_for_n_candles(df, num_shifts):
    shifted_df = pd.concat([df.shift(i) for i in range(1, num_shifts)], axis=1)
    shifted_df.columns = [f'{col}_shifted_{i}' for i in range(1, num_shifts) for col in df.columns]
    joined_df = pd.concat([df, shifted_df], axis=1)
    joined_df = joined_df.dropna()  # to remove rows with NaN values caused by shifting
    return joined_df


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


def create_filter(data: pd.DataFrame, query: str):
    """
    Create filter, that corresponds to the condition in query 
    and returns np.array, containing 1 and 0.
    1 if condition is True
    Otherwise 0
    """
    mask = data.query(query).index
    return data.index.isin(mask.values).astype(int)
