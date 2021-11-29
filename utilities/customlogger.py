"""

 Class name: CustomLogger.py

 Description:
    This class contains a custom logger

"""

import logging
import os
import time

# Now, some additional information

__author__ = "Massimiliano Razzano"
__copyright__ = "Copyright 2016-2020, Massimiliano Razzano"
__credits__ = ["Line for credits"]
__license__ = "GPL"
__version__ = "0.1.0"
__maintainer__ = "M. Razzano"
__email__ = "massimiliano.razzano@pi.infn.it"
__status__ = "Production"


class CustomLogger(logging.Logger):
    """

    This class contains a custom logger

    """

    def __init__(self, m_name,m_file_logging=False,m_log_dir=None):
        # init start time
        self.__start_time = str(time.strftime("%y%m%d_%Hh%Mm%Ss", time.localtime()))
        self.__log_filename = None

        logging.Logger.__init__(self, m_name)

        base_handler = logging.StreamHandler()
        base_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s %(levelname)-4s: %(message)s', datefmt='%H:%M:%S')

        base_handler.setFormatter(formatter)
        self.addHandler(base_handler)


        if m_file_logging:
            if not os.path.exists(m_log_dir):
                os.mkdir(m_log_dir)

            #add a file logger
            if m_log_dir is None:
                file_handler_name = m_name+"_"+self.__start_time+".log"
            else:
                file_handler_name = os.path.join(m_log_dir,m_name+"_"+self.__start_time+".log")

            try:
                file_handler = logging.FileHandler(file_handler_name)
                self.__log_filename = file_handler_name
                self.addHandler(file_handler)
            except OSError:
                self.error("Cannot open the log file")


        self.info('Logger started at ' + self.__start_time + " (LEVEL=" + str(self.getEffectiveLevel()) + ")")
        if m_file_logging:
            self.info("Log file saved to "+file_handler_name)

        print("Logger " + m_name + " started")

    def get_log_filename(self):
        """

        :return:
        """

        return self.__log_filename

if __name__ == '__main__':
    print("\n****\nTesting custom Logger...\n****\n")

    my_logger = CustomLogger("testlogger")

    my_logger.setLevel(logging.DEBUG)
    my_logger.debug("This is a debug message")

    my_logger.setLevel(logging.INFO)
    my_logger.debug("This is an info message")

    my_logger.setLevel(logging.ERROR)
    my_logger.debug("...and this is an ERROR message!")
