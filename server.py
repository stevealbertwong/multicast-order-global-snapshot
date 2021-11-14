import operator
import threading
import sys
import json
from packet import Packet 
import config
import socket
import random as rand
import time
from collections import namedtuple
from multiprocessing import Queue

from helpers import *


MONEY = 0
IPHONE = 1

# each ps runs a global snapshot multicast ordering server 
class GSMOServer:
    def __init__(self, node_id):

        ###################################### 
        # init + import from config
        ######################################      
        self.node_id = node_id
        print( "node_id : ", node_id)

        (self.ip, self.port) = config.config['hosts'][self.node_id]
        self.is_sequencer = True if self.node_id == config.config['sequencer_id'] else False ## total order, https://stackoverflow.com/questions/2802726/putting-a-simple-if-then-else-statement-on-one-line
        self.multicast_order = config.config['multicast_order'] ## total or causal 
        self.num_processes = config.config['num_processes']
        self.num_snapshots = config.config['num_snapshots']
        self.message_max_size = config.config['message_max_size']
        self.delay_time = config.config['delay_time']
        self.drop_rate = config.config['drop_rate']


        ###################################### 
        # multicast ordering data structure
        ######################################       
        
        self.received_msgs_history = [] ## gateway for filtering: avoid processing dup msgs (due to reliable multicast unack)
        
        self.buffered_packets_queue = [] ## causal order (out of vector timestamp order)
        self.vector_timestamp = [0] * self.num_processes        
        
        self.original_msg_queue = [] ## total order 
        self.sequencer_msg_queue = [] ## total order (out of sequence no. order)
        self.global_sequence_num = 0 ## total order: if this node is sequencer, keep global
        self.local_sequence_num = 0 ## total order


        self.unack_messages = [] ## ack handler periodically resends all unack msgs        



        ###################################### 
        # global snapshot algo data structure!!!!
        ######################################                 
        ## channels -> 2D dict(num_processes x num_snapshots)
        ## -> to guarantee consistent cut

        # self.channels = [ [{'data':[], 'is_recording': False} for i in range(self.num_processes)] for j in range(self.num_snapshots)]
        self.channels = [{'packets':[], 'num_packets': 0, 'is_recording': False} for i in range(self.num_processes)] # https://stackoverflow.com/questions/13368498/python-object-as-dictionary-value
        self.saved_snapshots = [ [{'state'}, { 'channel_data': [{'packets':[], 'num_packets': 0} for i in range(self.num_processes) ]} ] for j in range(self.num_snapshots)]
        self.marker_received = [False] * self.num_snapshots ## marker message
        self.snapshot_id = 0 ## count of snapshot taken
        self.snapshotting = False ## stops simulation before global snapshot for simplicity 


        # self.num_channels_recorded = 0 ## end global snapshotting    


        ###################################### 
        # general
        ######################################  
        self.state = {"money" : config.config['starting_money'], "iphone" : config.config['starting_iphone']} ## {"money": 10, "iphone": 10}
        self.outgoing_msg_queue = [] ## (send_time, packet), sorted at all time to just pop()
        self.incoming_msg_queue = []
        self.msg_id = 0 ## this node's msg count

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) ## this node's socket, UDP ??
        self.sockets = [] ## each ps is connected to all ps' sockets
        init_socket(self)

        self.start_threaded_handlers() 


        ###################################### 
        # locks
        ###################################### 
        self.msg_id_mutex = threading.Lock() 
        self.state_mutex = threading.Lock()
        self.sockets_mutex = threading.Lock()
        self.outgoing_msg_queue_mutex = threading.Lock()
        self.vector_timestamp_mutex = threading.Lock()
        self.buffered_packets_queue_mutex = threading.Lock()
        self.channels_mutex = threading.Lock()
        self.received_msgs_history_mutex = threading.Lock()
        self.unack_messages_mutex = threading.Lock()
        self.marker_received_mutex = threading.Lock()
        self.markers_received_mutex = threading.Lock()
        self.snapshotting_mutex = threading.Lock()
        self.saved_snapshot_mutex = threading.Lock()
        self.original_msg_queue_mutex = threading.Lock()
        self.sequencer_msg_queue_mutex = threading.Lock()
        self.buffered_packets_queue_mutex = threading.Lock()
        self.global_sequence_num_mutex = threading.Lock()


        # self.inv_types = {v:k for k, v in types.items()} ## reverse lookup

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
    # global snapshot 
    # 
    #########################################################################################################

    def marker_handler(self, marker_packet):
        
        ## 1st marker msg -> save_snapshot_state() + start saving data msgs received in channel[][] + broadcast marker 
        if self.marker_received[marker_packet[marker_packet.snapshot_id]] == False: 
            self.marker_received_mutex.acquire()
            self.marker_received[marker_packet[marker_packet.snapshot_id]] = True
            self.marker_received_mutex.release()
            
            self.markers_received_mutex.acquire()
            self.markers_received += 1
            self.markers_received_mutex.release()

            self.snapshotting_mutex.acquire()
            self.snapshotting = True
            self.snapshotting_mutex.release()
            
            self.save_snapshot_state(self, marker_packet)
            
            ## multicast resend() marker msg to all outgoing channels
            for j in range(self.num_processes):
                if j != self.node_id:

                    self.channels_mutex.acquire()
                    self.channels[marker_packet[marker_packet.snapshot_id]][j]['is_recording'] = True
                    self.channels_mutex.release()
                    
                    self.msg_id_mutex.acquire()
                    self.msg_id += 1
                    self.msg_id_mutex.release()

                    packet = Packet(j, self.node_id, "marker", marker_packet.snapshot_id)
                    
                    self.outgoing_msg_queue_mutex.acquire()
                    self.outgoing_msg_queue.append(packet)
                    self.outgoing_msg_queue_mutex.release()
        

        ## 2nd marker msg -> save_snapshot_channel() + stop recording channel msgs
        else: 

            if self.channels[marker_packet[marker_packet.snapshot_id]]['is_recording']:
                self.channels[marker_packet[marker_packet.snapshot_id]]['is_recording'] = False
                self.markers_received += 1
                
                self.save_snapshot_channel(self.node_id, marker_packet[marker_packet.snapshot_id], self.channels[marker_packet[marker_packet.snapshot_id]][i], i)
                
                ## stop global snapshotting
                if self.markers_received == self.num_processes - 1: ## all ps have sent marker back 
                    self.num_channels_recorded += 1 ## ??
                    self.markers_received = 0 
                    self.snapshot_id += 1
                    self.snapshotting = False 
                
                if (self.node_id == 0 and self.num_channels_recorded == self.num_processes - 1) or (self.node_id != 0 and self.num_channels_recorded == self.num_processes - 2):
                    return



    ## self.channels/state -> self.saved_snapshots
    def save_snapshot_channel(self, packet):
        for i in self.num_processes: # i: ps index

            self.saved_snapshot_mutex.acquire()
            self.saved_snapshots[packet.snapshot_id]['channels'][i]['num_packets'] = self.channels[i]['num_packets']
            self.saved_snapshot_mutex.release()
            
            for j in self.channels[i]['num_packets']: # j: packet index
                self.saved_snapshot_mutex.acquire()
                self.saved_snapshots[packet.snapshot_id]['channels'][i][j] = self.channels[i]['packets'][j]
                self.saved_snapshot_mutex.release()
    


    def save_snapshot_state(self, packet):
        self.saved_snapshot_mutex.acquire()
        self.saved_snapshots[packet.snapshot_id]['state'] = self.state # tuple
        self.saved_snapshot_mutex.release()

      



    # TODO
    ## loop thru snapshot dict to print state n all channels 
    # def retrieve_snapshot_handler(self, snapshot_id):





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
    # multicast ordering
    #
    #########################################################################################################

  
    def deliver(self, packet):
        """ update() KV data list + timestamps + global snapshots channels if recording"""
        

        # ## incorporate other process vector timestamp (NOT vector seq no)
        # update_logical_timestamp(self.logical_timestamp, logical_timestamp)        
        # self.vector_timestamp[self.node_id] += 1 ## bump local timestamps
        # update_vector_timestamp(self.vector_timestamp, vector_timestamp)

        ## updates KV data list        
        if packet.msg_type == "send_money":   
            self.state_mutex.acquire()             
            self.state['money'] += packet.value
            self.state_mutex.release()

        if packet.msg_type == "send_iphone":    
            self.state_mutex.acquire()                  
            self.state['iphone'] += packet.value
            self.state_mutex.release()

        print("iphone : " + self.state['money'] + "moeny : " + self.state['iphone'])



    
    def causal_order(self, data_packet): 
        """ 
        KEY: each element == how many msg that ps has delivered to you itself in order 
        HARDEST: deal with weird cases e.g. (0,0,0,1) (0,0,0,2) (0,0,0,3) 

        if you are ps 2, and your vector timestamp is (1,2,2,1)
        
        ps 1's vector (2,2,2,1) == casual order 
        ps 1's vector (2,2,1,1) == casual order 
        ps 1's vector (2,2,0,0) == casual order, possible only p1, p2 receives each other packets
        
        ps 1's vector (3,2,2,1) =/= casual order 
        ps 1's vector (2,1,2,1) =/= casual order 
        ps 1's vector (1,2,3,1) =/= casual order 
        ps 1's vector (2,2,3,1) =/= casual order 
        

        buffer vs deliver logic !!!!!!!!
        - BOTH cases need to be satisfied to be "delivered"
            - 1st: only next packet from sender
            - 2nd: if sender already bumped by other PS, means "happens before", buffers to wait for original sender packets
            - i.e. even if next packet from sender, if our timestamp is behind sender's on other ps's elements, buffer
        - LIFO 
            - keep looping until all packets are cleared
            - newly arrived packets "deliver" many buffered packets
        """            
        ready_to_deliver = []

        while True:

            ## determine if newly received packet is the next packet
            ## TODO: dont think these are the packet's fields 
            for j, (sender_id, vector_timestamp, data_packet) in enumerate(self.buffered_packets_queue):
                found_next_packet = True

                for i in range(len(vector_timestamp)): # vector_timestamp == seq no. NOT actual clock
                    # 1st: only next packet from sender
                    if i == sender_id:
                        if vector_timestamp[i] != self.vector_timestamp[i] + 1: # not next packet
                            found_next_packet = False
                    # 2nd: wait for original sender packet as that is "happens-before"
                    else: 
                        if vector_timestamp[i] > self.vector_timestamp[i]:
                            found_next_packet = False            
                
            ## if next packet, updated your timestamp, restart again
            if found_next_packet:
                ready_to_deliver.append((sender_id, vector_timestamp, data_packet))   

                self.vector_timestamp_mutex.acquire()
                self.vector_timestamp[sender_id] += 1 ## update your own vector timestamp
                self.vector_timestamp_mutex.release()

                self.buffered_packets_queue_mutex.acquire()
                del self.buffered_packets_queue[j]
                self.buffered_packets_queue_mutex.release()
            ## if no, leave the buffered packets,  
            else:
                break

        ## deliver == formally deemed as received 
        for packet in ready_to_deliver:            
            self.deliver(packet) 




    def total_order(self, packet): 
        """
        a newly arrived next packet could unleash many next packets in the buffer
        original_msg_queue + sequencer_msg_queue -> delivered

        which ps is central sequencer == user defined 
        is_central_sequencer == included in every packet sent

        every ps has 2 holdback_queue + holdback_queue_markers
        there is a chance either one could be missing packets

        
        called when recv() new orignal or sequencer msg
        deliver() orignal msg according to global seq no in sequencer msg
        """
        ## sort() sequencer msg == only the 1st one might match
        ## dont sort just for loop, for loop is only O(N), sort likely O(n log n) -> but now it is used multiple times
        ## https://stackoverflow.com/questions/3121979/how-to-sort-list-tuple-of-lists-tuples
        # self.sequencer_msg_queue.sort(key=lambda tup: tup[2]) ## sort by 3rd element of tuple 
        # https://stackoverflow.com/questions/4010322/sort-a-list-of-class-instances-python
        self.sequencer_msg_queue.sort(key=operator.attrgetter('seq_no'))
        
        while True:

            found_next_packet = False
            if self.local_sequence_num + 1 == int(self.sequencer_msg_queue[0].m_sequence):

                ## use message_id to for loop every recevied packets
                for i, m_packet in enumerate(self.original_msg_queue):        
                    
                    if(m_packet.sender_id == packet.sender_id and m_packet.msg_id == packet.msg_id):
                    
                        self.deliver(m_packet) 

                        ## https://stackoverflow.com/questions/11520492/difference-between-del-remove-and-pop-on-lists/11520540
                        self.original_msg_queue_mutex.acquire()
                        del self.original_msg_queue[i]
                        self.original_msg_queue_mutex.release()

                        self.sequencer_msg_queue_mutex.acquire()
                        del self.sequencer_msg_queue[0]
                        self.sequencer_msg_queue_mutex.release()
                        found_next_packet = True ## original_msg_queue might not arrive yet
                        

            if found_next_packet == False:
                break ## not deliver() this round -> no more matching         



    #########################################################################################################
    #
    #
    #
    #
    #
    # kv pairs 
    #
    #########################################################################################################


    def kv_handler(self, packet):
        """ Receive UDP messages from other processes 
        store them in the holdback queue.
        buffer before append vector_clock in RAM """

        ## 1. if recording channels (marker mode), store all received packets 
        
        if packet.msg_type == "send_money" or "send_iphone": 
            for i in range(len(self.channels)): ## num_processes
                if self.channels[i]['is_recording']:
                    self.channels_mutex.acquire()
                    self.channels[i]['packets'].append(packet)
                    self.channels[i]['num_packets'] += 1
                    self.channels_mutex.release()

        ## 2. reply ack to sender
        ack_packet = Packet(self.sender_id, packet.sender_id, "ack", self.msg_id)
        push_outgoing_msg_queue(ack_packet) 
        
        ## 3. ensure packet's ordering
        ## causal ordering
        if self.multicast_order == 'causal':
            
            self.buffered_packets_queue_mutex.acquire()
            self.buffered_packets_queue.append(packet)
            self.buffered_packets_queue_mutex.release()
            
            ## TODO: thread this
            self.causal_order(packet) ## buffered_packets_queue -> delivered

        ## total ordering        
        elif self.multicast_order == 'total':

            ## 1. orignal msg
            ## run by BOTH sequencer + non-sequencer 
            if packet.msg_type != "sequencer_msg": 

                ## run ONLY by sequencer (to broadcast sequencer msg)
                if self.node_id == config.sequencer_id: ## if this node is sequencer                     
                    for _, receiver_id in enumerate(config.config['hosts']):
                        seq_packet = Packet(self.node_id, receiver_id, 'sequencer_msg', packet.msg_id, total_seq_no = self.global_sequence_num)
                        push_outgoing_msg_queue(seq_packet)                    
                    
                    self.global_sequence_num_mutex.acquire()
                    self.global_sequence_num += 1 
                    self.global_sequence_num_mutex.release()

                ## run by BOTH sequencer + non-sequencer 
                self.original_msg_queue_mutex.acquire()
                self.original_msg_queue.append(packet) 
                self.original_msg_queue_mutex.release()

                ## TODO: thread this
                self.total_order(packet) ## maybe already next seq no., but missing original msg

            ## 2. sequencer msg
            ## run ONLY by NON sequencer (since sent by sequencer)
            else:                 
                self.sequencer_msg_queue_mutex.acquire()
                self.sequencer_msg_queue.append(packet)
                self.sequencer_msg_queue_mutex.release()

                ## TODO: thread this
                self.total_order(packet) ## maybe just missing next seq no.




    def ack_handler(self, packet):    
        for m_packet in self.unack_messages:
            if packet.sender_id == m_packet.sender_id & packet.msg_id == m_packet.msg_id:
                self.unack_messages_mutex.acquire()
                del m_packet
                self.unack_messages_mutex.release()



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
    # threads
    #########################################################################################################


    ## no race condition since only this function touches all its data structure
    def receiver_thread(self):
        """ Thread that listens for incoming UDP messages """
        while True:
            
            ## TODO: class object -> string in payload
            ## https://stackoverflow.com/questions/34600003/converting-json-to-string-in-python
            ## https://stackoverflow.com/questions/6578986/how-to-convert-json-data-into-a-python-object
            packet_string = self.socket.recv()
            packet_json = json.loads(packet_string)
            # Parse JSON into an object with attributes corresponding to dict keys.
            packet = json.loads(packet_json, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
            

            ## 1. received_msgs_history == filter to avoid duplicate packets            
            ## reliable == resend == possiblities duplicate
            if self.already_received(packet.sender_id, packet.msg_id): 
                continue
            
            self.received_msgs_history_mutex.acquire()
            self.received_msgs_history.append((packet.sender_id, packet.msg_id)) # tuple
            self.received_msgs_history_mutex.release()

            ## 2.                       
            if packet.msg_type == "send_money" or "send_iphone" or "sequencer_msg":
                # TODO: thread this
                self.kv_handler(packet)
                
            elif packet.msg_type == "marker":
                # TODO: thread this
                self.marker_handler(packet)

            elif packet.msg_type == "ack":
                # TODO: thread this
                self.ack_handler(packet)
            

    ## search thru received_msgs_history list, if found, dont run msg's handler again
    def already_received(self, sender_id, msg_id):
        for (m_sender_id, m_msg_id) in self.received_msgs_history:
            if m_sender_id == sender_id & m_msg_id == msg_id: 
                return True 


        
    ###################################
    # simulates each process randomly multicasts to other processes
    #
    # -> bump vector clock before acked 
    # -> as MO gurantee packets' deliver() order even late re-send
    # 
    #
    # 0. stop transfer while snapshot process is going on - for simplicity
    # 1. random target ps, random send time, random value of iphone n money 
    # 2. bump vector timestamp before send
    # 3. push to send_queue, then while sleep loop to send at random time 
    # 4. 
    # 4. 
    # 5. 
    #
    #
    # 
    #     
    ###################################
    
    def simulate_multicasting_thread(self):
        
        while True:

            if self.snapshotting: 
                time.sleep(1)
                continue

            random_receiver_id = rand.randint(0, self.num_processes - 2)

            if rand.uniform(0, 1) > 0.5: ## 1/2 chance send money
                
                money_left = self.state["money"]
                if money_left <= 0:
                    pass
                else:
                    value = rand.randint(1, int(money_left/3)+1)
                    
                    self.state_mutex.acquire()
                    self.state["money"] = self.state["money"] - value                    
                    self.state_mutex.release()
                    
                    packet = Packet(self.msg_id, self.node_id, random_receiver_id, "send_money", value, self.vector_timestamp)
                    
                    self.outgoing_msg_queue_mutex.acquire()
                    self.outgoing_msg_queue.append(packet)
                    self.outgoing_msg_queue_mutex.release()
            

            elif rand.uniform(0, 1) <= 0.5: # 1/2 chance send iphone            
                iphone_left = self.state["iphone"]
                if iphone_left <= 0:
                    pass
                else:
                    value = rand.randint(1, int(iphone_left/3)+1)
                    
                    self.state_mutex.acquire()
                    self.state["iphone"] = self.state["iphone"] - value
                    self.state_mutex.release()
                    
                    if self.multicast_order == "causal":
                        
                        self.vector_timestamp_mutex.acquire()
                        self.vector_timestamp[id] = self.vector_timestamp[id] + 1
                        self.vector_timestamp_mutex.release()

                    packet = Packet(random_receiver_id, "send_iphone", value, self.vector_timestamp)
                    
                    self.outgoing_msg_queue_mutex.acquire()
                    self.outgoing_msg_queue.append(packet)
                    self.outgoing_msg_queue_mutex.release()

            
            ## only sequencer process randomly take snapshot num_snapshot of times
            # if self.node_id == config.sequencer_id:        

            #     if rand.uniform(0, 1) <= self.sending_probability:
            #         save_snapshot_state(self.node_id, snapshot_id, (logical_timestamp, vector_timestamp, asset))                
            #     self.marker_received[snapshot_id] = True
                
            #     for i in range(1, num_processes):
            #         self.channels[snapshot_id][i]['is_recording'] = True
            #         push_outgoing_msg_queue(i, msg_types['marker'], [snapshot_id])
                
            #     self.snapshot_id += 1
            #     if self.snapshot_id == self.num_snapshot: ## this thread dies when taken enough snapshot
            #         break 



    ###################################### 
    # periodically sends out messages when send time <= current_time
    # 
    # -> why not send() right away ??
    ######################################          

    def outgoing_msg_queue_thread(self):    
        while True:
            if self.outgoing_msg_queue: ## not empty
                (send_time, packet) = self.outgoing_msg_queue.get() ## first one ??
                if send_time <= time.time():
                    sock = self.sockets[packet.receiver_id]
                    ## https://stackoverflow.com/questions/34600003/converting-json-to-string-in-python
                    ## https://pythonexamples.org/convert-python-class-object-to-json/
                    packet_string = json.dumps(packet.__dict__)
                    sock.sendall(packet_string)
                
                self.outgoing_msg_queue_mutex.acquire()
                del self.outgoing_msg_queue[0]
                self.outgoing_msg_queue_mutex.release()

            else:
                time.sleep(0.1)

    ###################################### 
    # periodically re-sends unack msgs 
    # 
    # -> bump vector clock when send() not when resend() here 
    # -> as MO gurantee packets' deliver() order even late re-send
    # -> no race condition since locked
    ######################################                 

    def resend_ack_thread(self):
        while True:
            if self.unack_messages: ## not empty
                for packet in self.unack_messages:                
                    push_outgoing_msg_queue(packet)
            else:
                time.sleep(0.2)


    # 
    # no while true loop == since run only 1 time
    def init_cluster_sockets_thread(self):
        

        ## init sockets with all ps greater node_id than yourself 
        ## intuition: earlier ps would have already established conn w you (see the graph)
        for i in range(self.node_id + 1, self.num_processes):
            # (source_port, destination_port) = port_mapping[(id, i)]
            other_ps_ip, other_ps_port = config.config['hosts'][i]
            
            print ("hellow world 1", other_ps_ip, other_ps_port) 

            while True:
                try:
                    other_ps_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    # addr = socket.gethostname() ## all ps are localhost 
                    # other_ps_sock.bind((self.ip, self.port))
                    other_ps_sock.connect((other_ps_ip, other_ps_port))
                    print ("hellow world 2")

                    self.sockets_mutex.acquire()
                    self.sockets.append(other_ps_sock)
                    self.sockets_mutex.release()
                    break ## next ps 
                except:
                    # print ("hellow world exception")
                    time.sleep(0.1) ## wait for all fork finishes
        
        ## set timeouts for sockets
        for i in range(self.num_processes):
            if i == id:
                continue
            self.sockets_mutex.acquire()
            self.sockets[i].settimeout(0.01)    
            self.sockets_mutex.release()




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
    def start_threaded_handlers(self):
        thread_routines = [ 
            self.init_cluster_sockets_thread,
            self.receiver_thread,
            self.simulate_multicasting_thread,
            self.outgoing_msg_queue_thread,
            self.resend_ack_thread
            ]

        threads = []
        for thread_routine in thread_routines:
            thread = threading.Thread(target=thread_routine)
            thread.daemon = True
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()



    #########################################################################################################
    #########################################################################################################
    #########################################################################################################
    #########################################################################################################
    #########################################################################################################
    #########################################################################################################
    #########################################################################################################
    #########################################################################################################



## Console thread only to get the information from console - Done
# class user_input_thread(threading.Thread):
# 	def __init__(self,name,inputQueueLock, snapshotQueueLock):
# 		threading.Thread.__init__(self)
# 		self.name = name
# 		self.inputQueueLock = inputQueueLock
# 		self.snapshotQueueLock = snapshotQueueLock
	
# 	def run(self):		
# 		global clientCount 
# 		clientCount = 0			
# 		while(True):
# 			while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
#   				line = sys.stdin.readline().strip()
#   				if (line.split()[0] == "Snap"):
# 					self.snapshotQueueLock.acquire()
# 					snapshotQueue.put("Snapshot")
# 					self.snapshotQueueLock.release()
# 				elif (line.split()[0]=="Quit"):					
# 					exitQueue.put(line)					
# 					break				
# 				else:
# 					print (self.name).upper() + ": Invalid input"	
# 			if (not exitQueue.empty()):				
# 				break	

# def push_outgoing_msg_queue():
    

# def simulate_sending_kv_pairs():
#     clientChosen = random.randint(1,3)
#     debitAmount = random.randint(1,100)


