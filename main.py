#!/usr/bin/env python3
import logging
import sys
import os
import multiprocessing as mp
import random
from server import *
from helpers import *
import json

from config import config

# logger = logging.getLogger()

# def startLoggin():
#     global logger
#     print 'I have started logging ! Check the logs !'
#     log_file_name= client_id+ "_client.log"
    
#     logger.setLevel(logging.DEBUG)
    
#     #creating logger file
#     handler=logging.FileHandler(log_file_name)
#     handler.setLevel(logging.DEBUG)

#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     handler.setFormatter(formatter)
#     logger.addHandler(handler)


# logger.info('Initialization is complete for snapshot dict')
# logger.debug(SNAPSHOT_DICT)


## simulates DS w multi-process on same machine
def fork_multiple_processes(num_processes):

    processes = []    

    for i in range(num_processes):
        ## https://docs.python.org/2.7/library/multiprocessing.html
        p = mp.Process(target=GSMOServer(i), args=(i))        
        # p = mp.Process(target=GSMOServer(i))
        p.start() 
        processes.append(p)

    for p in processes:
        p.join()


if __name__ == '__main__':
    
    with open('config.json') as data_file:    
        data = json.load(data_file)
        TCP_IP = data['tcp_ip']
        num_processes = data['num_processes']
        PROC_ID_MAPPING = data['reverse_dict']



    # logger.setLevel(logging.DEBUG)
    # console_handler = logging.StreamHandler(sys.stdout)
    # formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s]"
    #                               "[%(levelname)-5.5s]  %(message)s")
    # console_handler.setFormatter(formatter)
    # logger.addHandler(console_handler)

    ## starts DS simulation
    fork_multiple_processes(num_processes) 
