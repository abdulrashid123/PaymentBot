from logConfig import setup_logger
import logging
from EmailExtractor import Extractor

if __name__ == '__main__':
    setup_logger('main', 'logs/main.log')
    setup_logger('report', 'logs/report.log')
    main_log = logging.getLogger('main')
    report_log = logging.getLogger('report')
    obj = Extractor(main_log,report_log)
    obj.get_emails_data()
