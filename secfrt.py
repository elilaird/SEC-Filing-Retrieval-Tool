import argparse 
import os

from data_processing_service import DataProcessingService
from model_generation_service import ModelGenerationService
from database_service import DatabaseService
from analytics_service import AnalyticsService
from configs.base import config

from pprint import pprint

parser = argparse.ArgumentParser(description='SEC Document Tool')
parser.add_argument('command', type=str, help='command to run')
parser.add_argument('-t', '--ticker', type=str, help='ticker to run command on')
parser.add_argument('-a', '--analysis_type', type=str, help='analysis type to run', default='dataframe')

args = parser.parse_args()

dps = DataProcessingService(config)
db = DatabaseService(config)
mgs = ModelGenerationService(config)
analytics = AnalyticsService(config)

# check command type
if args.command == 'process':

    print(f"Downloading yearly reports (10-K) for {args.ticker}")
    dps.download_filings(args.ticker, '10-K', limit=4)

    print(f"Downloading quarterly reports (10-Q) for {args.ticker}")
    dps.download_filings(args.ticker, '10-Q', limit=16)

    print(f"Processing 10-K filings for {args.ticker}")
    yearly_filings = dps.parse_filing(args.ticker, '10-K', overwrite=False)

    print(f"Processing 10-Q filings for {args.ticker}")
    quarterly_filings = dps.parse_filing(args.ticker, '10-Q', overwrite=False)

    filings = yearly_filings + quarterly_filings

    print(f"Saving filings for {args.ticker} to database")
    dps.save_filings(filings)

    print(f"Done processing {args.ticker}")

elif args.command == 'analyze':

    if args.analysis_type == 'forecast_yearly':
        print(f"forecasting yearly for {args.ticker}")
        df = analytics.forecast_yearly_by_company(args.ticker, 'Total Revenue')
        print(df)

    elif args.analysis_type == 'forecast_quarterly':
        print(f"forecasting quarterly for {args.ticker}")
        df = analytics.forecast_quarterly_by_company(args.ticker, 'Total Revenue')
        print(df)

    elif args.analysis_type == 'stats_yearly':
        print(f"calculating statistics for {args.ticker} aggregated over years")
        df = analytics.stats_yearly_by_company(args.ticker)
        print(df)

    elif args.analysis_type == 'dataframe':
        pprint(analytics.get_dataframe(args.ticker))
    else:
        print(f"analysis type {args.analysis_type} not found")

elif args.command == 'generate':
    print(f"generating model for {args.ticker}")
    if mgs.generate_model(args.ticker):
        print(f"model saved to {os.path.join(config.model_save_directory, args.ticker)}.xlsx")
    else:
        print(f"No data for {args.ticker}.  Run process command first.")

else:
    print(f"command {args.command} not found")
    print("available commands: process, analyze, generate")

