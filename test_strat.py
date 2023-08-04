from trade_tester import TradeTester
from indicators import level_crosses
import pandas as pd
import numpy as np
import talib as ta
from indicators import donchian_channel, channel_trend, trend_based_on_impulse_candles
from candlestick_patterns import impulse_candles
from utils import create_filter


df = pd.read_csv('eurusd_h1.csv', parse_dates=['dt'])
df.drop('pair', axis=1, inplace=True)

PERIOD = 42
df['ma'] = ta.SMA(ta.TYPPRICE(df['high'], df['low'], df['close']), PERIOD)
trend = np.where(df['ma'] > df['ma'].shift(1),  1,
              np.where(df['ma'] < df['ma'].shift(1), -1,
                                                      0))
df['mfi'] = ta.MFI(df['high'], df['low'], df['close'], df['volume'], 21)
df['fatr'] = ta.ATR(df['high'], df['low'], df['close'], 12)
df['satr'] = ta.ATR(df['high'], df['low'], df['close'], 24)
df['entries'] = level_crosses(df['mfi'], 50)
df.dropna(axis=0, inplace=True)
atr_filter = create_filter(df, query="fatr < satr")

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
tester.add_filters(atr_filter)
tester.set_stoploss_method('bar_extremum', PERIOD)
tester.set_takeprofit_method('atr', PERIOD, 6)
tester.run_strategy(n=PERIOD)
print(tester.form_order_statistic())
tester.show_orders_statistic()
