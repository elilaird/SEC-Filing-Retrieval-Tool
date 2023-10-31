from sec_edgar_downloader import Downloader
from data_processing_service import DataProcessingService
from configs.base import config

from pprint import pprint

dps = DataProcessingService(config)

filing = dps.get_and_parse('MSFT', '10-Q')
pprint(filing)