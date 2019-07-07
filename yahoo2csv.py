import random
import numpy as np
import pandas as pd
from pandas_datareader import data as pdr
import matplotlib.pyplot as plt
import fix_yahoo_finance as yf 
yf.pdr_override() 

fpath='C:/Users/Eric/Documents/'
ftype='.csv'
ticker = 'AAPL'
startdate = '2018-01-01'
enddate = '2019-01-31'

start = pd.to_datetime(startdate) 
end = pd.to_datetime(enddate)
sdata = pdr.get_data_yahoo(ticker, start=start, end=end)

columnsTitles=['Open','High','Low','Close','Volume','Adj Close']
sdata=sdata.reindex(columns=columnsTitles) 

z=np.datetime_as_string(sdata.index.values)
z=np.char.replace(z, 'T0', ' 0')
z=np.char.replace(z, '00.000000000', '00')
sdata=sdata.set_index(z)
sdata.index.names=['Date Time']

fname=fpath+ticker+ftype
sdata.to_csv(fname)

"""
#simple plot for double check of data
plt.title(ticker)
plt.plot(sdata['Close'])
plt.ylabel('Price')
plt.show()
"""



