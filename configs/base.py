from easydict import EasyDict as edict

config = edict()

config.company = 'LairdInvestments'
config.email = 'elilaird3@gmail.com'

config.cache_dir = 'sec-edgar-filings'

config.filing_types = ['10-Q']

config.income_statement_values = ['Total revenue', 'Total cost of revenue', 'Gross margin', 'Operating income', 'Net income']
config.comprehensive_income_statement_values = ['Net income', 'Comprehensive income']
config.balance_sheet_values = ['Total assets', 'Total current liabilities', 'Total liabilities', f"Total stockholders{chr(8217)} equity", f"Total liabilities and stockholders{chr(8217)} equity"]
config.cash_flow_values = ['Net cash from operations', 'Net cash( from)? \(?used in\)? financing', 'Net cash( from)? \(?used in\)? investing', 'Cash and cash equivalents, end of period']
config.stockholders_equity_values = [f"Total stockholders{chr(8217)} equity"]
#config.stockholders_equity_values = ['Common stock and paid-in capital', 'Balance, end of period', 'Retained earnings','Balance, end of period', 'Accumulated other comprehensive loss', 'Balance, end of period', f"Total stockholders{chr(8217)} equity"]


config.model_values = {
    'income_statements': config.income_statement_values,
    'comprehensive_income_statements': config.comprehensive_income_statement_values,
    'balance_sheets': config.balance_sheet_values,
    'cash_flows_statements': config.cash_flow_values,
    'stockholders_equity_statements': config.stockholders_equity_values
}