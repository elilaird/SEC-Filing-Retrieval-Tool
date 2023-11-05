import os
import xlsxwriter
from datetime import datetime
from database_service import DatabaseService

class ModelGenerationService():
    def __init__(self, config):
        self.db = DatabaseService(config)
        self.config = config
    
    def generate_model(self, ticker):

        # get all filings for ticker
        yearly_reports = self.db.get_filings_by_ticker_and_type(ticker, '10-K')
        quarterly_reports = self.db.get_filings_by_ticker_and_type(ticker, '10-Q')
        all_reports = yearly_reports + quarterly_reports
        print(f"found {len(yearly_reports)} yearly reports for {ticker}")
        print(f"found {len(quarterly_reports)} quarterly reports for {ticker}")

        # get dates
        dates = []
        for report in all_reports:
            date_str = report['period_end_date']
            dates.append((datetime.strptime(date_str, '%B %d, %Y'), 'Y' if report['type'] == '10-K' else 'Q'))
        dates.sort(key=lambda x: x[0])
        all_reports.sort(key=lambda x: datetime.strptime(x['period_end_date'], '%B %d, %Y'))

        # open excel document 
        try:
            output_path = os.path.join(self.config.model_save_directory, f"{ticker}.xlsx")

            # check if save directory exists, if not then make it
            if not os.path.exists(self.config.model_save_directory):
                os.makedirs(self.config.model_save_directory)
            
            workbook = xlsxwriter.Workbook(output_path)
            worksheet = workbook.add_worksheet()
            worksheet.set_column('G:Z', 7)
        except Exception as e:
            print(f"Error opening excel document: {e}")
            return
        
        self._write_dates(worksheet, dates)
        self._write_template(worksheet)
        self._write_numbers(worksheet, all_reports)




        workbook.close()

    def _write_template(self, worksheet):
        worksheet.write(4, 0, 'Balance Sheet')
        worksheet.write(6, 1, 'Assets & Liabilities')
        worksheet.write(8, 2, 'Total Assets')
        worksheet.write(10, 2, 'Total Liabilities')
        worksheet.write(12, 2, 'Total Sockholder\'s Equity')

        worksheet.write(16, 0, 'Income Statement')
        worksheet.write(18, 1, 'Total Revenue')
        worksheet.write(20, 1, 'Net Income')
    
    def _write_numbers(self, worksheet, reports):
        for i, report in enumerate(reports):
            # write balance sheet
            worksheet.write(8, 6 + i, report['balance_sheets']['total_assets'] if report['balance_sheets']['total_assets'] else "N/A")
            worksheet.write(10, 6 + i, report['balance_sheets']['total_liabilities'] if report['balance_sheets']['total_liabilities'] else "N/A")
            worksheet.write(12, 6 + i, report['balance_sheets']['total_stockholders_equity'] if report['balance_sheets']['total_stockholders_equity'] else "N/A")

            # write income statement
            worksheet.write(18, 6 + i, report['income_statements']['total_revenue'] if report['income_statements']['total_revenue'] else "N/A")
            worksheet.write(20, 6 + i, report['income_statements']['net_income'] if report['income_statements']['net_income'] else "N/A")
            
        

    def _write_dates(self, worksheet, dates):
        for i, date in enumerate(dates):
            date, type = date
            if type == 'Y':
                date = date.year
            else:
                date = f"{self._get_financial_quarter(date)}Q{date.year}"
            worksheet.write(3, 6 + i, date)

    def _get_financial_quarter(self, date):
        return (date.month - 1) // 3 + 1