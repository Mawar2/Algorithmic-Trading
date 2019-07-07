import pyalgotrade.strategy as strategy
import pyalgotrade.technical.ma as ma
import pyalgotrade.plotter as plotter
import pyalgotrade.barfeed.csvfeed as csvfeed
import pyalgotrade.bar as bar
import pyalgotrade.stratanalyzer.returns as ret
import pyalgotrade.stratanalyzer.sharpe as sharpe
import pyalgotrade.stratanalyzer.drawdown as drawdown
import pyalgotrade.stratanalyzer.trades as trades
from pyalgotrade.broker import backtesting

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import numpy as np

#moving average model
class MovingAverageStrategy(strategy.BacktestingStrategy):

	def __init__(self,feed,instrument,nfast,nslow):
		#this is where we have to define the initial budget
		super(MovingAverageStrategy,self).__init__(feed,INITIAL_BUDGET)
		#we can track the position: long or short positions
		#if it is None we know we can open one
		self.position = None
		#the given stock (for example AAPL)
		self.instrument = instrument
		#if we want to use adjusted closing prices instead of regular closing prices
		self.setUseAdjustedValues(True)
		#fast moving average indicator (short-term trend) period is smaller
		self.fastMA = ma.SMA(feed[instrument].getPriceDataSeries(),nfast)
		#slow moving average indicator (long-term trend) period is larger
		self.slowMA = ma.SMA(feed[instrument].getPriceDataSeries(),nslow)
		
	def getFastMA(self):
		return self.fastMA
		
	def getSlowMA(self):
		return self.slowMA
		
	#this is where the MA crossover strategy is implemented
	#this method is called when new bars are available
	#when fast > slow MA -> open a long position 
	#when fast < slow MA -> close the long position
	def onBars(self,bars):
		
		#MA with preiod p needs p previous values ... if not available then return (for the first p-1 bars the value is NULL)
		if self.slowMA[-1] is None:
			return
		
		#if we have not opened a long position so far then we open one
		if self.position is None:
			if self.fastMA[-1] > self.slowMA[-1]:
				self.position = self.enterLong(self.instrument,NSHARES,True)
		elif self.fastMA[-1] < self.slowMA[-1]:
			self.position.exitMarket()
			self.position = None
	
	#when we open a long position this function is called
	def onEnterOk(self,position):
		trade_info = position.getEntryOrder().getExecutionInfo()
		self.info("Buy stock at $%.2f and actual equity: $%.2f"%(trade_info.getPrice(),self.getBroker().getEquity()))
		
	#when we close the long position this function is called	
	def onExitOk(self,position):
		trade_info = position.getExitOrder().getExecutionInfo()
		self.info("Sell stock at $%.2f"%(trade_info.getPrice()))
	
if __name__ == "__main__":

	cost_per_trade = 4.95
	instrument = 'SPY'
	fpath='C:/Users/Eric/Documents/PyBlockchainProj/'
	ftype='.csv'
	fname=fpath+instrument+ftype

	#set up slowperiod and fastperiod values 
	fastminval = 3
	fastmaxval = 50
	fastvec = list(range(fastminval, fastmaxval+1))
	slowmult = [1.5,2,2.5,3,3.5,4]
	slowlist = []
	fastlist = []
	for fastPeriod in fastvec:
		tmp_slow = []
		tmp_fast = []
		for multval in slowmult:
			tmp_slow.append(int(multval*fastPeriod))			
			tmp_fast.append(fastPeriod)
		slowlist.append(tmp_slow)		
		fastlist.append(tmp_fast)

	#backtest each fastperiod/slowperiod pair 
	net_profit_list = []
	for i in range(len(fastvec)):
		fastPeriod = fastvec[i]
		tmp_profit_list = []
		for slowPeriod in slowlist[i]:

			print([fastPeriod,slowPeriod])

			#we have $10k as initial budget
			INITIAL_BUDGET = 10000
			NSHARES = 10

			#the data is in the CSV file (one row per day)
			feed = csvfeed.GenericBarFeed(bar.Frequency.DAY)
			feed.addBarsFromCSV(instrument,fname)

			#this is where we define the time for the moving average models (slow and fast)
			movingAverageStrategy = MovingAverageStrategy(feed,instrument,fastPeriod,slowPeriod)
	
			#we can define the cost of trading (cost pre trade)
			movingAverageStrategy.getBroker().setCommission(backtesting.FixedPerTrade(cost_per_trade))

			#we can analyze the returns during the backtest
			returnAnalyzer = ret.Returns()
			movingAverageStrategy.attachAnalyzer(returnAnalyzer)
	
			#we can analyze the Sharpe ratio during backtest
			sharpeRatioAnalyzer = sharpe.SharpeRatio()
			movingAverageStrategy.attachAnalyzer(sharpeRatioAnalyzer)
	
			#we can analyze the trades (maximum profit or loss etc.)
			tradesAnalyzer = trades.Trades()
			movingAverageStrategy.attachAnalyzer(tradesAnalyzer)
	
			#let's run the strategy on the data (CSV file) so let's backtest the algorithm
			movingAverageStrategy.run()
	
			print('Initial equity: $',INITIAL_BUDGET)
			print('Portfolio net trading profit and loss: $%.2f' % tradesAnalyzer.getAll().sum())
			tmp_profit_list.append(tradesAnalyzer.getAll().sum())

			del movingAverageStrategy

		net_profit_list.append(tmp_profit_list)

	#Surface plot of profitability ...
	fast_length=len(fastvec)
	slow_length=len(slowmult)
	X = np.zeros((fast_length,slow_length))
	Y = np.zeros((fast_length,slow_length))	
	Z = np.zeros((fast_length,slow_length))
	for i in range(fast_length):
		for j in range(slow_length):
			X[i,j] = fastlist[i][j]
			Y[i,j] = slowlist[i][j]
			Z[i,j] = net_profit_list[i][j]
	
	print()
	maxptr = np.unravel_index(np.argmax(Z, axis=None), Z.shape)
	print('Fast MA with max profit = ', int(X[maxptr]))
	print('Slow MA with max profit = ', int(Y[maxptr]))
	print('Max profit = ', Z[maxptr])

	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d')
	surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm)
	fig.colorbar(surf, shrink=0.5, aspect=5)
	plt.title(instrument)
	ax.set_xlabel('Fast')
	ax.set_ylabel('Slow')
	ax.set_zlabel('Profit $')
	plt.show()


