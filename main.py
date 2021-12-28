from get_tickers import GetTickers
from get_valuations import GetValuations
import os.path

stock_exchange = input('Enter a stock exchange you would like to analyse: ').title()

if not os.path.isfile(f'{stock_exchange}.txt'):
    getTickers = GetTickers(stock_exchange.title())
    getTickers.getTickers()
    with open(f'{stock_exchange}.txt', 'r') as myfile:
        stocks_to_watch_list = []
        for line in myfile:
            line = line.rstrip('\n')
            line = line.split(',')
            getValuations = GetValuations(line[0],line[1],line[2])
            getValuations.get_stock_data()
            getValuations.get_exchange_rate()
            revenue_estimate_growth = getValuations.get_revenue_estimate_growth()
            margin_of_safety = getValuations.get_margin_of_safety()
            return_on_equity = getValuations.get_return_on_equity()
            gross_profit_margin = getValuations.get_gross_profit_margin()
            if revenue_estimate_growth >= 0.15 and margin_of_safety >= 0.2 and return_on_equity > 0.09 and gross_profit_margin >= 0.4:
                stocks_to_watch_list.append((line[0],margin_of_safety))
            print(f'{line[0]}: '+"{:.0%}".format(margin_of_safety))
        print(stocks_to_watch_list)
else:
    with open(f'{stock_exchange}.txt', 'r') as myfile:
        stocks_to_watch_list = []
        for line in myfile:
            line = line.rstrip('\n')
            line = line.split(',')
            getValuations = GetValuations(line[0],line[1],line[2])
            getValuations.get_stock_data()
            getValuations.get_exchange_rate()
            revenue_estimate_growth = getValuations.get_revenue_estimate_growth()
            margin_of_safety = getValuations.get_margin_of_safety()
            return_on_equity = getValuations.get_return_on_equity()
            gross_profit_margin = getValuations.get_gross_profit_margin()
            if revenue_estimate_growth >= 0.15 and margin_of_safety >= 0.2 and return_on_equity > 0.09 and gross_profit_margin >= 0.4:
                stocks_to_watch_list.append((line[0],margin_of_safety))
            print(f'{line[0]}: '+"{:.0%}".format(margin_of_safety))
        print(stocks_to_watch_list)