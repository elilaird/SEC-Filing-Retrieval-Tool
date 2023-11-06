import re
import os
from io import StringIO
import pandas as pd
from bs4 import BeautifulSoup
from pymongo import MongoClient
from sec_edgar_downloader import Downloader
from database_service import DatabaseService
import copy
from datetime import datetime


_base_filing = {
    'ticker': 'NA',
    'type': 'NA',
    'file': 'NA',
    'period_end_date': 'NA',
    'income_statements': {
        'total_revenue': None,
        'net_income': None,
    }, 
    'balance_sheets': {
        'total_assets': None,
        'total_liabilities': None,
        'total_stockholders_equity': None,
    },
}

class DataProcessingService:
    def __init__(self, config):
        self.config = config

        # connect to mongodb
        self.client = MongoClient(f'mongodb://{self.config.db_user}:{self.config.db_password}@{self.config.db_host}:{self.config.db_port}')
        self.db = self.client[self.config.db_name]
        self.collection = self.db[self.config.collection]

        # set up database service
        self.db_service = DatabaseService(self.config)

        # set up downloader
        self.dl = Downloader(self.config.company, self.config.email)
        self.cache_dir = self.config.cache_dir
    
    def download_filings(self, ticker, filing_type, limit=None, after=None, before=None):
        try:
            self.dl.get(filing_type, ticker, limit=limit, after=after, before=before)
            return True
        except Exception as e:
            print(f"Failed to download filings for {ticker} {filing_type} {limit} {after} {before}")
            print(f"Exception: {e}")
            return False
    
    def parse_filing(self, ticker, type, overwrite=False):
        
        # check if local files exist in cache directory
        assert ticker in os.listdir(self.cache_dir), f"No local files found for {ticker}"
        assert type in os.listdir(os.path.join(self.cache_dir, ticker)), f"No local files found for {ticker} {type}"
        assert len(os.listdir(os.path.join(self.cache_dir, ticker, type))) > 0, f"No local files found for {ticker} {type}"


        filings = []
        # parse each file
        for file in os.listdir(os.path.join(self.cache_dir, ticker, type)):
            if file == '.DS_Store':
                continue
            soup = None
            try:
                with open(os.path.join(self.cache_dir, ticker, type, file, 'full-submission.txt'), 'r', encoding='utf-8', errors='ignore') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                if soup is None:
                    raise Exception(f"Failed to parse {file}")
            except Exception as e:
                print(f"Failed to parse {file}")
                print(f"Exception: {e}")
                continue
            
            filing = copy.deepcopy(_base_filing)
            filing['ticker'] = ticker
            filing['type'] = type
            filing['file'] = file
            
            filing['period_end_date'] = self._get_submission_date(os.path.join(self.cache_dir, ticker, type, file, 'full-submission.txt'))

            # find end date
            # if type == '10-K':
            #     fiscal_year_end_date = self._find_fiscal_year(soup, 'For the Fiscal Year Ended')#'For the Fiscal Year Ended')
            #     #filing['period_end_date'] = fiscal_year_end_date.replace('For the Fiscal Year Ended ', "") if fiscal_year_end_date else 'NA'
            #     filing['period_end_date'] = re.sub('For the Fiscal Year Ended ', "", fiscal_year_end_date, flags=re.IGNORECASE).replace('\xa0', ' ').strip() if fiscal_year_end_date else 'NA'

            # elif type == '10-Q':
            #     quarter_end_date = self._find_end_date(soup, 'For the Quarter(ly)? (period)? ')
            #     filing['period_end_date'] = re.sub('For the Quarter(ly)? (period)? (ended)?', "", quarter_end_date, flags=re.IGNORECASE).replace('\xa0', ' ').strip() if quarter_end_date else 'NA'

            print("\n------------------------\n")
            print(f"Processing {type} {filing['period_end_date']} for {ticker}...")
            print("\n------------------------\n")

            # check if filing already exists
            if not overwrite and self.db_service.check_exists(ticker, type, filing['period_end_date'], filing['file']):
                print(f"Filing {ticker} {type} {filing['period_end_date']} already exists, skipping.")
                continue

            # find all tables
            all_tables = soup.find_all('table')
            for table in all_tables:
                try:
                    table_df = pd.read_html(StringIO(str(table)))[0]
                    table_df = table_df.replace({'\$':''}, regex = True)\
                                            .replace({'\)':''}, regex = True)\
                                            .replace({'\(':''}, regex = True)\
                                            .replace({'\%':''}, regex = True)\
                                            .replace({' ','', 1}, regex = True)
                except Exception as e:
                    print(f"Exception: {e}")
                    continue
                
                # check for values in table
                try:
                    if filing['income_statements']['total_revenue'] is None:
                        if self._is_in_table(table_df, 'Total Revenues'):
                            row = self._find_row_in_table(table_df, 'Total Revenues')
                            filing['income_statements']['total_revenue'] = self._get_first_digit(row) * 1e6 if self._get_first_digit(row) is not None else None
                except Exception as e:
                    print(f"Error finding total revenue: {e}")

                try:
                    if filing['income_statements']['net_income'] is None:
                        if self._is_in_table(table_df, 'Net Income'):
                            row = self._find_row_in_table(table_df, 'Net Income')
                            filing['income_statements']['net_income'] = self._get_first_digit(row) * 1e6 if self._get_first_digit(row) is not None else None
                except Exception as e:
                    print(f"Error finding net income: {e}")

                try:
                    if filing['balance_sheets']['total_assets'] is None:
                        if self._is_in_table(table_df, 'Total Assets'):
                            row = self._find_row_in_table(table_df, 'Total Assets')
                            filing['balance_sheets']['total_assets'] = self._get_first_digit(row) * 1e6 if self._get_first_digit(row) is not None else None
                except Exception as e:
                    print(f"Error finding total assets equity: {e}")
    
                try:
                    if filing['balance_sheets']['total_liabilities'] is None:
                        if self._is_in_table(table_df, 'Total Liabilities'):
                            row = self._find_row_in_table(table_df, 'Total Liabilities')
                            filing['balance_sheets']['total_liabilities'] = self._get_first_digit(row) * 1e6 if self._get_first_digit(row) is not None else None
                except Exception as e:
                    print(f"Error finding total liabilities: {e}")

                try:
                    if filing['balance_sheets']['total_stockholders_equity'] is None:
                        if self._is_in_table(table_df, 'Total Stockholders\' Equity'):
                            row = self._find_row_in_table(table_df, 'Total Stockholders\' Equity')
                            filing['balance_sheets']['total_stockholders_equity'] = self._get_first_digit(row) * 1e6 if self._get_first_digit(row) is not None else None
                except Exception as e:
                    print(f"Error finding total stockholders' equity: {e}")
                        
                
                            
            filings.append(filing)

        return filings
            

    def _get_submission_date(self, file):
        # Open the file
        try:
            with open(file, 'r') as file:
                # Loop through each line in the file
                for line in file:
                    # If the line contains the string you're interested in, print it and the next line
                    if 'CONFORMED PERIOD OF REPORT:' in line:
                        line = line.replace('\n', '').replace('\t', '')
                        date = re.sub('CONFORMED PERIOD OF REPORT:', "", line)
                        date = datetime.strptime(date, '%Y%m%d')
                        return date.strftime('%B %d, %Y')
        except Exception as e:
            print(f"Failed to get submission date for {file}")
            print(f"Exception: {e}")
            return 'NA'

    def _get_first_digit(self, row):
        for value in row:
            if isinstance(value, str):
                if value.isdigit():
                    try:
                        value = int(value)
                        return value
                    except Exception:
                        return None
        return None
    
    def _is_in_table(self, table, value):
        mask = table.apply(lambda x: x.astype(str).str.contains(value, case=False))
        return mask.any().any()

    def _find_row_in_table(self, table, value):
        mask = table.apply(lambda x: x.astype(str).str.contains(value, case=False))
        row_df = table[mask[0]].dropna(axis=1, how='all', inplace=False).reset_index(drop=True).values.tolist()[0]
        return row_df


    def save_filings(self, filings):
        for filing in filings:
            try:
                self.db_service.insert_filing(filing)
            except Exception as e:
                print(f"Failed to save filing {filing}")
                print(f"Exception: {e}")
                continue

    def _parse_table(self, soup, key):
        table = {}
        table_values = self.config.model_values[key]
        table_table = self._find_table_after_id(soup, key)
        if table_table is not None:
            for value in table_values:
                row = self._find_row_with_text(table_table, value)
                if row is not None:
                    table[value] = self._strip_row(value, row.text)
                else:
                    table[value] = 'NA'
        else:
            for value in table_values:
                table[value] = 'NA'
        return table

    
    def _strip_row(self, value, str):
        return re.sub(value, '', str.replace('\n', '')).replace('$', '').replace('\xa0', ' ').replace(',', '').replace(chr(8217), '').replace('(', "").replace(")", "").strip().split(' ')[0]


    def _find_end_date(self, soup, str):
        #p_tag = soup.find(string=re.compile(str, re.IGNORECASE))
        p_tag = soup.find_all(lambda tag: tag.name == 'p' and bool(re.match(str, tag.get_text(), re.IGNORECASE)))
        if p_tag:
            return p_tag[0].text
        else:
            return None
        
    def _find_fiscal_year(self, soup, str):
        #p_tag = soup.find('p', string=re.compile(str, re.IGNORECASE))
        #p_tag = soup.find('ix:nonNumeric', attrs={'name': re.compile("dei:DocumentPeriodEndDate", re.IGNORECASE)})
        p_tag = soup.find_all(lambda tag: tag.name == 'p' and bool(re.match(str, tag.get_text(), re.IGNORECASE)))
        if p_tag:
            return p_tag[0].text
        else:
            return None
    
    def _find_table_after_id(self, soup, id):
        #p_tag = soup.find(id=id)
        #p_tag = soup.find_all('p', id=re.compile(id, re.IGNORECASE))
        p_tag = soup.find_all(lambda tag: tag.name == 'p' and bool(re.match(str, tag.get_id(), re.IGNORECASE)))
        if p_tag:
            table = p_tag[0].find_next('table')
            return table
        else:
            return None

    def _find_row_with_text(self, table, text):
        rows = table.find_all('tr')
        for row in rows:
            if re.search(text, row.text):
                return row
        return None
