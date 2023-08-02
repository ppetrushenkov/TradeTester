from tqdm import tqdm
import pandas as pd


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