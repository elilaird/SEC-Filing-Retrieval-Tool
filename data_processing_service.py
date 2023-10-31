import requests
from bs4 import BeautifulSoup
import re
import os
from sec_edgar_downloader import Downloader


class DataProcessingService:
    def __init__(self, config):
        self.config = config
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
    
    def get_and_parse(self, ticker, type):
        
        # check if local files exist in cache directory
        assert ticker in os.listdir(self.cache_dir), f"No local files found for {ticker}"
        assert type in os.listdir(os.path.join(self.cache_dir, ticker)), f"No local files found for {ticker} {type}"
        assert len(os.listdir(os.path.join(self.cache_dir, ticker, type))) > 0, f"No local files found for {ticker} {type}"


        filings = []
        # parse each file
        for file in os.listdir(os.path.join(self.cache_dir, ticker, type)):
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

            # find quarter end date
            quarter_end_date = self._find_quarter_end_date(soup)
            filing['quarter_end_date'] = quarter_end_date if quarter_end_date else 'NA'

            # find model values 
            for key in self.config.model_values:
                filing[key] = self._parse_table(soup, key)

            filings.append(filing)
            

    def _parse_table(self, soup, key):
        table = {}
        table_values = self.config.model_values[key]
        table_table = self._find_table_after_id(soup, key)
        if table_table is not None:
            for value in table_values:
                row = self._find_row_with_text(table_table, value)
                if row is not None:
                    table[value] = row
                else:
                    table[value] = 'NA'
        else:
            for value in table_values:
                table[value] = 'NA'
        return table


    def _find_quarter_end_date(soup):
        p_tag = soup.find(string=re.compile("For the Quarter Ended"))
        if p_tag:
            return p_tag
        else:
            return None
    
    def _find_table_after_id(soup, id):
        p_tag = soup.find(id=id)
        if p_tag:
            table = p_tag.find_next('table')
            return table
        else:
            return None

    def _find_row_with_text(table, text):
        rows = table.find_all('tr')
        for row in rows:
            if text in row.text:
                return row
        return None
