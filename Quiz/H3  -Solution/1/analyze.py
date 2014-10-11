import sys, os, datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import copy
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.DataAccess as da
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkstudy.EventProfiler as ep

class Analyzer(object):
    def __init__(self, value_file_path, benchmark):
        self.value_file_path = value_file_path
        self.benchmark = benchmark

    def analyze(self):
        self._parse_value_file()
        self._read_benchmark()
        self.portfolio_values = self.values
        self.values = zip(self.portfolio_values, self.bm_values)
        self._plot()

        values = np.array(self.portfolio_values, float)
        tsu.returnize0(values)

        bench_values = np.array(self.bm_values, float)
        tsu.returnize0(bench_values)

        return {"portfolio": {'stdev': values.std(),
                              'avg': values.mean(),
                              'sharp': np.sqrt(252) * values.mean() / values.std(),
                              'return': (self.portfolio_values[-1] / self.portfolio_values[0])},
                self.benchmark: {'stdev': bench_values.std(),
                                 'avg': bench_values.mean(),
                                 'sharp': np.sqrt(252) * bench_values.mean() / bench_values.std(),
                                 'return': (self.bm_values[-1] / self.bm_values[0])}}

    def _read_benchmark(self):
        bm = self.benchmark
        db = da.DataAccess("Yahoo")
        times = du.getNYSEdays(self.dates[0], self.dates[-1] + datetime.timedelta(days=1), datetime.timedelta(hours=16))
        bm_price = db.get_data(times, [bm], ['close'])[0][self.benchmark]
        volume = self.values[0] / bm_price.values[0]

        self.bm_values = []
        for date in self.dates:
            date += datetime.timedelta(hours=16)
            self.bm_values.append(bm_price[date] * volume)

    def _parse_value_file(self):
        self.dates = []
        self.values = []
        with open(self.value_file_path) as value_file:
            records = value_file.read().split()
            for record in records:
                year, month, day, value = record.split(',')
                date = datetime.datetime(int(year), int(month), int(day))
                self.dates.append(date)
                self.values.append(float(value))

    def _plot(self):
        plt.clf()
        fig, ax = plt.subplots(1)
        ax.plot(self.dates, self.values)
        fig.autofmt_xdate()
        plt.xticks(size='xx-small')
        plt.yticks(size='xx-small')
        plt.legend(['Portfolio', self.benchmark])
        plt.ylabel("Daily Value")
        plt.xlabel("Date")
        plt.savefig("plotfolio.pdf", format='pdf')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Sample usage: python2.7 analyze.py values.csv $SPX"
        print "%d arguments provided" % len(sys.argv)
        #sys.exit(0)

    value_file_path = 'values.csv'
    benchmark = '$SPX'
    #value_file_path = sys.argv[1]
    #benchmark = sys.argv[2]

    analyzer = Analyzer(value_file_path, benchmark)
    detail = analyzer.analyze()

    # Output the detail of portfolio
    print "The final value of the portfolio using the sample file is -- %s, %.1f\n" % (analyzer.dates[-1], analyzer.portfolio_values[-1])
    print "\nDetails of the Performance of the portfolio\n"
    print "\nData Range :  %s  to  %s\n" % (analyzer.dates[0], analyzer.dates[-1])
    print "Portfolio performance:\n"
    print detail['portfolio']
    print "\n%s performance:\n" % analyzer.benchmark
    print detail[analyzer.benchmark]
    
