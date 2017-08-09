from bs4 import BeautifulSoup
import pandas as pd
from urllib.request import urlopen
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, WeekdayLocator,DayLocator, MONDAY
from matplotlib.finance import candlestick_ohlc
from matplotlib.dates import date2num

# define stocks to compare. Each stock contains its name and stock page in Yahoo Finance historical data
stocks = [['SNAP', 'https://finance.yahoo.com/quote/SNAP/history?p=SNAP'],
          ['TWITTER', 'https://finance.yahoo.com/quote/TWTR/history?p=TWTR'],
          ['FB', 'https://finance.yahoo.com/quote/FB/history?p=FB']]

def scrape_data_yahoo(url):
    '''
    scrape data from Yahoo finance
    '''
    data = []
    try:
        conn = urlopen(url)
        soup = BeautifulSoup(conn, "html.parser")
        locate_tag = soup.find("div", {"id": "Main"})
        table_tag = locate_tag.find_next("table", {"data-test": "historical-prices"})
        tbody_tag = table_tag.find_next("tbody")
        # scrape the data
        for row in tbody_tag.find_all('tr'):
            col = row.find_all('td')
            # the first is date, the other are numbers
            data.append([col[0].find_next('span').text]+
                        [float(td.find_next('span').text.replace(',','')) for td in col[1:]])
        return to_pandas_data_frame(np.array(data))
    finally:
        # properly release the resources
        try:
            if soup:
                soup.decompose()
            if conn:
                conn.close()
        except NameError:
            pass

def to_pandas_data_frame(data):
    '''
    Transform to pandas dataframe for analysis
    '''
    df = pd.DataFrame(data=data[0:,1:], # values
            index=data[0:,0], # date as index
            columns=['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']) # column names
    # to numeric
    df = df.apply(pd.to_numeric, errors='ignore')
    df.index.name = 'Date'
    # index field to date
    df.index = pd.to_datetime(df.index, format='%b %d, %Y')
    return df

def scrape_all():
    '''
    scrape all data in stocks
    '''
    data_all = []
    for s in stocks:
        data_all.append(scrape_data_yahoo(s[1]))
    return data_all

def pandas_candlestick_ohlc(dat, stick = "day", otherseries = None):
    mondays = WeekdayLocator(MONDAY)        # major ticks on the mondays
    alldays = DayLocator()              # minor ticks on the days
    dayFormatter = DateFormatter('%d')

    # Create a new DataFrame which includes OHLC data for each period specified by stick input
    transdat = dat.loc[:,["Open", "High", "Low", "Close"]]
    if (type(stick) == str):
        if stick == "day":
            plotdat = transdat
            stick = 1 # Used for plotting
        elif stick in ["week", "month", "year"]:
            if stick == "week":
                transdat["week"] = pd.to_datetime(transdat.index).map(lambda x: x.isocalendar()[1]) # Identify weeks
            elif stick == "month":
                transdat["month"] = pd.to_datetime(transdat.index).map(lambda x: x.month) # Identify months
            transdat["year"] = pd.to_datetime(transdat.index).map(lambda x: x.isocalendar()[0]) # Identify years
            grouped = transdat.groupby(list(set(["year",stick])))
            plotdat = pd.DataFrame({"Open": [], "High": [], "Low": [], "Close": []})
            for name, group in grouped:
                plotdat = plotdat.append(pd.DataFrame({"Open": group.iloc[0,0],
                                            "High": max(group.High),
                                            "Low": min(group.Low),
                                            "Close": group.iloc[-1,3]},
                                           index = [group.index[0]]))
            if stick == "week": stick = 5
            elif stick == "month": stick = 30
            elif stick == "year": stick = 365

    elif (type(stick) == int and stick >= 1):
        transdat["stick"] = [np.floor(i / stick) for i in range(len(transdat.index))]
        grouped = transdat.groupby("stick")
        plotdat = pd.DataFrame({"Open": [], "High": [], "Low": [], "Close": []}) # Create empty data frame containing what will be plotted
        for name, group in grouped:
            plotdat = plotdat.append(pd.DataFrame({"Open": group.iloc[0,0],
                                        "High": max(group.High),
                                        "Low": min(group.Low),
                                        "Close": group.iloc[-1,3]},
                                       index = [group.index[0]]))

    else:
        raise ValueError('Valid inputs to argument "stick" include the strings "day", "week", "month", "year", or a positive integer')


    # Set plot parameters, including the axis object ax used for plotting
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.2)
    if plotdat.index[-1] - plotdat.index[0] < pd.Timedelta('730 days'):
        weekFormatter = DateFormatter('%b %d')
        ax.xaxis.set_major_locator(mondays)
        ax.xaxis.set_minor_locator(alldays)
    else:
        weekFormatter = DateFormatter('%b %d, %Y')
    ax.xaxis.set_major_formatter(weekFormatter)

    ax.grid(True)

    # Create the candelstick chart
    candlestick_ohlc(ax, list(zip(list(date2num(plotdat.index.tolist())), plotdat["Open"].tolist(), plotdat["High"].tolist(),
                      plotdat["Low"].tolist(), plotdat["Close"].tolist())),
                      colorup = "black", colordown = "red", width = stick * .4)

    # Plot other series (such as moving averages) as lines
    if otherseries != None:
        if type(otherseries) != list:
            otherseries = [otherseries]
        dat.loc[:,otherseries].plot(ax = ax, lw = 1.3, grid = True)

    ax.xaxis_date()
    ax.autoscale_view()
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')

def compare_plot(data_all, compare_field="Adj Close"):
    '''
    compare the stocks in a plot
    '''
    dic = dict()
    secondary_y = []
    for idx, data in enumerate(data_all):
        dic[stocks[idx][0]] = data[compare_field]
        secondary_y.append(stocks[idx][0])
    df = pd.DataFrame(dic)
    df.plot(secondary_y = secondary_y, grid = True)

# 1. scrape the data
data_all = scrape_all()

# 2. show the SNAPCHAT candlestick plot
pandas_candlestick_ohlc(data_all[0])

# 3. compare stocks
compare_plot(data_all)

# call this show function at the end so all plots could show at the same time
plt.show()
