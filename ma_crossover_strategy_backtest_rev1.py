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

#we have $10k as initial budget
INITIAL_BUDGET = 10000
NSHARES = 10

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
	instrument = 'AAPL'
	fpath='C:/Users/Eric Sakk/Documents/PythonProjVScode/'
	ftype='.csv'
	fname=fpath+instrument+ftype

	#first MA indicator tracks the slow trend with period 50
	slowPeriod = 100
	#second MA indicator tracks the fast trend with period 30
	fastPeriod = 50
	
	#the data is in the CSV file (one row per day)
	feed = csvfeed.GenericBarFeed(bar.Frequency.DAY)
	feed.addBarsFromCSV(instrument,fname)
	
	#this is where we define the time for the moving average models (slow and fast)
	movingAverageStrategy = MovingAverageStrategy(feed,instrument,fastPeriod,slowPeriod)
	
	#we can define the cost of trading (cost pre trade)
	movingAverageStrategy.getBroker().setCommission(backtesting.FixedPerTrade(cost_per_trade))
	
	#we want to plot the stock (instrument) with the buy/sell orders
	plot = plotter.StrategyPlotter(movingAverageStrategy,plotAllInstruments=True,plotBuySell=True,plotPortfolio=True)
	plot.getInstrumentSubplot('S&P500').addDataSeries('Fast SMA',movingAverageStrategy.getFastMA())
	plot.getInstrumentSubplot('S&P500').addDataSeries('Slow SMA',movingAverageStrategy.getSlowMA())
	
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
	#we have to define the risk free rate (0.0 in this case)
	print('Annualized Sharpe ratio: %.2f' % sharpeRatioAnalyzer.getSharpeRatio(0.0))
	print('Number of trades: %d' % tradesAnalyzer.getCount())
	
	tradesProfits = tradesAnalyzer.getAll()
	
	print('Total average of profit and loss: $%.2f' % tradesProfits.mean())
	print('Maximum profit (trade) $%.2f' % tradesProfits.max())
	print('Maximum loss (trade) $%.2f' % tradesProfits.min())
	
	print('Annual return: %0.2f %%' % (returnAnalyzer.getCumulativeReturns()[-1]*100))
	print('Strategy final equity: $%.2f' % movingAverageStrategy.getBroker().getEquity())
	
	plot.plot()