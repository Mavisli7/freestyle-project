
from bs4 import BeautifulSoup
import pandas as pd
from urllib.request import urlopen
import numpy as np
import matplotlib.pyplot as plt

def welcome():
    '''
    welcome message
    '''
    print("-------------------------------------------------------")
    print("Welcome to the stock scraping and compare application.")
    print("-------------------------------------------------------")
    print("Please enter the stock symbol names you'd like to look up (e.g. SNAP, TWTR, FB).")
    print("The symbols could be looked up at https://finance.yahoo.com/lookup/.")
    print("Please Enter 'DONE' if you have finished\n")

def stock_inputs():
    '''
    input stocks by user
    '''
    stocks=[]
    while True:
        name= input("Please enter the stock symbol: ")
        name = name.upper().strip() 
        if name == "DONE":
            if len(stocks) == 0:
                print("Please input at least one stock symbol.")
            else:
                break
        else:
            stocks.append([name, 'https://finance.yahoo.com/quote/'+name+'/history?p='+name])
    return stocks

#scrape data from web
def scrape_data(stock):
    '''
    scrape data from yahoo finance
    '''
    data=[]
    try:
        html=urlopen(stock[1])
        soup=BeautifulSoup(html, "html.parser")
        div=soup.find("div", {"id": "Main"})
        table=div.find_next("table", {"data-test": "historical-prices"})
        tbody=table.find_next('tbody')
        #scrape the data
        for row in tbody.find_all('tr'):
            col=row.find_all('td')
            if len(col) < 7:
                # avoid cases such as 'Dividend'
                continue
            data.append([col[0].find_next('span').text]+
                        [float(td.find_next('span').text.replace(',','')) for td in col[1:]])
        return pandas_frame(np.array(data))
    except:
        print('Something went wrong with symbol "'+stock[0]+'"...please check your symbol name')
        return None
    finally:
        try:
            if soup:
                soup.decompose()
            if html:
                html.close()
        except NameError:
            pass

def pandas_frame(data):
    '''
    Transform to pandas dataframe for analysis
    '''
    df = pd.DataFrame(data=data[0:,1:],
            index=data[0:,0],
            columns=['Open','High','Low','Close','Adj Close','Volume'])
    df=df.apply(pd.to_numeric, errors='ignore')
    df.index.name='Date'
    df.index = pd.to_datetime(df.index, format='%b %d, %Y')
    return df

def scrape_all():
    '''
    scrape all data in stocks
    '''
    data_all=[]
    for s in stocks:
        data_all.append(scrape_data(s))
    return data_all

def compare_plot(date_all, compare_field='Adj Close'):
    '''
    compare the stocks in a plot
    '''
    dic=dict()
    secondary_y=[]
    for idx, data in enumerate(data_all):
        if data is None:
            continue
        
        dic[stocks[idx][0]] = data[compare_field]
        secondary_y.append(stocks[idx][0])
    
    if len(dic) == 0:
        print('No valid stocks to show')
    else:
        df = pd.DataFrame(dic)
        df.plot(secondary_y = secondary_y, grid= True)
        plt.show()

# 0. welcome
welcome()

# 1. users input the stocks
stocks=stock_inputs()

# 2. scrape data
print("Scraping the data from Yahoo finance...")
data_all=scrape_all()

# 3. compare stocks
print("Compare stocks...")
compare_plot(data_all)
