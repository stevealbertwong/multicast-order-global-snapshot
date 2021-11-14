
#########################################################################################################
#
#
#
#
#
# Networking Helpers
#########################################################################################################

import random as rand
import time 
import sys
import config
import socket

## send msg to all known processes -> called by user manually inputing a msg
# def multicast (self, payload, sequencer_msg=False):    
#     for process_id, _ in enumerate(config.config['hosts']):
#         self.push_outgoing_msg_queue(process_id, payload=payload, sequencer_msg=sequencer_msg)
    

## logic specific to type of msg 
def push_outgoing_msg_queue(self, packet):
    """ Push an outgoing message to the message queue """
    
    # all types of msg have a unique id 
    self.msg_id_mutex.acquire()
    self.msg_id += 1 
    self.msg_id_mutex.release()


    ## for simplicity, only kv pairs implemented vector clock, reliable multicast, delay, random drop 
    if packet.msg_type == "send_money" or "send_iphone":
        ## bump vector clock before send()
        if self.multicast_order == "causal":
            self.vector_timestamp_mutex.acquire()
            self.vector_timestamp[self.node_id] += 1
            self.vector_timestamp_mutex.release()
        
        self.unack_messages_mutex.acquire()
        self.unack_messages.append(packet)
        self.unack_messages_mutex.release()
        
        if rand.random() <= self.drop_rate: ## simulates random drop, stored in unack_msgs so resend
            return            
        
        ## buffer before send(), since not using sync code
        send_time = time.time() + rand.uniform(0, 2) # 1234892919.655932 == Tue Feb 17 10:48:39 2009     
    
        self.outgoing_msg_queue_mutex.acquire()
        self.outgoing_msg_queue.append((send_time, packet)) 
        ## https://stackoverflow.com/questions/3121979/how-to-sort-list-tuple-of-lists-tuples
        self.outgoing_msg_queue.sort(key=lambda tup: tup[0]) ## sort by 1st element of tuple 
        self.outgoing_msg_queue_mutex.release()
    else:
        send_time = time.time()
        self.outgoing_msg_queue_mutex.acquire()
        self.outgoing_msg_queue.append((send_time, packet)) 
        self.outgoing_msg_queue.sort(key=lambda tup: tup[0]) ## sort by 1st element of tuple 
        self.outgoing_msg_queue_mutex.release()
    


#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################


## TODO -> seems very buggy
# each ps init sockets with every other ps 
def init_socket(self): ## sockets = empty []
    # ports = pick_free_ports(num_processes * (num_processes - 1)) ## os syscall
    # ## port_mapping: {(0, 1): (1001, 1002), (1, 2): (1005, 1006), (0, 2): (1003, 1004)}    
    # port_mapping = {}
    # counter = 0
    # for i in range(self.num_processes):
    #     for j in range(i + 1, self.num_processes):
    #         port_mapping[(i, j)] = (ports[counter], ports[counter + 1])
    #         counter = counter + 2
    
    ## membership list    
    backlog = 10    
    try:
        # self.socket.bind(socket.gethostname(), self.port) ## bind your socket with user defined port
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) ## port binding bug: https://stackoverflow.com/questions/5875177/how-to-close-a-socket-left-open-by-a-killed-program
        self.socket.bind(('', self.port)) ## bind your socket with user defined port

        self.socket.listen(backlog)
        
    except:
        print("ERROR : your own socket creation failed.")
        sys.exit(1)



    # for i in range(self.node_id):
    #     other_ps_ip, other_ps_port = config.config['hosts'][i]

    # 	## socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     ## socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    #     try:
    #         self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) ## UDP ??
    #         self.socket.bind((socket.gethostname(), self.port)) ## bind your socket with user defined port
    #         self.socket.listen(backlog)
    #     except:
    #         print("ERROR : Socket creation failed.")
    #         sys.exit(1)
        
    #     other_ps_sock, host, client_port = self.socket.accept()
    #     self.sockets.append(other_ps_sock)
    # self.sockets.append(None)        
    





#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################


#########################################################################################################
#
#
#
#
#
# Global Snapshot Helpers
#########################################################################################################


# def save_snapshot_state(pid, snapshot_id, state):
#     """state is a tuple of (logical, vector, asset) where logical is an int,
#     vector is a list, state is [iphone, money]"""

#     logical = state[0]
#     vector = " ".join(str(i) for i in state[1])
#     asset = state[2]
#     content = "id {} : snapshot {} : logical {} : vector {} : money {} : widgets {}\n".format(
#         pid, snapshot_id, logical, vector, asset[1], asset[0]
#     )

#     filename = os.path.dirname(os.path.realpath(__file__)) + "/../../snapshots/snapshot." + str(pid)
#     with open(filename, "a") as f: ## append
#         f.write(content)



# def save_snapshot_channel(pid, snapshot_id, channel, channel_id):
#     content = ''
#     for entry in channel['data']: ## channel: dict
#         type = entry[0]

#         asset_type = ''
#         if type == 'send_iphone':
#             asset_type = 'iphone'
#         else:
#             asset_type = 'money'

#         amount = entry[1]
#         logical_timestamp = entry[2]
#         vector_timestamp = entry[3:]

#         vector_timestamp_str = " ".join(str(i) for i in entry[3:])

#         ## message in transit during marker period
#         content = content + "id {} : snapshot {} : logical {} : vector {} : message {} to {} : {} {}\n".format(
#             pid, snapshot_id, logical_timestamp, vector_timestamp_str, channel_id, pid, asset_type, amount
#         )

#     snapshot_dir = os.path.dirname(os.path.realpath(__file__)) + "/../../snapshots/"
#     filename = snapshot_dir + "snapshot." + str(pid)
#     with open(filename, "a") as f:
#         f.write(content)

  # print "________________________________________________________"							
        # print (self.name).upper() + ": Snapshot recording completed. Snapshot Id :" + snapshot.getMarkerId() + " initiated by " + sender
        # outputFile.write((self.name).upper() + ": Snapshot recording completed. Snapshot Id :" + snapshot.getMarkerId() + " initiated by " + sender + "\n")
        # print (self.name).upper() + ": Process State : " + str(snapshot.getProcessState())
        # outputFile.write( (self.name).upper() + ": Process State : " + str(snapshot.getProcessState())+"\n")

        # print (self.name).upper() + ": Channel " + name_info["client1"].upper() + " to " + self.name.upper() + " state : " + str(snapshot.getChannelOne().queue)
        # outputFile.write( (self.name).upper() + ": Channel " + name_info["client1"].upper() + " to " + self.name.upper() + " state : " + str(snapshot.getChannelOne().queue)+"\n")
        # print (self.name).upper() + ": Channel " + name_info["client2"].upper() + " to " + self.name.upper() + " state : " + str(snapshot.getChannelTwo().queue)
        # outputFile.write( (self.name).upper() + ": Channel " + name_info["client2"].upper() + " to " + self.name.upper() + " state : " + str(snapshot.getChannelTwo().queue)+"\n")
        # print (self.name).upper() + ": Channel " + name_info["client3"].upper() + " to " + self.name.upper() + " state : " + str(snapshot.getChannelThree().queue)
        # outputFile.write( (self.name).upper() + ": Channel " + name_info["client3"].upper() + " to " + self.name.upper() + " state : " + str(snapshot.getChannelThree().queue)+"\n")
        # del snapshotIdValue[markerId]
        # print "________________________________________________________"
        # outputFile.close()



# SNAPSHOT_DICT[initiator_id]['channel_states'][self.id]['flag'] = False
# def create_snapshot_dict(self):
#     SNAPSHOT_DICT[client_id] = {}
#     for client in TOTAL_CLIENTS:
#         proc_id = PROC_ID_MAPPING[str(client)]['proc_id']
#         SNAPSHOT_DICT[proc_id] = {}
#     for key in SNAPSHOT_DICT:
#         channel_states = {}
#         for client in TOTAL_CLIENTS:
#             key1 = PROC_ID_MAPPING[str(client)]['proc_id']
#             channel_states[key1] = {}
#             channel_states[key1]['flag'] = False
#             channel_states[key1]['state'] = []
#         SNAPSHOT_DICT[key] = {'SAVED_STATEN':None,'SAVING_STATEN':False,'channel_states': channel_states}





#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################

#########################################################################################################
#
#
#
#
#
# other helpers
#########################################################################################################

def return_random(smaller_boundary, bigger_boundary, seed): ## between 0, 1
    rand = random.Random()
    rand.seed(seed)
    probability = rand.uniform(smaller_boundary, bigger_boundary)
    return probability

def update_logical_timestamp(local_timestamp, received_timestamp):
    return max(local_timestamp, received_timestamp) + 1

def update_vector_timestamp(local_timestamp, received_timestamp):
    new_timestamp = [0] * len(local_timestamp)
    for i in range(len(local_timestamp)):
        new_timestamp[i] = max(local_timestamp[i], received_timestamp[i])
    return new_timestamp








