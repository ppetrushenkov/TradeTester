import MetaTrader5 as mt5
from datetime import datetime


def get_data(pair: str,
             timeframe=mt5.TIMEFRAME_H1,
             from_date: str = '2015-01-01',
             to_date: str = datetime.today().isoformat(),
             date_as_index: bool = True):
    """
    Return data from MetaTrader5
    :param pair: Symbol name (EURUSD)
    :param timeframe: TimeFrame (mt5.TIMEFRAME_H1)
    :param from_date: start date (ISO FORMAT)
    :param to_date: last date (can be just datetime.today()) (ISO FORMAT)
    :param date_as_index: if True, sets column 'time' as index
    :return: price data as Pandas DataFrame
    """
    import MetaTrader5 as mt5
    
    if not mt5.initialize():
        print('[INFO] Initialize() failed')
        mt5.shutdown()

    from_date = datetime.fromisoformat(from_date)
    to_date = datetime.fromisoformat(to_date)
    data = mt5.copy_rates_range(pair, timeframe, from_date, to_date)
    mt5.shutdown()

    if data is not None:
        data = pd.DataFrame(data)
        data['time'] = pd.to_datetime(data['time'], unit='s')
        data.drop('real_volume', axis=1, inplace=True)
        data.rename(columns={'tick_volume': 'volume'}, inplace=True)
        if date_as_index:
            data.set_index(data['time'], inplace=True)
        return data

    else:
        raise ValueError("It seems MT5 doesn't have such data. Try to pass the closer date to today.")