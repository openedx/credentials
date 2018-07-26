def assert_log_correct(log_capture, logger_name, log_level, log_message):
    """ Helper for testing correct log output. """
    log_capture.check_present(('{}'.format(logger_name), '{}'.format(log_level), '{}'.format(log_message),))
