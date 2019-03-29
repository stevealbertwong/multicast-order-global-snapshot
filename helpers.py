
#########################################################################################################
#
#
#
#
#
# Networking Helpers
#########################################################################################################

def engineer_packet(payload_fields):
    return ('::'.join([str(x) for x in payload_fields])).encode('utf-8')

def parse_packet(payload):
	message = payload.decode('utf-8')
    sender_id, message_id, message_type, multicast_order, logical_timestamp, vector_timestamp, vector_seq_no, payload = message.split('::', 8)

    ## TODO: convert to right data type
	return [sender_id, message_id, message_type, multicast_order, logical_timestamp, vector_timestamp, vector_seq_no, payload]


## send msg to all known processes -> called by user manually inputing a msg
def multicast(self, payload, sequencer_msg=False):    
    for process_id, host in enumerate(config.config['hosts']):
        self.unicast_send(process_id, payload=payload, sequencer_msg=sequencer_msg)
    

## send to 1 known process
def unicast_send(self, dest_node_id, message_type, multicast_order, logical_timestamp, vector_timestamp, vector_seq_no, payload, sequencer_msg, snapshot_id):
    """ Push an outgoing message to the message queue """
    self.msg_id += 1

    ## engineer packets
    packet = engineer_packet([self.node_id, self.msg_id, message_type, multicast_order, logical_timestamp, stringify_vector_timestamp(vector_timestamp), vector_seq_no, payload, sequencer_msg, snapshot_id])
    dest_ip, dest_port = config.config['hosts'][dest_node_id]
    

    if message_type == ACK:
        with self.mutex:
            self.unack_messages.append((dest_node_id, packet)) ## resend msg until ack back

    if random.random() <= self.drop_rate: ## simulates random drop, stored in unack_msgs so resend
        return
            
    ## buffer before send(), since not using sync code
    send_time = calculate_send_time(self.delay_time)
    with self.mutex: 
    	self.outgoing_queue.put((send_time, packet, dest_id, dest_ip, dest_port)) 


## TODO -> seems very buggy
def init_membership_list(self, sockets): ## sockets = []
    ports = pick_free_ports(num_processes * (num_processes - 1)) ## os syscall

    ## port_mapping: {(0, 1): (1001, 1002), (1, 2): (1005, 1006), (0, 2): (1003, 1004)}    
    port_mapping = {}
    counter = 0
    for i in range(self.num_processes):
        for j in range(i + 1, self.num_processes):
            port_mapping[(i, j)] = (ports[counter], ports[counter + 1])
            counter = counter + 2
    
    ## membership list    
    backlog = 10    
    for i in range(self.node_id):

    	## socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ## socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) ## UDP ??
        server_sock.bind((socket.gethostname(), port_mapping[(i, id)][1]))
        server_sock.listen(backlog)
        client_sock, (host, client_port) = server_sock.accept()
        sockets.append(client_sock)
    sockets.append(None)

    for i in range(self.node_id + 1, self.num_processes):
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr = socket.gethostname()
        (source_port, destination_port) = port_mapping[(id, i)]
        client_sock.bind((addr, source_port))
        client_sock.connect((addr, destination_port))
        sockets.append(client_sock)
    
    for i in range(self.num_processes): ## set timeouts for sockets
        if i == id:
            continue
        sockets[i].settimeout(0.01)    


#########################################################################################################
#
#
#
#
#
# Global Snapshot Helpers
#########################################################################################################


def save_snapshot_state(pid, snapshot_id, state):
    """state is a tuple of (logical, vector, asset) where logical is an int,
    vector is a list, state is [iphone, money]"""

    logical = state[0]
    vector = " ".join(str(i) for i in state[1])
    asset = state[2]
    content = "id {} : snapshot {} : logical {} : vector {} : money {} : widgets {}\n".format(
        pid, snapshot_id, logical, vector, asset[1], asset[0]
    )

    filename = os.path.dirname(os.path.realpath(__file__)) + "/../../snapshots/snapshot." + str(pid)
    with open(filename, "a") as f: ## append
        f.write(content)


def save_snapshot_channel(pid, snapshot_id, channel, channel_id):
    content = ''
    for entry in channel['data']: ## channel: dict
        type = entry[0]

        asset_type = ''
        if type == 'send_iphone':
            asset_type = 'iphone'
        else:
            asset_type = 'money'

        amount = entry[1]
        logical_timestamp = entry[2]
        vector_timestamp = entry[3:]

        vector_timestamp_str = " ".join(str(i) for i in entry[3:])

        ## message in transit during marker period
        content = content + "id {} : snapshot {} : logical {} : vector {} : message {} to {} : {} {}\n".format(
            pid, snapshot_id, logical_timestamp, vector_timestamp_str, channel_id, pid, asset_type, amount
        )

    snapshot_dir = os.path.dirname(os.path.realpath(__file__)) + "/../../snapshots/"
    filename = snapshot_dir + "snapshot." + str(pid)
    with open(filename, "a") as f:
        f.write(content)



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
