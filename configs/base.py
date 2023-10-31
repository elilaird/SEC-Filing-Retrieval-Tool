from easydict import EasyDict as edict

config = edict()

config.company = 'LairdInvestments'
config.email = 'elilaird3@gmail.com'

config.cache_dir = 'sec-edgar-filings'

config.filing_types = ['10-Q']

config.income_statement_values = ['Total revenue', 'Total cost of revenue', 'Gross margin', 'Operating income', 'Net income']
config.comprehensive_income_statement_values = ['Net income', 'Comprehensive income']
config.balance_sheet_values = ['Total assets', 'Total current liabilities', 'Total liabilities', "Total stockholders", "Total liabilities and stockholders"]
config.cash_flow_values = ['Net cash from operations', 'Net cash from (used in) financing', 'Net cash from (used in) investing', 'Cash and cash equivalents, end of period']
config.stockholders_equity_values = ['Common stock and paid-in capital', 'Balance, end of period', 'Retained earnings','Balance, end of period', 'Accumulated other comprehensive loss', 'Balance, end of period', 'Total stockholders']

config.model_values = {
    'income_statement': config.income_statement_values,
    'comprehensive_income_statement': config.comprehensive_income_statement_values,
    'balance_sheet': config.balance_sheet_values,
    'cash_flow': config.cash_flow_values,
    'stockholders_equity': config.stockholders_equity_values
}