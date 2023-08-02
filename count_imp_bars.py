from itertools import groupby
from indicators import impulse_candles
import pandas as pd


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


df = pd.read_csv('eurusd_h1.csv', parse_dates=['dt'])
df.drop('pair', axis=1, inplace=True)

imp = impulse_candles(df['open'], df['high'], df['low'], df['close'], 21, 4)
print(pd.Series(imp).value_counts(normalize=True))

combs = count_combinations(imp)
print(combs)
print(pd.DataFrame(combs).T)