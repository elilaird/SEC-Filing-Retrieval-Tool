from pymongo import MongoClient, ASCENDING, errors

class DatabaseService:
    def __init__(self, config):
        self.client = MongoClient(f'mongodb://{config.db_user}:{config.db_password}@{config.db_host}:{config.db_port}')
        self.db = self.client[config.db_name]
        self.collection = self.db[config.collection]

        self.collection.create_index([('ticker', ASCENDING), ('type', ASCENDING), ('period_end_date', ASCENDING), ('file', ASCENDING)], unique=True)

    def insert_filing(self, filing):
        try:
            self.collection.insert_one(filing)
        except errors.DuplicateKeyError:
            print("Duplicate document, skipping insert.")

    def get_all_filings(self):
        return list(self.collection.find())

    def get_filings_by_ticker(self, ticker):
        return list(self.collection.find({'ticker': ticker}))
    
    def get_filings_by_ticker_and_type(self, ticker, type):
        return list(self.collection.find({'ticker': ticker, 'type': type}))
    
    def check_exists(self, ticker, type, period_end_date, file):
        if self.collection.find_one({'ticker': ticker, 'type': type, 'period_end_date': period_end_date, 'file': file}):
            return True
        else: 
            return False

    def delete_filing(self, filing_id):
        self.collection.delete_one({'_id': filing_id})
