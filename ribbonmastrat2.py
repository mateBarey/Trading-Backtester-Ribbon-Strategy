from binance.client import Client
import talib as ta
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from collections import defaultdict

class Trader:
    def __init__(self, file):
        self.connect(file)

    """ Creates Binance client """
    def connect(self,file):
        lines = [line.rstrip('\n') for line in open(file)]
        key = lines[0]
        secret = lines[1]
        self.client = Client(key, secret)

    """ Gets all account balances """
    def getBalances(self):
        prices = self.client.get_withdraw_history()
        return prices

class Strategy:

    def __init__(self, indicator_name, strategy_name, pair, interval, klines):
        #Name of indicator
        self.indicator = indicator_name
        #Name of strategy being used
        self.strategy = strategy_name
        #Trading pair
        self.pair = pair
        #Trading interval
        self.interval = interval
        #Kline data for the pair on given interval
        self.klines = klines
        #Calculates the indicator
        self.indicator_result = self.calculateIndicator()
        #Uses the indicator to run strategy
        self.strategy_result = self.calculateStrategy()


    '''
    Calculates the desired indicator given the init parameters
    '''
    def calculateIndicator(self):

        if self.indicator == 'RIBBON':
            close = [float(entry[4]) for entry in self.klines]
            close_array = np.asarray(close)
            #ema_8, ema_13, ema_21, ema_55 = ta.EMA(close_array, timeperiod=8, timeperiod=13, timeperiod=21,timeperiod=55)
            ema_8 = ta.EMA(close_array, timeperiod=8)
            ema_13 = ta.EMA(close_array, timeperiod=13)
            ema_21 = ta.EMA(close_array, timeperiod=21)
            ema_55 = ta.EMA(close_array, timeperiod=55)

            return [ema_8, ema_13, ema_21, ema_55]
        else:
            return None


    '''
    Runs the desired strategy given the indicator results
    '''
    #need to come back to this
    def calculateStrategy(self):
        if self.indicator == 'RIBBON':

            if self.strategy == 'CROSS':
                open_time = [int(entry[0]) for entry in self.klines]
                new_time = [datetime.fromtimestamp(time / 1000) for time in open_time]
                self.time = new_time
                crosses = []
                ema_above = False
                slopes = []
                #Runs through each timestamp in order
                for i,el in enumerate(self.indicator_result[0]):
                  if np.isnan(self.indicator_result[0][i]) or np.isnan(self.indicator_result[1][i]) or np.isnan(self.indicator_result[2][i]) or np.isnan(self.indicator_result[3][i]):
                    pass

                    #If both the MACD and signal are well defined, we compare the 2 and decide if a cross has occured
                  else:
                    ema_8_slope = (self.indicator_result[0][i] - self.indicator_result[0][i-1])/(4)
                    ema_13_slope = (self.indicator_result[1][i] - self.indicator_result[1][i-1])/(4)
                    ema_21_slope = (self.indicator_result[2][i] - self.indicator_result[3][i-1])/(4)
                    ema_avg_slope = (ema_8_slope + ema_13_slope + ema_21_slope)/3
                    if (self.indicator_result[0][i] > self.indicator_result[3][i] and self.indicator_result[1][i] > self.indicator_result[3][i] and self.indicator_result[2][i] > self.indicator_result[3][i]) :
                        if ema_above == False:
                            ema_above = True
                            # this is where I think you should calculate the momentum slope

                            #want to try to rank acceleration or change in momentum  to see when we could probably choose to not buy and see if it changes anything

                            slopes.append([new_time[i],ema_avg_slope,'go','buy'])


                            #Appends the timestamp, MACD value at the timestamp, color of dot, buy signal, and the buy price
                            cross = [new_time[i],self.indicator_result[0][i] , 'go', 'BUY', self.klines[i][4],ema_avg_slope]
                            crosses.append(cross)

                    else:
                        if ema_above == True :
                            ema_above = False
                            #Appends the timestamp, MACD value at the timestamp, color of dot, sell signal, and the sell price

                            slopes.append([new_time[i], ema_avg_slope,'ro','sell'])

                            cross = [new_time[i], self.indicator_result[0][i], 'ro', 'SELL', self.klines[i][4],ema_avg_slope]
                            crosses.append(cross)
                return crosses

            else:
                return None
        else:
            return None

    '''
    Getter for the strategy result
    '''
    def getStrategyResult(self):
        return self.strategy_result

    '''
    Getter for the klines
    '''
    def getKlines(self):
        return self.klines

    '''
    Getter for the trading pair
    '''
    def getPair(self):
        return self.pair

    '''
    Getter for the trading interval
    '''
    def getInterval(self):
        return self.interval

    '''
    Getter for the time list
    '''
    def getTime(self):
        return self.time

    '''
    Plots the desired indicator with strategy buy and sell points
    '''

    def plotIndicator(self):
        if self.indicator == 'RIBBON':
            open_time = [int(entry[0]) for entry in klines]
            new_time = [datetime.fromtimestamp(time / 1000) for time in open_time]
            plt.style.use('dark_background')
            plt.plot(new_time, self.indicator_result[0], label='ema_8')
            plt.plot(new_time, self.indicator_result[1], label='ema_13')
            plt.plot(new_time, self.indicator_result[2], label='ema_21')
            plt.plot(new_time, self.indicator_result[3], label='ema_55')
            for entry in self.strategy_result:
                plt.plot(entry[0], entry[1], entry[2])
            title = "RIBBON Plot for " + self.pair + " on " + self.interval
            plt.title(title)
            plt.xlabel("Open Time")
            plt.ylabel("Value")
            plt.legend()
            plt.show()

        else:
            pass

class Backtest:
    def __init__(self, starting_amount, start_datetime, end_datetime, strategy,):
        #Starting amount
        self.start = starting_amount
        #Number of trades
        self.num_trades = 0
        #Number of profitable trades
        self.profitable_trades = 0
        self.counter = 0
        #Running amount
        self.amount = self.start
        #Start of desired interval
        self.startTime = start_datetime
        #End of desired interval
        self.endTime = end_datetime
        #Strategy object
        self.strategy = strategy
        #Trading pair
        self.pair = self.strategy.getPair()
        #Trading interval
        self.interval = self.strategy.getInterval()
        #Outputs the trades exectued
        self.trades = []
        self.end_h = defaultdict()
        #Runs the backtest
        self.results = self.runBacktest()
        #Prints the results
        self.printResults()





    def runBacktest(self):
        amount = self.start
        klines = self.strategy.getKlines()
        time = self.strategy.getTime()
        point_finder = 0
        factor = (1-.1/100)
        strategy_result = self.strategy.getStrategyResult()
        #Finds the first cross point within the desired backtest interval
        while strategy_result[point_finder][0] < self.startTime:
            point_finder += 1
        #Initialize to not buy
        active_buy = False
        buy_price = 0
        #Runs through each kline
        for i in range(len(klines)):
            if point_finder > len(strategy_result)-1:
                break
            #If timestamp is in the interval, check if strategy has triggered a buy or sell
            if time[i] > self.startTime and time[i] < self.endTime:
                if(time[i] == strategy_result[point_finder][0]):
                    if strategy_result[point_finder][3] == 'BUY':
                        active_buy = True
                        buy_price = float(strategy_result[point_finder][4])
                        self.trades.append(['BUY', buy_price])
                    if strategy_result[point_finder][3] == 'SELL' and active_buy == True:
                        active_buy = False
                        bought_amount = amount / buy_price
                        self.num_trades += 1
                        if(float(strategy_result[point_finder][4]) > buy_price):
                            self.counter += 1
                            self.profitable_trades += 1
                            profit = bought_amount  * (float(strategy_result[point_finder][4])*factor-buy_price)
                            self.end_h[self.counter] = {}
                            self.end_h[self.counter]['profit'] = [str(profit), str(strategy_result[point_finder][5])]

                        else:
                            self.counter += 1
                            self.end_h[self.counter]={}
                            loss = bought_amount * (float(strategy_result[point_finder][4])*factor-buy_price)
                            self.end_h[self.counter]['loss'] = [str(loss), str(strategy_result[point_finder][5])]

                        amount = bought_amount * float(strategy_result[point_finder][4])*float(1-.1/100)  # for modification depreciat by exchange fees for more realistic scenario
                        self.trades.append(['SELL', float(strategy_result[point_finder][4])])
                    point_finder += 1
        self.amount = amount

    '''
    Prints the results of ribbon backtest
    '''
    def printResults(self):
        f = open('newfile1124.txt','w')
        print("Trading Pair: " + self.pair,file=f)
        print("Interval: " + self.interval,file=f)
        print("Ending amount: " + str(self.amount),file=f)
        print("Number of Trades: " + str(self.num_trades),file=f)
        profitable = self.profitable_trades / self.num_trades * 100
        print("Percentage of Profitable Trades: " + str(profitable) + "%",file=f)
        percent = self.amount / self.start * 100
        print(str(percent) + "% of starting amount",file=f)
        for entry in self.trades:
            print(entry[0] + " at " + str(entry[1]),file=f)
        for k,v in self.end_h.items():
          for k1,v1 in v.items():
            if k1 =='profit':
              print('profit  at  ' + (v1[0]) + ' slope ' + (v1[1]),file=f)
            else:
              print('loss  at  ' + (v1[0]) + ' slope ' + (v1[1]),file=f)
        f.close()


# add file name  and change  trading pair
filename = '/home/george/mlb.txt'
trader = Trader(filename)
trading_pair = 'ETHUSDT'
interval = '4h'
#klines = trader.client.get_klines(symbol=trading_pair,interval=interval)
klines = trader.client.get_historical_klines("ETHUSDT", trader.client.KLINE_INTERVAL_4HOUR, "1 Dec, 2017", "22 Jan, 2020")

ribbon_strategy = Strategy('RIBBON','CROSS',trading_pair,interval,klines)
#macd_strategy.plotIndicator()
time = ribbon_strategy.getTime()
ribbon_backtest = Backtest(10000, time[0], time[len(time)-1], ribbon_strategy)
