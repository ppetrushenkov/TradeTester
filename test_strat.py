from trade_tester import TradeTester
from indicators import level_crosses
import pandas as pd
import numpy as np
import talib as ta
from indicators import donchian_channel, channel_trend, trend_based_on_impulse_candles
from candlestick_patterns import impulse_candles


df = pd.read_csv('eurusd_h1.csv', parse_dates=['dt'])
df.drop('pair', axis=1, inplace=True)

PERIOD = 42
df['ma'] = ta.SMA(df['close'], PERIOD)
trend = np.where(df['ma'] > df['ma'].shift(1),  1,
              np.where(df['ma'] < df['ma'].shift(1), -1,
                                                      0))
# upper, middle, lower = donchian_channel(df['high'], df['low'], PERIOD)
# trend = channel_trend(df['high'], df['low'], upper, middle, lower)
# imp = impulse_candles(df['open'].values, df['high'].values, df['low'].values, df['close'].values, PERIOD, 3)
# trend = trend_based_on_impulse_candles(df['open'].values, df['high'].values, df['low'].values, df['close'].values, imp)

df['mfi'] = ta.MFI(df['high'], df['low'], df['close'], df['volume'], PERIOD)
# df['mfi'] = ta.RSI(df['close'], PERIOD)
# df['mfi'] = ta.CCI(df['high'], df['low'], df['close'], PERIOD)
df['entries'] = level_crosses(df['mfi'], 50)
df.dropna(axis=0, inplace=True)

tester = TradeTester()
tester.add_data(
    datetime_data=df['dt'].values, 
    open_data=df['open'].values, 
    high_data=df['high'].values, 
    low_data=df['low'].values, 
    close_data=df['close'].values
)

tester.add_trend(np.array(trend))
tester.add_entries(df['entries'])
# tester.set_stoploss_method('bar_extremum', PERIOD)
# tester.set_stoploss_method('channel', PERIOD)
tester.set_stoploss_method('atr', PERIOD, 1)
tester.set_takeprofit_method('atr', PERIOD, 6)
# tester.set_takeprofit_method('SL ratio', 5)
# tester.set_takeprofit_method('channel', PERIOD*4, 4)
tester.run_strategy(n=PERIOD*2)
print(tester.form_order_statistic())
tester.show_orders_statistic()
