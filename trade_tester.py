from dataclasses import dataclass
from typing import Literal
from tqdm import tqdm
from indicators import lowest_value, highest_value
from indicators import drawdown, sharp_ratio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import talib as ta
plt.style.use('seaborn-v0_8-whitegrid')


@dataclass
class Order:
    bar_id: int
    order_status: str
    order_dir: str
    open_dt: str
    close_dt: str
    open_price: float
    close_price: float
    tp: float
    sl: float


class TradeTester:
    def __init__(self,
                 trade_data,
                 trend,
                 entries,
                 points: float = 0.00001,
                 show_log: bool = False):
        
        # Data
        self.dt = trade_data['dt'].values
        self.op = trade_data['open'].values
        self.hi = trade_data['high'].values
        self.lo = trade_data['low'].values
        self.cl = trade_data['close'].values

        self.trend = trend.values
        self.entries = entries.values

        # Stop Loss and Take Profit Parameters
        self.sl_method = None
        self.sl_value = None
        self.tp_method = None
        self.tp_value = None
        self.sl_mult = 2
        self.tp_mult = 5

        # Order Parameters
        self.in_market = False
        self.order = None
        self.orderBook = {
            'bar_id': [],
            'order_dir': [],
            'open_dt': [],
            'open_price': [],
            'close_dt': [],
            'close_price': [],
            'status': [],
            'profit': []
        }
        self.orderBookDf = None

        self.thresh = 5 * points
        self.points = points
        self.show_log = show_log
    
    def set_stoploss_method(self, kind: Literal['fixed', 'channel', 'atr', 'bar_extremum'], value: int | float, mult: int = 2):
        self.sl_method = kind
        self.sl_value = value
        if kind == 'atr':
            self.sl_mult = mult

    def set_takeprofit_method(self, kind: Literal['fixed', 'channel', 'atr', 'SL ratio'], value: int | float, mult: int = 3):
        self.tp_method = kind
        self.tp_value = value
        if kind == 'atr':
            self.tp_mult = mult

    def __get_sl(self, idx: int, trade_dir: int):
        """
        Return the price level, where stop loss will be set
        idx: Bar index with trade
        trade_dir: 1 or -1
            1: Buy
            -1: Sell
        """
        if self.sl_method == 'fixed':
            if trade_dir == 1:
                return self.cl[idx] - self.sl_value * self.points
            else:
                return self.cl[idx] + self.sl_value * self.points
        
        elif self.sl_method == 'bar_extremum':
            if trade_dir == 1:
                return self.lo[idx] - self.thresh
            else:
                return self.hi[idx] + self.thresh
            
        elif self.sl_method == 'atr':
            period = self.sl_value + 1
            atr = ta.ATR(self.hi[idx-period:idx],
                        self.lo[idx-period:idx],
                        self.cl[idx-period:idx],
                        self.sl_value)[-1]
            if trade_dir == 1:
                return self.lo[idx] - atr * self.sl_mult
            else:
                return self.hi[idx] + atr * self.sl_mult
        
        elif self.sl_method == 'channel':
            if trade_dir == 1:
                return lowest_value(self.lo[:idx], self.sl_value)
            else:
                return highest_value(self.hi[:idx], self.sl_value)

    def __get_tp(self, idx: int, trade_dir: int):
        """
        Return the price level, where take profit will be set
        idx: Bar index with trade
        trade_dir: 1 or -1
            1: Buy
            -1: Sell
        """
        if self.tp_method == 'fixed':
            if trade_dir == 1:
                return self.hi[idx] + self.tp_value * self.points
            else:
                return self.lo[idx] - self.tp_value * self.points
        
        elif self.tp_method == 'atr':
            period = self.tp_value + 1
            atr = ta.ATR(self.hi[idx-period:idx],
                        self.lo[idx-period:idx],
                        self.cl[idx-period:idx],
                        self.tp_value)[-1]
            if trade_dir == 1:
                return self.hi[idx] + atr * self.tp_mult
            else:
                return self.lo[idx] - atr * self.tp_mult
        
        elif self.tp_method == 'channel':
            if trade_dir == 1:
                return highest_value(self.hi[:idx], self.tp_value)
            else:
                return lowest_value(self.lo[:idx], self.tp_value)
        
        elif self.tp_method == 'SL ratio':
            if trade_dir == 1:
                sl = self.__get_sl(idx, 1)
                sl_distance = abs(self.hi[idx] - sl)
                return self.hi[idx] + sl_distance * self.tp_value
            else:
                sl = self.__get_sl(idx, -1)
                sl_distance = abs(self.lo[idx] - sl)
                return self.lo[idx] - sl_distance * self.tp_value

    def __calculate_profit(self, entry, close, direction):
        return close - entry if direction == 'buy' else entry - close
    
    def __print_log(self, log, idx=None):
        if self.show_log:
            dt = self.dt[idx] if idx else ''
            print(f'[INFO, {dt}]', log)

    def run_strategy(self, n):
        # iterate through each bar
        for idx in tqdm(range(n, len(self.cl) - n)):
            # If uptrend and BUY condition
            if not self.in_market:
                if self.trend[idx] == 1 and self.entries[idx] == 1:
                    sl = self.__get_sl(idx, 1)
                    tp = self.__get_tp(idx, 1)
                    self.order = Order(order_status='stop',
                                    order_dir='buy',
                                    open_dt=self.dt[idx],
                                    open_price=self.hi[idx] + self.thresh,
                                    bar_id=idx,
                                    close_price=None,
                                    close_dt=None,
                                    sl=sl,
                                    tp=tp)
                    self.in_market = True
                    self.__print_log(f'BUY ORDER PENDED at {self.order.open_price}')
                
                # If downtrend and SELL condition
                elif self.trend[idx] == -1 and self.entries[idx] == -1:
                    sl = self.__get_sl(idx, -1)
                    tp = self.__get_tp(idx, -1)
                    self.order = Order(order_status='stop',
                                    order_dir='sell',
                                    open_dt=self.dt[idx],
                                    open_price=self.lo[idx] - self.thresh,
                                    bar_id=idx,
                                    close_price=None,
                                    close_dt=None,
                                    sl=sl,
                                    tp=tp)
                    self.in_market = True
                    self.__print_log(f'SELL ORDER PENDED at {self.order.open_price}', idx)

            # If order was set
            elif self.in_market:
                for i in range(n):
                    # Work with pended orders
                    if self.order.order_status == 'stop':
                        if self.order.order_dir == 'buy':
                            if self.hi[idx + i] > self.order.open_price:
                                self.order.order_status = 'in market'
                                self.__print_log(f'ORDER IN MARKET at {self.order.open_price}', idx)
                                
                        elif self.order.order_dir == 'sell':
                            if self.lo[idx + i] < self.order.open_price:
                                self.order.order_status = 'in market'
                                self.__print_log(f'ORDER IN MARKET at {self.order.open_price}', idx)

                    # Work with market orders
                    elif self.order.order_status == 'in market':
                        # if BUY order
                        if self.order.order_dir == 'buy':
                            if self.lo[idx + i] <= self.order.sl:
                                self.close_order(self.order.sl, self.dt[idx + i], 'sl')
                                break
                            elif self.hi[idx + i] >= self.order.tp:
                                self.close_order(self.order.tp, self.dt[idx + i], 'tp')
                                break
                        # if SELL order
                        elif self.order.order_dir == 'sell':
                            if self.hi[idx + i] >= self.order.sl:
                                self.close_order(self.order.sl, self.dt[idx + i], 'sl')
                                break
                            elif self.lo[idx + i] <= self.order.tp:
                                self.close_order(self.order.tp, self.dt[idx + i], 'tp')
                                break

                    # If order still in work
                    if i == n - 1:
                        if self.order.order_status == 'stop':
                            self.close_order(self.order.open_price, self.dt[idx + i], 'canceled')
                        if self.order.order_status == 'in market':
                            self.close_order(self.cl[idx + i], self.dt[idx + i], 'closed')

    def append_order_into_orderbook(self):
        """
        Append order data into order book
        :return:
        """
        self.orderBook['bar_id'].append(self.order.bar_id)
        self.orderBook['order_dir'].append(self.order.order_dir)
        self.orderBook['open_dt'].append(self.order.open_dt)
        self.orderBook['open_price'].append(self.order.open_price)
        self.orderBook['close_dt'].append(self.order.close_dt)
        self.orderBook['close_price'].append(self.order.close_price)
        self.orderBook['status'].append(self.order.order_status)
        self.orderBook['profit'].append(self.__calculate_profit(self.order.open_price,
                                                                self.order.close_price,
                                                                self.order.order_dir))
        return

    def close_order(self, close_price, close_datetime, status: Literal['tp', 'sl', 'canceled', 'closed']):
        self.order.order_status = status
        self.order.close_price = close_price
        self.order.close_dt = close_datetime
        self.in_market = False
        profit = self.__calculate_profit(self.order.open_price,
                                         self.order.close_price,
                                         self.order.order_dir)
        self.__print_log(f'ORDER CLOSED with profit: {profit}')
        self.append_order_into_orderbook()
        return

    def win_lose_draw(self, profit: pd.Series):
        if profit > 0:
            return 'win'
        elif profit < 0:
            return 'lose'
        else: return 'canceled'

    def order_lifetime(self, open_time, close_time):
        "Return order lifetime in hours"
        diff = pd.to_datetime(close_time) - pd.to_datetime(open_time)
        return diff.total_seconds() / 3600

    def form_order_statistic(self):

        self.orderBookDf = pd.DataFrame(self.orderBook)
        self.orderBookDf['order_lifetime'] = self.orderBookDf.apply(
            lambda x: self.order_lifetime(x['open_dt'], x['close_dt']), axis=1
        )
        profit = self.orderBookDf['profit']
        self.orderBookDf['win/lose'] = profit.apply(self.win_lose_draw)
        win_lose_ratio = self.orderBookDf['win/lose'].value_counts(normalize=True).to_frame().T

        win_orders = self.orderBookDf[profit > 0]
        lose_orders = self.orderBookDf[profit < 0]

        trade_drawdown, max_drawdown = drawdown(profit)

        stat = pd.DataFrame({
            'Orders count:': self.orderBookDf[self.orderBookDf['win/lose'] != 'canceled'].shape[0],
            'Win %:': win_lose_ratio['win'].values[0] * 100,
            'Lose %:': win_lose_ratio['lose'].values[0] * 100,
            'Canceled %:': win_lose_ratio['canceled'].values[0] * 100,
            'Avg Profit (pips):': (win_orders['profit'].mean()) / self.points,
            'Avg Loss (pips):': (lose_orders['profit'].mean()) / self.points,
            'PnL order ratio:': win_lose_ratio['win'].values[0] / win_lose_ratio['lose'].values[0],
            'PnL profit ratio:': win_orders['profit'].mean() / abs(lose_orders['profit'].mean()),
            'Total (pips):': (profit.cumsum().values[-1]) / self.points,
            'Drawdown %:': max_drawdown.min(),
            'Sharp Ratio:': sharp_ratio(profit)
        }, index=['statistic'])
        return stat.T.to_markdown(tablefmt="grid")

    def show_order_statistic(self):
        profit = self.orderBookDf['profit']
        trade_drawdown, max_drawdown = drawdown(profit)
        returns = profit[self.orderBookDf['win/lose'] != 'canceled'].values

        fig, ax = plt.subplots(2, 2, figsize=(8, 6))
        ax[0, 0].set_title('Account gain')
        ax[0, 0].plot(self.orderBookDf.open_dt, profit.cumsum())
        ax[0, 0].set_xlabel('Date')
        ax[0, 0].set_ylabel('Account')
        ax[0, 0].xaxis.set_tick_params(rotation=45)
        
        ax[0, 1].set_title('Returns distribution')
        ax[0, 1].hist(returns, bins=30)
        ax[0, 1].vlines(0, 
                        ymin=0, 
                        ymax=ax[0, 1].get_ylim()[1],
                        colors='k', linestyles='dashed')
        ax[0, 1].set_xlabel('Returns')
        ax[0, 1].set_ylabel('Count')
        
        ax[1, 0].set_title('Drawdown')
        ax[1, 0].plot(self.orderBookDf.open_dt, trade_drawdown)
        ax[1, 0].plot(self.orderBookDf.open_dt, max_drawdown)
        ax[1, 0].set_xlabel('Date')
        ax[1, 0].set_ylabel('Drawdown')
        ax[1, 0].xaxis.set_tick_params(rotation=45)

        ax[1, 1].set_title('Order lifetime')
        ax[1, 1].scatter(self.orderBookDf['order_lifetime'], profit)
        ax[1, 1].set_xlabel('Order lifetime')
        ax[1, 1].set_ylabel('Profit')

        fig.suptitle("Overview", fontsize=16)
        plt.tight_layout()
        plt.show()
    
