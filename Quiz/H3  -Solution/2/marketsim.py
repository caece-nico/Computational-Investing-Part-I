import sys, os, datetime
import pandas as pd
import numpy as np
import math
import copy
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.DataAccess as da
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkstudy.EventProfiler as ep

class Trade(object):
    def __init__(self, date, symbol, trade_type, volume):
        self.date = date
        self.symbol = symbol
        self.trade_type = trade_type
        self.volume = volume

    def __str__(self):
        return "%s %s %d" % (self.symbol, self.trade_type, self.volume)
    
    def __repr__(self):
        return str(self)

class Simulator(object):
    def __init__(self, cash, order_file, out_file):
        self.cash = cash
        self._parse_order_file(order_file)
        self._read_relative_history()
        self.out_file_path = out_file

    def _read_relative_history(self):
        self.history_times = du.getNYSEdays(self.begin_date, self.end_date, datetime.timedelta(hours = 16))
        db = da.DataAccess("Yahoo")
        self.history_data_frame = db.get_data(self.history_times, self.symbols, ['close'])[0]
        

    def _parse_order_file(self, order_file_path):
        self.begin_date = datetime.datetime(3980, 1, 1)
        self.end_date = datetime.datetime(1920, 1, 1)
        self.order_dict = {}
        self.symbols = set()
        with open(order_file_path) as order_file:
            raw = order_file.read().split()
            for line in raw:
                fields = line.split(',')
                if len(fields) < 6:
                    print "ignore order line:(%s)" % line
                    continue
                year = int(fields[0])
                month = int(fields[1])
                day = int(fields[2])
                symbol = fields[3]
                trade_type = fields[4]
                volume = int(fields[5])
                date = datetime.datetime(year, month, day, 16)

                if date < self.begin_date:
                    self.begin_date = date
                if date > self.end_date:
                    self.end_date = date

                self.symbols.add(symbol)

                trade = Trade(date, symbol, trade_type, volume)
                
                trade_list = self.order_dict.setdefault(date, [])
                trade_list.append(trade)

    def simulate(self):
        print "first date:%s\nlast date:%s\nscheduled trades:\n" % (self.begin_date, self.end_date)
        for date in sorted(self.order_dict):
            print "%s: %s" % (date, self.order_dict[date])
        print "symbols:"
        print self.symbols
        print self.history_data_frame

        out_file = open(self.out_file_path, 'w')
        cur_date = self.begin_date
        self.stocks = dict()
        while cur_date <= self.end_date:
            try:
                cur_value = self.cash + self._get_stock_value(cur_date)
                out_file.write("%d,%d,%d,%.3f\n" % (cur_date.year, cur_date.month, cur_date.day, cur_value))
                self._make_trade(cur_date)
            except Exception, err:
                pass
            cur_date += datetime.timedelta(days=1)
        out_file.close()
            
    def _make_trade(self, date):
        trades = self.order_dict.get(date, [])
        for trade in trades:
            price = self.history_data_frame[trade.symbol].ix[date]
            if trade.symbol not in self.stocks:
                self.stocks[trade.symbol] = 0

            if trade.trade_type.upper() == "BUY":
                self.cash -= trade.volume * price
                self.stocks[trade.symbol] += trade.volume
            elif trade.trade_type.upper() == "SELL":
                self.cash += trade.volume * price
                self.stocks[trade.symbol] -= trade.volume
            else:
                raise Exception("bad trade:%s" % str(trade))

    def _get_stock_value(self, cur_date):
        val = 0.0
        for symbol, volume in self.stocks.items():
            if cur_date not in self.history_data_frame[symbol]:
                raise Exception("Non trading day")
            val += float(volume) * self.history_data_frame[symbol].ix[cur_date]
        return val
                

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "Sample usage: python marketsim.py 1000000 orders.csv values.csv"
        #sys.exit(0)


    #cash = float(sys.argv[1])
    #order_file = sys.argv[2]
    #out_file = sys.argv[3]
    cash = float(1000000)
    order_file = 'orders2.csv'
    out_file = 'values.csv'
    print "simulating using cash:%.2f, order file:%s, output: %s" % (cash, order_file, out_file)
    simu = Simulator(cash, order_file, out_file)
    simu.simulate()

