from easydict import EasyDict as edict

config = edict()

config.db_name = 'financials'
config.collection = 'sec_filings'
config.db_host = '0.0.0.0'
config.db_port = 27017
config.db_user = 'root'
config.db_password = 'password'

config.company = 'LairdInvestments'
config.email = 'elilaird3@gmail.com'

config.cache_dir = 'sec-edgar-filings'

config.model_save_directory = 'models'