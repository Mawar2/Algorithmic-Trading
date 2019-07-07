import pyalgotrade.strategy as strategy
import pyalgotrade.technical.ma as ma
from pyalgotrade.technical import rsi
import pyalgotrade.plotter as plotter
import pyalgotrade.barfeed.csvfeed as csvfeed
import pyalgotrade.bar as bar
import pyalgotrade.stratanalyzer.returns as ret
import pyalgotrade.stratanalyzer.sharpe as sharpe
import pyalgotrade.stratanalyzer.drawdown as drawdown
import pyalgotrade.stratanalyzer.trades as trades
import itertools
from pyalgotrade.optimizer import local

#we have $10k as initial budget
INITIAL_BUDGET = 10000
NSHARES = 10

#moving average model
class RSIMovingAverageStrategy(strategy.BacktestingStrategy):

	def __init__(self,feed,instrument,fastPeriod,slowPeriod,rsiPeriod,overboughtThreshold,oversoldThreshold):
		#this is where we have to define the initial budget
		super(RSIMovingAverageStrategy,self).__init__(feed,INITIAL_BUDGET)
		#we can track the position: long or short positions
		#if it is None we know we can open one
		self.longPosition = None
		self.shortPosition = None
		self.oversoldThreshold = oversoldThreshold
		self.overboughtThreshold = overboughtThreshold
		#the given stock (for example AAPL)
		self.instrument = instrument
		#if we want to use adjusted closing prices instead of regular closing prices
		self.setUseAdjustedValues(True)
		#fast moving average indicator (short-term trend) period is smaller
		self.fastMA = ma.EMA(feed[instrument].getPriceDataSeries(),fastPeriod)
		#slow moving average indicator (long-term trend) period is larger
		self.slowMA = ma.EMA(feed[instrument].getPriceDataSeries(),slowPeriod)
		#define the RSI model
		self.rsi = rsi.RSI(feed[instrument].getPriceDataSeries(),rsiPeriod)
		
	def getFastMA(self):
		return self.fastMA
		
	def getSlowMA(self):
		return self.slowMA
		
	def getRSI(self):
		return self.rsi
		
	#this is where the MA crossover strategy is implemented
	#this method is called when new bars are available
	def onBars(self,bars):
		
		if self.fastMA[-1] is None or self.slowMA[-1] is None or self.rsi[-1] is None:
			return
		
		#we exit the long position (if we've opened one in the past + there is an exit signal)
		if self.longPosition is not None:
				if self.exitLongSignal():
					self.longPosition.exitMarket()
					self.longPosition = None
		#we exit short position (if we've opened one in the past + there is an exit signal)
		elif self.shortPosition is not None:
				if self.exitShortSignal():
					self.shortPosition.exitMarket()
					self.shortPosition = None
		#maybe we have to open long or short positions so let's check the signals
		else:
		
			#enter long position if the signal suggests
			if self.enterLongSignal():
				self.longPosition = self.enterLong(self.instrument,NSHARES,True)
			#enter short position if the signals suggest to do so
			elif self.enterShortSignal():
				self.shortPosition = self.enterShort(self.instrument,NSHARES,True)
		
	def enterLongSignal(self):
		return self.fastMA[-1]>self.slowMA[-1] and self.rsi[-1]<self.oversoldThreshold
		
	def enterShortSignal(self):
		return self.fastMA[-1]<self.slowMA[-1] and self.rsi[-1]>self.overboughtThreshold

	def exitLongSignal(self):
		return self.fastMA[-1]<self.slowMA[-1]
		
	def exitShortSignal(self):
		return self.fastMA[-1]>self.slowMA[-1]
	
if __name__ == "__main__":
	
#===================================
#Test the moving average crossover strategy using BOTH
#long and short trades along with using the RSI indicator. 
#The optimize will test all possible combinations of the variables show
#below.
#	RSI strategy: 
#				a. Test different values for the RSI window (recall that the default
#				is usually RSI(14), but the example below tests the values 
#				RSI(2), RSI(3), RSI(5), RSI(7), RSI(10), RSI(14))
#				b. Oversold threshold values to be tested 10,20,30
#				c. Overbought threshold values to be tested 70,80,90
#				d. If fastperiod ma crosses above slowperiod ma and RSI less than oversold threshold, go long					
#				e.If fastperiod ma crosses below slowperiod ma and  RSI greater than overbought threshold, go short	
#               f. Exit wjen moving average crosses back (regardless of RSI value)
#Important Note: maximum value for fastperiod must remain less than the #minimum value for the slowperiod


	#we want to predict the S&P500 (^GSPC index)
	instrument = ['AAPL']

	fpath='C:/Users/Eric/Documents/PyBlockchainProj/'
	ftype='.csv'
	fname=fpath+instrument[0]+ftype

	#Important Note: maximum value for fastperiod must remain less than the 
	#minimum value for the slowperiod
	slowPeriod = (50,60,80,100,150,170,200)   
	fastPeriod = (5,10,20,30,40)
	rsiPeriod = (2,3,5,7,10,14)
	oversoldThreshold = (10,20,30)
	overboughtThreshold = (70,80,90)

#===========================================================================#

	#we can generate all the permutations
	all = itertools.product(instrument,fastPeriod,slowPeriod,rsiPeriod,
		overboughtThreshold,oversoldThreshold)
	
	#the data is in the CSV file (one row per day)
	feed = csvfeed.GenericBarFeed(bar.Frequency.DAY)
	feed.addBarsFromCSV(instrument[0],fname)
	
	#we can run the optimization parallel 
	local.run(RSIMovingAverageStrategy,feed,all)

