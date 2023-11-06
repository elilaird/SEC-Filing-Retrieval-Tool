from datetime import datetime
import pandas as pd
import warnings
warnings.filterwarnings('ignore', category=UserWarning)
from sklearn.linear_model import LinearRegression

from database_service import DatabaseService

class AnalyticsService():
    def __init__(self, config):
        self.db = DatabaseService(config)
        self.config = config

    def forecast_yearly_by_company(self, ticker, target_variable):
    
        # get all filings for ticker
        filings = self.db.get_filings_by_ticker_and_type(ticker, '10-K')
        print(f"found {len(filings)} filings for {ticker}")

        # sort by date
        filings.sort(key=lambda x: datetime.strptime(x['period_end_date'], '%B %d, %Y'))

        # get numericals
        df = self._get_numericals_df(filings)
        df_temp = df.drop('Date', axis=1)
        df[df_temp.columns] = df_temp.fillna(df_temp.mean())   

        X = df[['Date']]
        y = df[target_variable]

        # check if y is all NaN
        if y.isnull().all():
            print(f"no data for {target_variable}")
            return None
    
        model = LinearRegression()
        model.fit(X, y)

        # predict next year
        next_year = datetime.now().year + 1
        prediction = model.predict([[next_year]])

        return prediction[0]
    
    def stats_yearly_by_company(self, ticker):

        # get all filings for ticker
        filings = self.db.get_filings_by_ticker_and_type(ticker, '10-K')
        print(f"found {len(filings)} filings for {ticker}")

        # sort by date
        filings.sort(key=lambda x: datetime.strptime(x['period_end_date'], '%B %d, %Y'))

        # get numericals
        df = self._get_numericals_df(filings)
        df.set_index('Date', inplace=True)
        df.fillna(df.mean(), inplace=True)

        # Calculate the averages and standard deviation of the data
        averages = df.mean()
        stds = df.std()

        # Create a DataFrame from the averages and stds
        stats_df = pd.DataFrame({'Mean': averages, 'Standard Deviation': stds})

        return stats_df

    def forecast_quarterly_by_company(self, ticker, target_variable):
        # get all filings for ticker
        filings = self.db.get_filings_by_ticker_and_type(ticker, '10-Q')
        print(f"found {len(filings)} filings for {ticker}")

        # sort by date
        filings.sort(key=lambda x: datetime.strptime(x['period_end_date'], '%B %d, %Y'))

        # get numericals
        df = self._get_numericals_df(filings, quarterly=True)
        df_temp = df.drop('Date', axis=1)
        df[df_temp.columns] = df_temp.fillna(df_temp.mean()) 

        X = df[['Date']]
        y = df[target_variable]

        # check if y is all NaN
        if y.isnull().all():
            print(f"no data for {target_variable}")
            return None
    
        model = LinearRegression()
        model.fit(X, y)

        # predict next year
        next_year = datetime.now().year + 1
        prediction = model.predict([[next_year]])

        return prediction[0]
    
    def get_dataframe(self, ticker):
        # get all filings for ticker
        filings = self.db.get_filings_by_ticker(ticker)
        print(f"found {len(filings)} filings for {ticker}")

        # sort by date
        filings.sort(key=lambda x: datetime.strptime(x['period_end_date'], '%B %d, %Y'))

        # get numericals
        df = self._get_clean_numericals(filings)

        return df
    
    def _get_clean_numericals(self, filings):
        data = []

        for filing in filings:
            date = datetime.strptime(filing['period_end_date'], '%B %d, %Y')
            if filing['type'] == '10-Q':
                date = f"{self._get_financial_quarter(date)}Q{date.year}"
            else:
                date = str(date.year)
            total_revenue = filing['income_statements']['total_revenue']
            net_income = filing['income_statements']['net_income']
            total_assets = filing['balance_sheets']['total_assets']
            total_liabilities = filing['balance_sheets']['total_liabilities']
            total_stockholders_equity = filing['balance_sheets']['total_stockholders_equity']

            data.append([date, total_revenue, net_income, total_assets, total_liabilities, total_stockholders_equity])
        
        df = pd.DataFrame(data, columns=['Date', 'Total Revenue', 'Net Income', 'Total Assets', 'Total Liabilities', 'Total Stockholders Equity'])

        return df


    def _get_financial_quarter(self, date):
        return (date.month - 1) // 3 + 1

    def _get_numericals_df(self, filings, quarterly=False):
        # Initialize an empty list to store the data
        data = []

        # Extract the numerical values and the year from each filing
        for filing in filings:
            
            date = datetime.strptime(filing['period_end_date'], '%B %d, %Y')
            if quarterly:
                date = str(date.year + (date.month / 12))
            else:
                date = str(date.year)
            total_revenue = filing['income_statements']['total_revenue']
            net_income = filing['income_statements']['net_income']
            total_assets = filing['balance_sheets']['total_assets']
            total_liabilities = filing['balance_sheets']['total_liabilities']
            total_stockholders_equity = filing['balance_sheets']['total_stockholders_equity']

            # Add the data to the list
            data.append([date, total_revenue, net_income, total_assets, total_liabilities, total_stockholders_equity])

        # Create a DataFrame from the data
        df = pd.DataFrame(data, columns=['Date', 'Total Revenue', 'Net Income', 'Total Assets', 'Total Liabilities', 'Total Stockholders Equity'])

        return df



