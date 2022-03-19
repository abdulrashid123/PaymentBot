from __future__ import absolute_import

import logging
import os


def setup_logger(logger_name, log_file, level=logging.INFO):
    log_filename = log_file
    if not os.path.isfile(log_filename):
        with open(log_filename, 'w') as fp:
            pass
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s  %(name)s - %(levelname)s : %(message)s')
    fileHandler = logging.FileHandler(log_file, mode='a')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)