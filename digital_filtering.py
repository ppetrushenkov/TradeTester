from indicators import impulse_candles
import numpy as np
import pandas as pd
from scipy import signal
import talib as ta
import plotly.graph_objects as go
from indicators import slow_adaptive_trend_line


data = pd.read_csv('eurusd_h1.csv', parse_dates=['dt'])
data = data.iloc[-1000:]
data.drop('pair', axis=1, inplace=True)

PERIOD = 21
cutoff_frequency = 2.0  # Adjust this value based on your specific data
sampling_frequency = 64  # Adjust this value based on your specific data

print(data.shape)
data['MA'] = ta.SMA(data['close'], PERIOD)
data['satl'] = slow_adaptive_trend_line(data['close'])
print(data)

# Create the candlestick trace
candlestick = go.Candlestick(
    x=data.index,
    open=data['open'],
    high=data['high'],
    low=data['low'],
    close=data['close'],
    name='Candlestick'
)

# Create the moving average line trace
ma_line1 = go.Scatter(
    x=data.index,
    y=data['MA'],
    mode='lines',
    name='MA ({})'.format(PERIOD),
    line={'color': 'orange'}
)

# Create the Low-pass filter line trace
ma_line2 = go.Scatter(
    x=data.index,
    y=data['satl'],
    mode='lines',
    name='SATL ({}-{})'.format(cutoff_frequency, sampling_frequency),
    line={'color': 'red'}
)

# Create the layout
layout = go.Layout(
    title='Candlestick Chart with Moving Average',
    xaxis={'title': 'Date'},
    yaxis={'title': 'Price'}
)

# Create the figure and add the traces
fig = go.Figure(data=[candlestick, ma_line1, ma_line2], layout=layout)

# Show the plot
fig.show()

