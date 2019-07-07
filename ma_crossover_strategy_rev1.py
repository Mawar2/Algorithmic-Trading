import pyalgotrade.strategy as strategy
import pyalgotrade.technical.ma as ma
import pyalgotrade.plotter as plotter
import pyalgotrade.barfeed.csvfeed as csvfeed
import pyalgotrade.bar as bar

#moving average model
class MovingAverageStrategy(strategy.BacktestingStrategy):

	def __init__(self,feed,instrument,nfast,nslow):
		super(MovingAverageStrategy,self).__init__(feed)
		#we can track the position: long or short positions
		#if it is None we know we can open one
		self.position = None
		#the given stock (for example AAPL)
		self.instrument = instrument
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
		
		#MA with period p needs p previous values ... if not available then return (for the first p-1 bars the value is NULL)
		if self.slowMA[-1] is None:
			return
		
		#if we have not opened a long position so far then we open one
		if self.position is None:
			#when fastMA crosses the slowMA and fastMA>slowMA then open a long position
			if self.fastMA[-1] > self.slowMA[-1]:
				self.position = self.enterLong(self.instrument,1,True)
		elif self.fastMA[-1] < self.slowMA[-1]:
			#exit the long position
			self.position.exitMarket()
			self.position = None
	
	#when we open a long position this function is called
	def onEnterOk(self,position):
		trade_info = position.getEntryOrder().getExecutionInfo()
		self.info("Buy stock at $%.2f"%(trade_info.getPrice()))
		
	#when we close the long position this function is called
	def onExitOk(self,position):
		trade_info = position.getExitOrder().getExecutionInfo()
		self.info("Sell stock at $%.2f"%(trade_info.getPrice()))
	
if __name__ == "__main__":

	instrument = 'AAPL'
	fpath='C:/Users/Eric Sakk/Documents/PythonProjVScode/'
	ftype='.csv'
	fname=fpath+instrument+ftype	

	#first MA indicator tracks the slow trend with period 100
	slowPeriod = 50
	#second MA indicator tracks the fast trend with period 50
	fastPeriod = 30
	
	#the data is in the CSV file (one row per day)
	feed = csvfeed.GenericBarFeed(bar.Frequency.DAY)
	feed.addBarsFromCSV(instrument,fname)
	
	#this is where we define the time for the moving average models (slow and fast)
	movingAverageStrategy = MovingAverageStrategy(feed,instrument,fastPeriod,slowPeriod)
	
	#we want to plot the stock (instrument) with the buy/sell orders
	plot = plotter.StrategyPlotter(movingAverageStrategy,plotAllInstruments=True,plotBuySell=True,plotPortfolio=False)
	plot.getInstrumentSubplot(instrument).addDataSeries('Fast SMA',movingAverageStrategy.getFastMA())
	plot.getInstrumentSubplot(instrument).addDataSeries('Slow SMA',movingAverageStrategy.getSlowMA())
	
	#let's run the strategy on the data (CSV file)
	movingAverageStrategy.run()
	plot.plot()