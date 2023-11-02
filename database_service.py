from pymongo import MongoClient

class DatabaseService:
    def __init__(self, config):
        self.client = MongoClient(f'mongodb://{config.db_user}:{config.db_password}@{config.db_host}:{config.db_port}')
        self.db = self.client[config.db_name]
        self.collection = self.db[config.collection]

    def insert_filing(self, filing):
        self.collection.insert_one(filing)

    def get_all_filings(self):
        return list(self.collection.find())

    def get_filings_by_ticker(self, ticker):
        return list(self.collection.find({'ticker': ticker}))

    def delete_filing(self, filing_id):
        self.collection.delete_one({'_id': filing_id})