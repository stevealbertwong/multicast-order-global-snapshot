#########################################################################################################
#
#
#
#
#
# Protocol definition
# 
#########################################################################################################

## packet's fields
SENDER_NODE_ID = 0
MESSSAGE_ID = 1 ## tgt with sender ID -> detects duplicates
MESSAGE_TYPE = 2 ## data, marker, ack, sequencer etc
MULTICAST_ORDER = 3 ## total, causal
LOGICAL_TIMESTAMP = 4 
VECTOR_TIMESTAMP = 5
VECTOR_SEQ_NO = 6
PAYLOAD = 7 ## seq msg, data msg -> different
IF_SEQUENCER_MSG = 8 ## total ordering
SNAPSHOT_ID = 9 ## global snapshot

## message type
SEND_MONEY = 0
SEND_IPHONE = 1
ACK = 2
MARKER = 3 ## global snapshot

MONEY = 0
IPHONE = 1

## ordering type
CAUSAL = 0
TOTAL = 1



