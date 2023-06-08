from trade_tester import TradeTester
from indicators import level_crosses
import pandas as pd
import numpy as np
import talib as ta


df = pd.read_csv('eurusd_h1.csv', parse_dates=['dt'])
df.drop('pair', axis=1, inplace=True)

PERIOD = 42
df['sma'] = ta.EMA(df['close'], PERIOD)

df['trend'] = np.where(df['sma'] > df['sma'].shift(1),  1,
              np.where(df['sma'] < df['sma'].shift(1), -1,
                                                        0))

df['mfi'] = ta.MFI(df['high'], df['low'], df['close'], df['volume'], PERIOD)
df['entries'] = level_crosses(df['mfi'], 50)
df.dropna(axis=0, inplace=True)

tester = TradeTester(
    trade_data=df,
    trend=df['trend'],
    entries=df['entries']
)
tester.set_stoploss_method('channel', PERIOD)
tester.set_takeprofit_method('atr', PERIOD, 7)
tester.run_strategy(n=42)
print(tester.form_order_statistic())
tester.show_order_statistic()
