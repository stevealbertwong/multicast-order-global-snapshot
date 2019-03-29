#########################################################################################################
#
#
#
#
#
# multi-process simulation with socket
# 
#########################################################################################################

#!/usr/bin/env python3
import logging
import sys
import os
import multiprocessing as mp
import random
from handlers import *
from helpers import *

from config import config

logger = logging.getLogger()


def fork_multiple_processes():

    ## simulates DS w multi-process on same machine
    processes = []    

    for i in range(num_processes):
        ## python multi-process
        p = mp.Process(target=GSMOServer(), args=(i))        
        p.start() 
        processes.append(p)

    for p in processes:
        p.join()


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s]"
                                  "[%(levelname)-5.5s]  %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    ## starts DS simulation
    fork_multiple_processes() 
