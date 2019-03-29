class GSMOServer:
    def __init__(self, node_id):

        ###################################### 
        # init + import from config
        ######################################      
        self.node_id = node_id
        self.multicast_order = config.config['multicast_order']
        self.num_processes = config.config['num_processes']
        self.num_snapshots = config.config['num_snapshots']
        self.message_max_size = config.config['message_max_size']
        self.delay_time = config.config['delay_time']
        self.drop_rate = config.config['drop_rate']
        self.mutex = threading.Lock()

        ###################################### 
        # multicast ordering data structure
        ######################################       

        self.wait_packets_queue = [] ## causal order waiting packets
        self.original_msg_queue = [] ## total order
        self.sequencer_msg_queue = [] ## total order
        self.global_sequence_num = 0 ## if this node is sequencer
        self.local_sequence_num = 0 ## for every node -> before deliver()
        self.unack_messages = [] ## ack handler periodically resends all unack msgs
        self.vector_clock ## vector clock could be increased due to own state changes
        self.vector_seq_no ## vector seq no only increase when send() to another peer
        self.received_msgs_history ## message received before

        ###################################### 
        # global snapshot algo data structure!!!!
        ######################################                 
        ## channels -> 2D dict(num_processes x num_snapshots)
        ## -> to guarantee consistent cut
        self.channels = [[{'data':[], 'is_recording': False} for i in range(self.num_processes)] for j in range(self.num_snapshots)]
        self.snapshot_id = 0 ## count of snapshot taken
        self.num_channels_recorded = 0 ## end global snapshotting
    
        self.logical_timestamp = 0
        self.vector_timestamp = [0] * config.num_processes    
        self.marker_received = [False] * config.num_snapshots ## marker message    

        ###################################### 
        # simulation data structure, spawn threaded handlers
        ######################################                         
        self.sending_probability = return_random(0.4, 0.8, self.node_id) ## id: seed
        self.asset = [config.starting_money, config.starting_iphone] ## each ps starting amount
        self.outgoing_queue = PriorityQueue() ## sort by its send_time
        
        self.inv_types = {v:k for k, v in types.items()} ## reverse lookup
        self.socket ## this node's socket
        self.sockets = [] ## membership list -> [node_id] = socket
        self.msg_id = 0 ## this node's msg count
                
        self.init_membership_list(self.sockets) 
        self.start_threaded_handlers() 


    #########################################################################################################
    #
    #
    #
    #
    #
    # global snapshot 
    # 
    #########################################################################################################

    def handle_marker_msg(self, marker_packet):
        
        ## 1st marker msg -> save_snapshot_state() + start saving data msgs received in channel[][]
        if self.marker_received[marker_packet[SNAPSHOT_ID]] == False: 
            self.marker_received[marker_packet[SNAPSHOT_ID]] = True            
            save_snapshot_state(self.node_id, parsed_msg[SNAPSHOT_ID], (self.logical_timestamp, self.vector_timestamp, self.asset))
            
            ## multicast resend() marker msg to all outgoing channels
            for j in range(self.num_processes):
                if j != self.node_id:
                    self.channels[marker_packet[SNAPSHOT_ID]][j]['is_recording'] = True
                    unicast_send(j, MARKER, snapshot_id)
        
        ## 2nd marker msg -> save_snapshot_channel() + stop recording channel msgs
        else: 
            if self.channels[marker_packet[SNAPSHOT_ID]][i]['is_recording']:
                self.channels[marker_packet[SNAPSHOT_ID]][i]['is_recording'] = False
                
                save_snapshot_channel(self.node_id, marker_packet[SNAPSHOT_ID], channels[marker_packet[SNAPSHOT_ID]][i], i)
                
                ## stop global snapshotting
                if snapshot_id_received == self.num_snapshots - 1: ## last snapshot
                    self.num_channels_recorded += 1
                if (self.node_id == 0 and self.num_channels_recorded == self.num_processes - 1) or (self.node_id != 0 and self.num_channels_recorded == self.num_processes - 2):
                    return


    #########################################################################################################
    #
    #
    #
    #
    #
    # multicast ordering
    #
    #########################################################################################################

    def receive_parse():        
        packet, _ = self.socket.recvfrom(self.message_max_size)                
        return parse_packet(packet)        

    
    def deliver(self, data_packet): ## apply() from local buffer to local process
        """ update() KV data list + timestamps + global snapshots channels if recording"""        

        ## parse data_packet
        sender_id = data_packet[SENDER_NODE_ID]
        msg_type = data_packet[MESSAGE_TYPE]
        sequencer_msg = data_packet[IF_SEQUENCER_MSG] ## for total ordering
        message_id = data_packet[MESSSAGE_ID]
        vector_seq_no = data_packet[VECTOR_SEQ_NO]
        payload = data_packet[PAYLOAD]
        logical_timestamp = data_packet[LOGICAL_TIMESTAMP]
        vector_timestamp = data_packet[VECTOR_TIMESTAMP]

        ## incorporate other process vector timestamp (NOT vector seq no)
        update_logical_timestamp(self.logical_timestamp, logical_timestamp)        
        self.vector_timestamp[self.node_id] += 1 ## bump local timestamps
        update_vector_timestamp(self.vector_timestamp, vector_timestamp)

        ## updates KV data list
        money_received, iphone_received = parse_payload(payload) ## TODO
        if msg_type == SEND_MONEY:                
            asset[1] += money_received
        if msg_type == SEND_IPHONE:            
            asset[0] += iphone_received

        ## if record channels (marker mode) -> stores {money, logical timestamp, vector timestamp}
        for j in range(len(self.channels)):
            if self.channels[j][i]['is_recording']:
                self.channels[j][i]['data'].append(data_packet)

    
    def causal_order(self, data_packet): 
        """ 
        when receives new msg -> check multicast_queue causal order w msg
        deliver() buffered msgs that are in causal order

        causal packet == concurrent / causal next packet
        """            
        deliver_queue = []

        ## check all pervious packets that fit next causal packets
        ## test -> check sender's previous msg's time
        for (sender_id, vector_seq_no[:], data_packet), j in enumerate(self.wait_packets_queue):
            causal_packet = True

            for i in range(len(vector_seq_no)):
                if i == sender_id:
                    if vector_seq_no[i] != self.vector_seq_no[i] + 1:
                        causal_packet = False
                else: 
                    if vector_seq_no[i] > self.vector_seq_no[i]:
                        causal_packet = False            
            
            if causal_packet: ## send() + remove queued msg
                deliver_queue.append((sender_id, vector_seq_no[:], data_packet))
                del wait_packets_queue(j)

        ## send() then remove msg
        for sender_id, vector_seq_no[:], data_packet in deliver_queue:
            self.vector_seq_no[sender] += 1 ## bump vector seq no before locally_apply() 
            self.deliver(data_packet) ## deliver() !!!!!


    def total_order(self, data_packet): 
        """
        called when recv() new orignal or sequencer msg
        deliver() orignal msg according to global seq no in sequencer msg
        """
        ## https://stackoverflow.com/questions/3121979/how-to-sort-list-tuple-of-lists-tuples
        ## sort() sequencer msg according to global sequence num
        self.sequencer_msg_queue.sort(key=lambda tup: tup[2]) ## 3rd element

        ## sequencer msg
        for (m_sender, m_message_id, m_sequence), j in enumerate(self.sequencer_msg_queue): 

            if m_sequence != self.local_sequence_num + 1: ## if not next seq no.
                break

            ## orignal msg
            for (sender, message_id, message), i in enumerate(self.original_msg_queue):        
                
                ## matching orignal n seq msg + next seq no. 
                if sender == m_sender and message_id == m_message_id and 
                self.local_sequence_num == int(m_sequence):
                    
                    self.deliver(data_packet) ## deliver() !!!!!

                    ## https://stackoverflow.com/questions/11520492/difference-between-del-remove-and-pop-on-lists/11520540
                    del self.original_msg_queue[i] ## delete delivered msg
                    del self.sequencer_msg_queue[j]                                        
                    self.local_sequence_num += 1                
                    break        

            break ## not deliver() this round -> no more matching         

    def handle_data_msg(self, data_packet):
        """ Receive UDP messages from other processes 
        store them in the holdback queue.
        buffer before append vector_clock in RAM """

        sender_id = data_packet[SENDER_NODE_ID]
        msg_type = data_packet[MESSAGE_TYPE]
        sequencer_msg = data_packet[IF_SEQUENCER_MSG] ## for total ordering
        message_id = data_packet[MESSSAGE_ID]
        vector_seq_no = data_packet[VECTOR_SEQ_NO]
        payload = data_packet[PAYLOAD]

        self.unicast_send(data_packet[SENDER_ID], ACK) ## reply ack to sender

        if (sender, message_id) not in self.received_msgs_history: ## not dup msg
            self.received_msgs_history[(sender, message_id)] = True ## mark received from src

            ## causal ordering
            if self.multicast_order == 'causal':
                self.wait_packets_queue.append((sender_id, vector_seq_no[:], data_packet))
                self.causal_order(data_packet) ## CO wait_packets_queue -> deliver()

            ## total ordering        
            elif if self.multicast_order == 'total':
                if sequencer_msg: 
                    ## buffers at local until heard from sequencer
                    m_sequencer, m_sender, m_id = [int(x) for x in payload.split('::')]
                    self.sequencer_msg_queue.append((m_sender, m_id, m_sequencer))
                    self.total_order(data_packet) ## TO original_msg_queue + sequencer_msg_queue -> deliver()
                
                else: ## orignal msg
                    if self.node_id == config.sequencer_id: ## if this node is sequencer 
                        sequencer_message_payload = '::'.join([str(x) for x in [self.sequence_counter, sender, message_id]])
                        multicast(payload = sequencer_message_payload, sequencer_message=True) ## sequncer broadcast
                        self.global_sequence_num += 1 

                    self.original_msg_queue.append((sender, message_id, payload)) ## append original msg
                    self.total_order(data_packet) 

    def handle_ack_msg(self, parsed_msg):    
        del self.unack_messages[(parsed_msg[SENDER_ID], parsed_msg[MESSAGE_ID])]


    #########################################################################################################
    #
    #
    #
    #
    #
    # threaded handlers
    #########################################################################################################


    ## no race condition since only this function touches all its data structure
    def incoming_message_handler(self):
        """ Thread that listens for incoming UDP messages """
        while True:
            try:
                ## [sender_id, message_id, message_type, multicast_order, logical_timestamp, vector_timestamp, vector_seq_no, kv_pairs]
                parsed_msg = receive_parse()
                msg_type = parsed_msg[MESSAGE_TYPE]

                if msg_type == SEND_MONEY:
                    handle_data_msg(parsed_msg)

                elif msg_type == SEND_IPHONE:
                    handle_data_msg(parsed_msg)

                elif msg_type == MARKER:
                    handle_marker_msg(parsed_msg)

                elif msg_type == ACK:
                    handle_ack_msg(parsed_msg)


    ###################################
    # simulates each process randomly multicasts to other processes
    #
    # -> bump vector clock before acked 
    # -> as MO gurantee packets' deliver() order even late re-send
    ###################################
    
    def random_send_thread(self):
        
        while True:                    
            if rand.uniform(0, 1) <= self.sending_probability:
                dest_node_id = rand.randint(0, config.num_processes - 2)

                if rand.uniform(0, 1) > 0.5: ## 1/2 chance send money
                    
                    money_left = self.asset[MONEY]
                    if money_left <= 0:
                        pass
                    else:
                        buying_amount = rand.randint(1, int(money_left/3)+1)
                        self.asset[MONEY] = self.asset[MONEY] - buying_amount

                        ## bump vector clock before send()
                        self.logical_timestamp = logical_timestamp + 1
                        self.vector_timestamp[self.node_id] += 1
                        self.msg_id +=1

                        unicast_send(dest_node_id, self.msg_id, SEND_MONEY, [buying_amount, logical_timestamp] + vector_timestamp)
                

                elif rand.uniform(0, 1) <= 0.5: # 1/2 chance send iphone            
                    iphone_left = self.asset[IPHONE]
                    if iphone_left <= 0:
                        pass
                    else:
                        buying_amount = rand.randint(1, int(iphone_left/3)+1)
                        self.asset[IPHONE] = self.asset[IPHONE] - buying_amount
                        self.logical_timestamp = logical_timestamp + 1
                        self.vector_timestamp[id] = vector_timestamp[id] + 1

                        unicast_send(seller, msg_types['send_widget'], [buying_amount, logical_timestamp] + vector_timestamp)

            ## only sequencer process randomly take snapshot num_snapshot of times
            if self.node_id == config.sequencer_id:        

                if rand.uniform(0, 1) <= self.sending_probability:
                    save_snapshot_state(self.node_id, snapshot_id, (logical_timestamp, vector_timestamp, asset))                
                self.marker_received[snapshot_id] = True
                
                for i in range(1, num_processes):
                    self.channels[snapshot_id][i]['is_recording'] = True
                    unicast_send(i, msg_types['marker'], [snapshot_id])
                
                self.snapshot_id += 1
                if self.snapshot_id == self.num_snapshot: ## this thread dies when taken enough snapshot
                    break 

    ###################################### 
    # periodically sends out messages when send time <= current_time
    # 
    # -> why not send() right away ??
    ######################################          

    def outgoing_queue_thread(self):    
        while True:
            time.sleep(0.01)
            ## self.outgoing_queue -> priority queue
            (send_time, packet, dest_id, dest_ip, dest_port) = self.outgoing_queue.get(block=True)
            if send_time <= time.time():
                sock = self.sockets[dest_id]
                ## self.sock.sendto(message, (ip, port)) 
                sock.sendall(packet)

    ###################################### 
    # periodically re-sends unack msgs 
    # 
    # -> bump vector clock when send() not when resend() here 
    # -> as MO gurantee packets' deliver() order even late re-send
    # -> no race condition since locked
    ######################################                 

    def resend_ack_thread(self):
        while True:
            time.sleep(0.2)
            with self.mutex: ## lock self.unack_messages -> might receive() ack msg n delete() from it
                for dest_id, packed_message in self.unack_messages:
                    [_, message_id, is_ack, is_order_marker, message_timestamp, message] = unpack_message(packed_message)
                    self.unicast_send(dest_id, message, msg_id=message_id, is_ack=is_ack,
                                          is_order_marker=is_order_marker, timestamp=message_timestamp)


    def start_threaded_handlers(self, id):
        thread_routines = [ 
            self.incoming_message_thread,
            self.random_send_thread,
            self.resend_ack_thread,
            self.outgoing_queue_thread,
            ]

        threads = []
        for thread_routine in thread_routines:
            thread = threading.Thread(target=thread_routine)
            thread.daemon = True
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
