
#########################################################################################################
#
# multicast ordering
# - timestamp (causal)
# - acks (reliable)
# - 2 threads receiving 2 types of packets 
# - engineer packets
#
# multicast vs vector clock
# - multicast == use buffer to maintain vector clock ordering when packets will arrive at unpredictable order 
# - EXCEPT:
# - vector clock 
#   - local instruction, send and received msg -> increases counter 
# - multicast
#   - for sender -> ONLY send msg increases counter 
#   - for receiver -> ONLY receive msg increases counter 
#   - local instruction does NOT increase counter
# 
# global snapshot
# - 
# - 
# - 
# 
# simulation 
# - 1 central sequencer ps spawns 1 new simulation thread + user input thread ?? 
# - 1 extra ps ?? 
# - 
# 
# 
# there shd be a new thread everytime there is something blocking e.g. socket send / recv, acquire_lock 
# 
# 1. struct 
# 2. packet fields (input)
# 3. handler (algo)
# 4. multithread architecture
#    - whenever blocking function
#    - socket send/recv()
#    - waiting for lock 
#    - for loop but loop many times e.g. causal ordering logic 
#    - while true timer loop
# 
# TODO:
# 1. [] vs queue vs priority queue ??
# 2. all data struct to dict ?? 
# 
# 
# 
#
#
# Networking Helpers
#########################################################################################################

'''
Check that send happens only when account balance >=1
On first marker receive , process state save
Set flags for all  channels and on receive
if flag is set, save the state of channel
On receive a marker if flag is set for that channel
close the channel, reset flag to false.
Save channel state on marker receive

See if you can break out of infinite while loop or close the thread
after connections are complete.

channel_state = {
    '2' : {
    'flag': True|False
    'state': []
    },
    '3' : {
    'flag': True|False
    'state': []
    }
}

Problem:
1. When receiving two markers from two different processes in quick succession, 
the global variable is over-ridden, so the first marker is not being processed.
2. While saving state, how to handle other messages received on the same channel.
'''
