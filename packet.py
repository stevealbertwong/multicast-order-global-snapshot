# 
# 
# 
# packet = queue.get()
# if (packet.getPacketType()=="snapshot")
# 
# 
# 
# msg_types: 
# 1. send_money
# 2. send_iphone
# 3. marker (snapshot)
# 4. sequencer_msg (total ordering)
# 5. ack (reliable)
# 
# TODO: 
# - retrieve_snapshot 
#

import json


class Packet:
	def __init__(self, sender_id, receiver_id, msg_type, 
			msg_id = None, key = None, value = None, vector_timestamp = None, seq_no = None, snapshot_id = None):    
    	
		## every msg must have
		self.sender_id = sender_id
		self.receiver_id = receiver_id # each ps already has each other's socket
		self.msg_type = msg_type

		## specific to 1 type of msg
		self.msg_id = msg_id
		self.key = key
		self.value = value	
		self.vector_timestamp = vector_timestamp
		self.seq_no = seq_no # total ordering
		self.snapshot_id = snapshot_id # identify marker msg id

	
	## class -> string 
	## https://stackoverflow.com/questions/4932438/how-to-create-a-custom-string-representation-for-a-class-object 
	def __str__(self):
		return '::'.join([str(i) for i in self.vector_timestamp])

	# necessary ?? 
	def get_dest_node_id(self):
		return self.dest_node_id
	def get_msg_id(self):
		return self.msg_id	
	def get_msg_type(self):
		return self.msg_type
	def getSenderInfo(self):
		return self.senderInfo

  	## marker msg for global snapshot 
	def engineer_packet(payload_fields):
    # packet = json.dumps({'id': client_id, 'type': 'marker','msg': initiator_id})
    # packet = pickle.dumps(Packet("QUIT",0,0,self.name)
		# '::'.join([str(x) for x in [self.sequence_counter, sender, message_id]])
		return ('::'.join([str(x) for x in payload_fields])).encode('utf-8')



	# def parse_packet(payload):

    # # payload = self.client_socket.recv(1024)
    # # payload_pickle = pickle.loads(payload)
    # # payload_pickle.getPacketType()=="snapshot"


    # # payload_json = json.loads(payload) 
    # # sender_id = json_payload['sender_id']
    # # msg_type = json_payload['type']


	# 	message = payload.decode('utf-8')
	# 	sender_id, message_id, message_type, multicast_order, logical_timestamp, vector_timestamp, vector_seq_no, payload = message.split('::', 8)



  