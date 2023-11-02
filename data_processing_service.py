import re
import os
from bs4 import BeautifulSoup
from pymongo import MongoClient
from sec_edgar_downloader import Downloader
from database_service import DatabaseService


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
    
    def parse_filing(self, ticker, type):
        
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
            
            filing = {'ticker': ticker, 'type': type, 'file': file}

            # find end date
            if type == '10-K':
                fiscal_year_end_date = self._find_fiscal_year(soup, 'For the Fiscal Year Ended')
                filing['fiscal_year_end_date'] = fiscal_year_end_date.replace('For the Fiscal Year Ended ', "") if fiscal_year_end_date else 'NA'

            elif type == '10-Q':
                quarter_end_date = self._find_end_date(soup, 'For the Quarter Ended')
                filing['quarter_end_date'] = quarter_end_date.replace('For the Quarter Ended ', "") if quarter_end_date else 'NA'

            # find model values 
            for key in self.config.model_values:
                filing[key] = self._parse_table(soup, key)

            filings.append(filing)

        return filings
            
    # def save_filings(self, filings):
    #     for filing in filings:
    #         try:
    #             self.collection.insert_one(filing)
    #         except Exception as e:
    #             print(f"Failed to save filing {filing}")
    #             print(f"Exception: {e}")
    #             continue
        
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
        p_tag = soup.find(string=re.compile(str))
        if p_tag:
            return p_tag
        else:
            return None
        
    def _find_fiscal_year(self, soup, str):
        p_tag = soup.find('p', string=re.compile(str))
        text = p_tag.text
        if text:
            return text
        else:
            return None
    
    def _find_table_after_id(self, soup, id):
        p_tag = soup.find(id=id)
        if p_tag:
            table = p_tag.find_next('table')
            return table
        else:
            return None

    def _find_row_with_text(self, table, text):
        rows = table.find_all('tr')
        for row in rows:
            if re.search(text, row.text):
                return row
        return None
