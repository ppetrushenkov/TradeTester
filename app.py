from trade_tester import TradeTester
from indicators import level_crosses, ma_trend
import pandas as pd
import numpy as np
import talib as ta
import streamlit as st
from indicators import donchian_channel, channel_trend, trend_based_on_impulse_candles
from candlestick_patterns import impulse_candles


st.write('Trade Tester')

df = pd.read_csv('eurusd_h1.csv', parse_dates=['dt'])
df.drop('pair', axis=1, inplace=True)

params = st.sidebar.title('Parameters:')
trend_period = st.sidebar.slider('Trend period', 2, 150, value=42)
ind_period = st.sidebar.slider('Indicator period', 2, 150, value=24)
trend_type = st.sidebar.radio('Choose trend type', 
                              ['SMA', 'EMA', 'WMA', 'KAMA', 'MAMA', 
                               'DEMA', 'TEMA', 'TRIMA', 'T3',
                               'HT_TRENDLINE', 'LINREG', 'Impulse', 'Channel'], 
                              horizontal=True)
entries_indicator = st.sidebar.radio('Choose indicator', ['RSI', 'CCI', 'MFI'])
cross_level = st.sidebar.radio('Level to cross', [50, 0])
ma_thresh = st.sidebar.slider('MA Lag', 1, 50, 1)
sl_method = st.sidebar.radio('Choose stop loss method', ['fixed', 'channel', 'atr', 'bar_extremum'])
tp_method = st.sidebar.radio('Choose take profit method', ['fixed', 'channel', 'atr', 'SL ratio'])
sl_value = st.sidebar.slider('SL value', 1, 150, 24)
tp_value = st.sidebar.slider('TP value', 1, 150, 24)
sl_mult = st.sidebar.slider('SL mult', 1, 20, 1)
tp_mult = st.sidebar.slider('TP mult', 1, 20, 6)

if trend_type == 'SMA':
    ma = ta.SMA(df['close'], trend_period)
    trend = ma_trend(ma, ma_thresh)

elif trend_type == 'EMA':
    ma = ta.EMA(df['close'], trend_period)
    trend = ma_trend(ma, ma_thresh)
    
elif trend_type == 'WMA':
    ma = ta.WMA(df['close'], trend_period)
    trend = ma_trend(ma, ma_thresh)

elif trend_type == 'KAMA':
    ma = ta.KAMA(df['close'], trend_period)
    trend = ma_trend(ma, ma_thresh)
    
elif trend_type == 'MAMA':
    ma = ta.MAMA(df['close'], trend_period)
    trend = ma_trend(ma, ma_thresh)
    
elif trend_type == 'T3':
    ma = ta.T3(df['close'], trend_period)
    trend = ma_trend(ma, ma_thresh)

elif trend_type == 'DEMA':
    ma = ta.DEMA(df['close'], trend_period)
    trend = ma_trend(ma, ma_thresh)
    
elif trend_type == 'TEMA':
    ma = ta.TEMA(df['close'], trend_period)
    trend = ma_trend(ma, ma_thresh)

elif trend_type == 'TRIMA':
    ma = ta.TRIMA(df['close'], trend_period)
    trend = ma_trend(ma, ma_thresh)
    
elif trend_type == 'LINREG':
    ma = ta.LINEARREG(df['close'], trend_period)
    trend = ma_trend(ma, ma_thresh)

elif trend_type == 'HT_TRENDLINE':
    ma = ta.HT_TRENDLINE(df['close'])
    trend = ma_trend(ma, ma_thresh)

elif trend_type == 'Impulse':
    imp = impulse_candles(df['open'].values, df['high'].values, df['low'].values, df['close'].values, trend_period, 4)
    trend = trend_based_on_impulse_candles(df['open'].values, df['high'].values, df['low'].values, df['close'].values, imp)

elif trend_type == 'Channel':
    upper, middle, lower = donchian_channel(df['high'], df['low'], trend_period)
    trend = channel_trend(df['high'], df['low'], upper, middle, lower)

if entries_indicator == 'RSI':
    ind = ta.RSI(df['close'], ind_period)
    entries = level_crosses(ind, cross_level)

elif entries_indicator == 'CCI':
    ind = ta.CCI(df['high'], df['low'], df['close'], ind_period)
    entries = level_crosses(ind, cross_level)

elif entries_indicator == 'MFI':
    ind = ta.MFI(df['high'], df['low'], df['close'], df['volume'], ind_period)
    entries = level_crosses(ind, cross_level)

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
tester.add_entries(entries)

if sl_method == 'fixed':
    tester.set_stoploss_method('fixed', sl_value)
elif sl_method == 'bar_extremum':
    tester.set_stoploss_method('bar_extremum', sl_value)
elif sl_method == 'atr':
    tester.set_stoploss_method('atr', sl_value, sl_mult)
elif sl_method == 'channel':
    tester.set_stoploss_method('channel', sl_value)

if tp_method == 'fixed':
    tester.set_takeprofit_method('fixed', tp_value)
elif tp_method == 'SL ratio':
    tester.set_takeprofit_method('SL ratio', tp_mult)
elif tp_method == 'atr':
    tester.set_takeprofit_method('atr', tp_value, tp_mult)
elif tp_method == 'channel':
    tester.set_takeprofit_method('channel', tp_value)

tester.run_strategy(n=trend_period)
st.dataframe(tester.form_order_statistic())
fig = tester.show_orders_statistic()
st.pyplot(fig)
