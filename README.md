# Trade Tester
## Info:
This app helps you backtest trading strategies for financials markets! It is fast and easy to use - you can set trends and entry points, set stop loss and take profit levels. Once you've done, the app will return you a clear statistic and overview of the strategy including `Win/Lose Ratio`, `Profit/Loss Ratio`, `Drawdown`, `Sharp Ratio` etc.

It also shows a graphical overview of returns distribution, account gain etc.

This app doesn't allow to set initial account or order size, because it was made mainly just to get statistic of how many trades was won/lose, its ratio and gain in pips.

---
## How to use:
To run strategy you may use whatever indicator you want. The only condition you need to do is to label the data, where you think the trend is and where are entries.

Here the values, that Trade Tester accepts:
- Trade data
- Trend
- Entries
- Set stop loss
- Set take profit
- Points (1 pip for an financial instrument)
- Show log (prints trades if True)

## Trade data
Trade Tester takes a pandas DataFrame as a trade data. Pandas DataFrame must contains the following columns: dt (datetime column), open, high, low, close
## Trend
Here you must to determine, where the trend is up and where is down. For uptrend uses `1`, for downtrend `0`. For example we may use simple moving average (SMA): if price is above sma -> `1`, if price below sma -> `-1` else -> `0`.

> So the Trend data is a pandas Series data, that contains 1, -1 and 0 values.

## Entries
The same idea here, 1 - if we have `buy` condition, -1 - if `sell` condition, else 0. Simple example - if indicator crosses specified level from bottom to top, it means we buy instrument.

> 1 - buy condition, -1 - sell condition, 0 - nothing

## Set stop loss and take profit
### Stop loss
There is 4 implemented methods, that Trade Tester can handle:
* Fixed
* Bar extremum
* Channel
* ATR

To set stop loss you need to use `set_stoploss_method(kind, value, mult)`
- `Fixed` method allows you to set fixed value as stop level, where order will be closed. For example `tester.set_stoploss_method('fixed', 500)` will always set stop loss level on 500 pips higher/lower order.
- `Bar extremum` will set stop level below executed bar or over executed bar.
- `Channel` will set stop level below/over the lowest/highers value for last N bars
- `ATR` calculates an average range for instrument and set `SL` on `ATR * mult` value below/over order. `Mult` variable is optional and uses just for `ATR` method.

### Take profit
As much as the stop loss method, the `set_takeprofit_method()` have 4 implemented methods:
* Fixed
* Channel
* ATR
* SL Ratio

- `Fixed` method is just fixed pips that you want to get
- `Channel` method will set `TP` level on the highest value for N previous bars for `buy order` and on the lowest value for `sell order`.
- `ATR` as much as stop loss method sets `TP` level on `ATR * mult` below/over executed order.
- `SL Ratio` sets `TP` on level, that greated `SL` in `value` times.

---
## Form statistic about strategy

To form statistic you need to run strategy via `tester.run_strategy(n=N)`. Then you can get statistic using `tester.form_order_statistic()`

|                    |     statistic |
|:-------------------|--------------:|
| Orders count:      |  1952         |
| Win %:             |    45.2336    |
| Lose %:            |    45.9813    |
| Canceled %:        |     8.78505   |
| Avg Profit (pips): |   554.749     |
| Avg Loss (pips):   |  -467.152     |
| PnL order ratio:   |     0.98374   |
| PnL profit ratio:  |     1.18751   |
| Total (pips):      | 77319.3       |
| Drawdown %:        |   -11.1055    |
| Sharp Ratio:       |     0.0608114 |

## Plot statistic about strategy
To plot statistic run `tester.show_order_statistic()`

![alt text](https://github.com/ppetrushenkov/TradeTester/blob/main/mfi_statistic.png?raw=true)

---
## Example:
1. Load trade data
```
df = pd.read_csv('eurusd_h1.csv', parse_dates=['dt'])
df.drop('pair', axis=1, inplace=True)
PERIOD = 42
```
2. Set trend
```
df['sma'] = ta.EMA(df['close'], PERIOD)
df['trend'] = np.where(df['sma'] > df['sma'].shift(1),  1,
              np.where(df['sma'] < df['sma'].shift(1), -1,
                                                        0))
```
3. Set entries
```
df['mfi'] = ta.MFI(df['high'], df['low'], df['close'], df['volume'], PERIOD)
df['entries'] = level_crosses(df['mfi'], 50)
df.dropna(axis=0, inplace=True)
```
4. Pass parameters into Trade Tester
```
tester = TradeTester(
    trade_data=df,
    trend=df['trend'],
    entries=df['entries']
)
tester.set_stoploss_method('channel', PERIOD)
tester.set_takeprofit_method('atr', PERIOD, 7)
```
5. Run strategy
```
tester.run_strategy(n=42)
```
6. Get statistics
```
print(tester.form_order_statistic())
tester.show_order_statistic()
```