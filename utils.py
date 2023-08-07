from typing import Literal
from datetime import datetime
from indicators import donchian_channel
import numpy as np
import talib as ta
import pandas as pd


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


def create_filter(data: pd.DataFrame, query: str):
    """
    Create filter, that corresponds to the condition in query 
    and returns np.array, containing 1 and 0.
    1 if condition is True
    Otherwise 0
    """
    mask = data.query(query).index
    return data.index.isin(mask.values).astype(int)
