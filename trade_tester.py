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
    close_bar_id: int
    open_price: float
    close_price: float
    tp: float
    sl: float


class TradeTester:
    def __init__(
            self,
            points: float = 0.00001,
            show_log: bool = False):
        
        # Data
        self.dt = None
        self.op = None
        self.hi = None
        self.lo = None        
        self.cl = None

        self.trend = None
        self.entries = None
        self.filters = None

        # Stop Loss and Take Profit Parameters
        self.sl_method = None
        self.sl_value = None
        self.tp_method = None
        self.tp_value = None
        self.sl_mult = 2
        self.tp_mult = 5

        # Entry parameters
        self.entry_method = None
        self.entry_value = None
        self.entry_mult = None

        # Parameters
        self.indent = 5 * points
        self.points = points
        self.show_log = show_log

        # Order Parameters
        self.in_market = False
        self.order = None
        self.orderBook = {
            'bar_id': [],
            'order_dir': [],
            'open_dt': [],
            'open_price': [],
            'close_dt': [],
            'close_bar_id': [],
            'close_price': [],
            'status': [],
            'profit': []
        }
        self.orderBookDf = None
        self.returns = None

    
    def add_data(self,
                 datetime_data: np.ndarray | pd.Series,
                 open_data: np.ndarray | pd.Series,
                 high_data: np.ndarray | pd.Series,
                 low_data: np.ndarray | pd.Series,
                 close_data: np.ndarray | pd.Series,
                 volume_data: np.ndarray | pd.Series = None):
        """
        
        """
        if isinstance(datetime_data, np.ndarray):
            self.dt = datetime_data
            self.op = open_data
            self.hi = high_data
            self.lo = low_data
            self.cl = close_data
            self.vo = volume_data if volume_data else None
        else:
            self.dt = datetime_data.values
            self.op = open_data.values
            self.hi = high_data.values
            self.lo = low_data.values
            self.cl = close_data.values
            self.vo = volume_data.values if volume_data else None
    
    def add_trend(self, trend):
        if isinstance(trend, np.ndarray):
            self.trend = trend
        else:
            self.trend = trend.values

    def add_entries(self, entries):
        if isinstance(entries, np.ndarray):
            self.entries = entries
        else:
            self.entries = entries.values

    def add_filters(self, filters):
        if isinstance(filters, np.ndarray):
            self.filters = filters
        else:
            self.filters = filters.values

    def set_entry_method(self, 
                         kind: Literal['close', 'channel', 'atr', 'bar_extremum'], 
                         value: int | float,
                         mult: int,
                         order_type: Literal['limit', 'stop'] = 'stop'):
        self.entry_method = kind
        self.entry_value = value
        self.order_type = order_type
        if kind == 'atr':
            self.entry_mult = mult

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
                return self.lo[idx] - self.indent
            else:
                return self.hi[idx] + self.indent
            
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
            dti = self.dt[idx]
            opi = self.op[idx]
            hii = self.hi[idx]
            loi = self.lo[idx]
            cli = self.cl[idx]

            # If uptrend and BUY condition
            if not self.in_market:
                if self.trend[idx] == 1 and self.entries[idx] == 1:
                    sl = self.__get_sl(idx, 1)
                    tp = self.__get_tp(idx, 1)
                    self.order = Order(order_status='stop',
                                    order_dir='buy',
                                    open_dt=dti,
                                    open_price=hii + self.indent,
                                    bar_id=idx,
                                    close_bar_id=None,
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
                                    open_dt=dti,
                                    open_price=loi - self.indent,
                                    bar_id=idx,
                                    close_bar_id=None,
                                    close_price=None,
                                    close_dt=None,
                                    sl=sl,
                                    tp=tp)
                    self.in_market = True
                    self.__print_log(f'SELL ORDER PENDED at {self.order.open_price}', idx)

            # If order was set
            elif self.in_market:
                for i in range(n):
                    dtn = self.dt[idx + i]  # dtn - dt next
                    opn = self.op[idx + i]
                    hin = self.hi[idx + i]
                    lon = self.lo[idx + i]
                    cln = self.cl[idx + i]

                    # Work with pended orders
                    if self.order.order_status == 'stop':
                        if self.order.order_dir == 'buy':
                            if hin > self.order.open_price:
                                self.order.order_status = 'in market'
                                self.__print_log(f'ORDER IN MARKET at {self.order.open_price}', idx)
                                
                        elif self.order.order_dir == 'sell':
                            if lon < self.order.open_price:
                                self.order.order_status = 'in market'
                                self.__print_log(f'ORDER IN MARKET at {self.order.open_price}', idx)

                    # Work with market orders
                    elif self.order.order_status == 'in market':
                        # if BUY order
                        if self.order.order_dir == 'buy':
                            if lon <= self.order.sl:
                                self.__close_order(self.order.sl, idx+i, 'sl')
                                break
                            elif hin >= self.order.tp:
                                self.__close_order(self.order.tp, idx+i, 'tp')
                                break
                        # if SELL order
                        elif self.order.order_dir == 'sell':
                            if hin >= self.order.sl:
                                self.__close_order(self.order.sl, idx+i, 'sl')
                                break
                            elif lon <= self.order.tp:
                                self.__close_order(self.order.tp, idx+i, 'tp')
                                break

                # If order still in work
                if self.order.order_status == 'stop':
                    self.__close_order(self.order.open_price, idx+i, 'canceled')
                    continue
                elif self.order.order_status == 'in market':
                    self.__close_order(cln, idx+i, 'closed')
                    continue

        self.__form_order_book()

    def __append_order_into_orderbook(self):
        """
        Append order data into order book
        :return:
        """
        self.orderBook['bar_id'].append(self.order.bar_id)
        self.orderBook['order_dir'].append(self.order.order_dir)
        self.orderBook['open_dt'].append(self.order.open_dt)
        self.orderBook['open_price'].append(self.order.open_price)
        self.orderBook['close_dt'].append(self.order.close_dt)
        self.orderBook['close_bar_id'].append(self.order.close_bar_id)
        self.orderBook['close_price'].append(self.order.close_price)
        self.orderBook['status'].append(self.order.order_status)
        self.orderBook['profit'].append(self.__calculate_profit(self.order.open_price,
                                                                self.order.close_price,
                                                                self.order.order_dir))
        return

    def __close_order(self, close_price, idx, status: Literal['tp', 'sl', 'canceled', 'closed']):
        self.order.order_status = status
        self.order.close_price = close_price
        # self.order.close_dt = close_datetime
        self.order.close_dt = self.dt[idx]
        self.order.close_bar_id = idx
        profit = self.__calculate_profit(self.order.open_price,
                                         self.order.close_price,
                                         self.order.order_dir)
        self.__print_log(f'ORDER CLOSED with profit: {profit}')
        self.__append_order_into_orderbook()
        self.in_market = False
        return

    def __win_lose_draw(self, profit: pd.Series):
        if profit > 0:
            return 'win'
        elif profit < 0:
            return 'lose'
        else: return 'canceled'

    def __order_lifetime(self, open_time, close_time):
        "Return order lifetime in hours"
        diff = pd.to_datetime(close_time) - pd.to_datetime(open_time)
        return diff.total_seconds() / 3600
    
    def __form_order_book(self):
        self.orderBookDf = pd.DataFrame(self.orderBook)
        self.orderBookDf['bars_in_deal'] = self.orderBookDf['close_bar_id'] - self.orderBookDf['bar_id']
        self.orderBookDf['win/lose'] = self.orderBookDf['profit'].apply(self.__win_lose_draw)
        self.returns = pd.Series(data=self.orderBookDf[self.orderBookDf['win/lose'] != 'canceled']['profit'].values, 
                                 index=self.orderBookDf[self.orderBookDf['win/lose'] != 'canceled']['open_dt'].values)
        return 
    
    def form_order_statistic(self):
        profit = self.orderBookDf['profit']
        win_lose_ratio = self.orderBookDf[self.orderBookDf['win/lose'] != 'canceled']['win/lose'].value_counts(normalize=True).to_frame().T
        win_lose_draw_ratio = self.orderBookDf['win/lose'].value_counts(normalize=True).to_frame().T

        win_orders = self.orderBookDf[profit > 0]
        lose_orders = self.orderBookDf[profit < 0]

        trade_drawdown, max_drawdown = drawdown(profit)

        order_count = self.orderBookDf[self.orderBookDf['win/lose'] != 'canceled'].shape[0]
        canceled = self.orderBookDf[self.orderBookDf['win/lose'] == 'canceled'].shape[0]

        stat = pd.DataFrame({
            'Orders count:': order_count,
            'Canceled:': canceled,
            'Canceled %:': canceled * 100 / order_count,
            'Win %:': win_lose_ratio['win'].values[0] * 100,
            'Lose %:': win_lose_ratio['lose'].values[0] * 100,
            'Avg Profit (pips):': (win_orders['profit'].mean()) / self.points,
            'Avg Loss (pips):': (lose_orders['profit'].mean()) / self.points,
            'PnL order ratio:': win_lose_ratio['win'].values[0] / (win_lose_ratio['lose'].values[0] + win_lose_ratio['win'].values[0]),
            'PnL profit ratio:': win_orders['profit'].mean() / abs(lose_orders['profit'].mean()),
            'Total (pips):': (profit.cumsum().values[-1]) / self.points,
            'Drawdown %:': max_drawdown.min(),
            'Sharp Ratio:': sharp_ratio(profit)
        }, index=['statistic'])
        # return stat.T.to_markdown(tablefmt="grid")
        return stat

    def show_orders_statistic(self):
        profit = self.orderBookDf['profit']
        trade_drawdown, max_drawdown = drawdown(profit)

        fig, ax = plt.subplots(2, 2, figsize=(10, 8))
        ax[0, 0].set_title('Account gain')
        ax[0, 0].plot(self.orderBookDf.open_dt, profit.cumsum())
        ax[0, 0].set_xlabel('Date')
        ax[0, 0].set_ylabel('Account')
        ax[0, 0].xaxis.set_tick_params(rotation=45)
        
        ax[0, 1].set_title('Returns distribution')
        ax[0, 1].hist(self.returns, bins=30)
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
        ax[1, 1].scatter(self.orderBookDf['bars_in_deal'], profit)
        ax[1, 1].set_xlabel('Bars')
        ax[1, 1].set_ylabel('Profit')

        fig.suptitle("Overview", fontsize=16)
        plt.tight_layout()
        # plt.show()
        return fig
    
