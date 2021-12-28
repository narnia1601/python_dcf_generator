import csv
import json
import requests
from dotenv.main import dotenv_values

class GetValuations:
    def __init__(self, stock, exchange, stock_price_currency):  
        self.stock = stock
        self.token = dotenv_values('.env')['API_TOKEN']
        if exchange in ['NYSE','NASDAQ','BATS','OTCQB','PINK','OTCQX','OTCMKTS','NMFQS','NYSE MKT','OTCBB','OTCGREY','BATS','OTC']:
            self.exchange = 'US'
        else:
            self.exchange = exchange
        self.result: json
        self.stock_price_currency = stock_price_currency
        self.exchange_rate = 1
        self.total_debt: float
        self.interest_expense: float
        self.continuing_growth_rate = 0.02
        self.wacc: float

    def get_stock_data(self):
        response = requests.get(f'https://eodhistoricaldata.com/api/fundamentals/{self.stock}.{self.exchange}?api_token={self.token}')
        self.result = response.json()

    def get_revenue_estimate_growth(self):
        # find growth estimate from estimate provided
        try:
            next_year_earnings_value = list(self.result['Earnings']['Trend'].values())[0]['revenueEstimateGrowth']
            next_year_earnings_value = self.get_value(next_year_earnings_value)
        except:
            # find growth estimate from yearly revenues
            try: 
                revenue = list(self.result['Financials']['Income_Statement']['yearly'].values())[0]['totalRevenue']
                revenue = self.get_value(revenue)
                revenue_previous_year = list(self.result['Financials']['Income_Statement']['yearly'].values())[1]['totalRevenue']
                revenue_previous_year = self.get_value(revenue_previous_year)
                next_year_earnings_value = (revenue - revenue_previous_year) / revenue_previous_year
            except:
                # find growth estimate from quarterly revenues
                try:
                    revenue = list(self.result['Financials']['Income_Statement']['quarterly'].values())[0]['totalRevenue']
                    revenue = self.get_value(revenue)
                    revenue_previous_quarter = list(self.result['Financials']['Income_Statement']['quarterly'].values())[1]['totalRevenue']
                    revenue_previous_quarter = self.get_value(revenue_previous_quarter)
                    next_year_earnings_value = (revenue - revenue_previous_quarter) / revenue_previous_quarter
                except:
                    next_year_earnings_value = 0
        return float(next_year_earnings_value)

    def get_exchange_rate(self):
        currency_symbol = self.result['Financials']['Cash_Flow']['currency_symbol']
        if currency_symbol != None:
            if currency_symbol != self.stock_price_currency:
                response = requests.get(f'https://api.exchangerate-api.com/v4/latest/{currency_symbol}')
                result = response.json()
                self.exchange_rate = result['rates'][self.stock_price_currency]
    
    def get_unlevered_free_cash_flow(self):
        # try yearly to get interest expense
        try:
            self.interest_expense = list(self.result['Financials']['Income_Statement']['yearly'].values())[0]['interestExpense']
            self.interest_expense = self.get_value(self.interest_expense)
            free_cash_flow = list(self.result['Financials']['Cash_Flow']['yearly'].values())[0]['freeCashFlow']
            free_cash_flow = self.get_value(free_cash_flow)
        except:
            try:
            # try quarterly to get interest expense
                self.interest_expense = list(self.result['Financials']['Income_Statement']['quarterly'].values())[0]['interestExpense']
                self.interest_expense = self.get_value(self.interest_expense) * 4
                free_cash_flow = list(self.result['Financials']['Cash_Flow']['quarterly'].values())[0]['freeCashFlow']
                free_cash_flow = self.get_value(free_cash_flow) * 4
            except:
                free_cash_flow = 0
                self.interest_expense = 0.0
        return free_cash_flow - self.interest_expense

    def get_value(self, value):
        if value == None:
            return 0
        else:
            return float(value) * self.exchange_rate

    def get_cost_of_debt(self):
        self.get_unlevered_free_cash_flow()
        try:
            # get yearly cost_of_debt
            total_short_term_debt = list(self.result['Financials']['Balance_Sheet']['yearly'].values())[0]['shortLongTermDebt']
            total_short_term_debt = self.get_value(total_short_term_debt)
            total_long_term_debt = list(self.result['Financials']['Balance_Sheet']['yearly'].values())[0]['longTermDebt']
            total_long_term_debt = self.get_value(total_long_term_debt)
            self.total_debt = total_short_term_debt + total_long_term_debt
        except:
            try:
            # get quarterly cost_of_debt
                total_short_term_debt = list(self.result['Financials']['Balance_Sheet']['quarterly'].values())[0]['shortLongTermDebt']
                total_short_term_debt = self.get_value(total_short_term_debt)
                total_long_term_debt = list(self.result['Financials']['Balance_Sheet']['quarterly'].values())[0]['longTermDebt']
                total_long_term_debt = self.get_value(total_long_term_debt)
                self.total_debt = total_short_term_debt + total_long_term_debt
            except:
                self.total_debt = 0
        try:
            cost_of_debt = self.interest_expense / self.total_debt
        except:
            cost_of_debt = 0
        return cost_of_debt

    def get_risk_free_rate(self):
        download = requests.get(f'https://eodhistoricaldata.com/api/eod/US10Y.GBOND?api_token={self.token}')
        content = download.content.decode('utf-8')
        cr = csv.reader(content.splitlines(), delimiter=',')
        my_list = list(cr)
        return float(my_list[len(my_list) - 2][5]) / 100

    def get_cost_of_equity(self):
        risk_free_rate = self.get_risk_free_rate()
        beta = self.result['Technicals']['Beta']
        if beta == None:
            beta = 0
        market_risk_premium = 0.05
        return risk_free_rate + (beta * market_risk_premium)

    def get_wacc(self):
        cost_of_debt = self.get_cost_of_debt()
        cost_of_equity = self.get_cost_of_equity()
        # try yearly:
        try:
            revenue = list(self.result['Financials']['Income_Statement']['yearly'].values())[0]['totalRevenue']
            revenue = self.get_value(revenue)
            tax = list(self.result['Financials']['Income_Statement']['yearly'].values())[0]['incomeTaxExpense']
            tax = self.get_value(tax)
            tax_rate = tax / revenue
        except:
            try:
            # try quarterly
                revenue = list(self.result['Financials']['Income_Statement']['quarterly'].values())[0]['totalRevenue']
                revenue = self.get_value(revenue)
                tax = list(self.result['Financials']['Income_Statement']['quarterly'].values())[0]['incomeTaxExpense']
                tax = self.get_value(tax)
                tax_rate = tax / revenue
            except:
            # use previous year to determine tax rate
                try:
                    revenue_previous_year = list(self.result['Financials']['Income_Statement']['yearly'].values())[1]['totalRevenue']
                    revenue_previous_year = self.get_value(revenue_previous_year)
                    tax_previous_year = list(self.result['Financials']['Income_Statement']['yearly'].values())[1]['incomeTaxExpense']
                    tax_previous_year = self.get_value(tax_previous_year)
                    tax_rate = tax_previous_year / revenue_previous_year
                except:
                    # use quarter to determine tax rate
                    try:
                        revenue_recent_quarter = list(self.result['Financials']['Income_Statement']['quarterly'].values())[0]['totalRevenue']
                        revenue_recent_quarter = self.get_value(revenue_recent_quarter)
                        tax_recent_quarter = list(self.result['Financials']['Income_Statement']['quarterly'].values())[0]['incomeTaxExpense']
                        tax_recent_quarter = self.get_value(tax_recent_quarter)
                        tax_rate = tax_recent_quarter / revenue_recent_quarter
                    except:
                        try:
                        # use previous quarter to determine tax rate
                            revenue_previous_quarter = list(self.result['Financials']['Income_Statement']['quarterly'].values())[1]['totalRevenue']
                            revenue_previous_quarter = self.get_value(revenue_previous_quarter)
                            tax_previous_quarter = list(self.result['Financials']['Income_Statement']['quarterly'].values())[1]['incomeTaxExpense']
                            tax_previous_quarter = self.get_value(tax_previous_quarter)
                            tax_rate = tax_previous_quarter / revenue_previous_quarter
                        except:
                            tax_rate = 0
        try:
            # try from year
            total_stockholder_equity = list(self.result['Financials']['Balance_Sheet']['yearly'].values())[0]['totalStockholderEquity']
            total_stockholder_equity = self.get_value(total_stockholder_equity)
        except:
            try:
                # try from quarter
                total_stockholder_equity = list(self.result['Financials']['Balance_Sheet']['quarterly'].values())[0]['totalStockholderEquity']
                total_stockholder_equity = self.get_value(total_stockholder_equity)
            except:
                total_stockholder_equity = 0
        try:
            wacc_debt = (self.total_debt / (self.total_debt + total_stockholder_equity) * cost_of_debt * (1-tax_rate))
        except:
            wacc_debt = 0
        try:
            wacc_equity = (total_stockholder_equity / (self.total_debt + total_stockholder_equity) * cost_of_equity)
        except:
            wacc_equity = 0
        self.wacc = wacc_debt + wacc_equity

    def get_enterprise_value(self):
        self.get_wacc()
        unlevered_free_cash_flow = self.get_unlevered_free_cash_flow()
        total_value_of_present_value_of_forecasted_free_cash_flows = 0
        revenue_growth_rate = self.get_revenue_estimate_growth()
        for i in range(5):
            growth_rate = revenue_growth_rate - (i * 0.01)
            unlevered_free_cash_flow = unlevered_free_cash_flow * (1 + growth_rate)
            discount_factor = 1 / ((1 + self.wacc) ** (i + 1))
            present_value_of_free_cash_flow = unlevered_free_cash_flow * discount_factor
            if i == 4:
                continuing_value = unlevered_free_cash_flow * (1 + self.continuing_growth_rate) / (self.wacc - self.continuing_growth_rate)
                present_value_of_continuing_value = continuing_value / (1 + self.wacc) ** (i + 1)
            total_value_of_present_value_of_forecasted_free_cash_flows += present_value_of_free_cash_flow
        return total_value_of_present_value_of_forecasted_free_cash_flows + present_value_of_continuing_value

    def get_margin_of_safety(self):
        enterprise_value = self.get_enterprise_value()
        try:
            cash = list(self.result['Financials']['Balance_Sheet']['yearly'].values())[0]['cash']
            cash = self.get_value(cash)
        except:
            try:
                cash = list(self.result['Financials']['Balance_Sheet']['quarterly'].values())[0]['cash']
                cash = self.get_value(cash)
            except:
                cash = 0
        market_cap = self.result['Highlights']['MarketCapitalization']
        equity_value = enterprise_value - self.total_debt + cash
        shares_outstanding = self.result['SharesStats']['SharesOutstanding']
        try:
            price_per_share = market_cap / shares_outstanding
            value_per_share = equity_value / shares_outstanding
            margin_of_safety = value_per_share - price_per_share
        except:
            return 0
        return margin_of_safety / price_per_share

    def get_return_on_equity(self):
        return_on_equity = self.result['Highlights']['ReturnOnEquityTTM']
        return_on_equity = self.get_value(return_on_equity)
        return return_on_equity

    def get_gross_profit_margin(self):
        gross_profit = self.result['Highlights']['GrossProfitTTM']
        gross_profit = self.get_value(gross_profit)
        revenue = self.result['Highlights']['RevenueTTM']
        revenue = self.get_value(revenue)
        try:
            gross_profit_margin = gross_profit / revenue
        except:
            gross_profit_margin = 0
        return gross_profit_margin