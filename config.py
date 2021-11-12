
config = {
    'hosts': [ ## hosts is a list of (IP address, port)
        ('localhost', 5555),
        ('localhost', 6666),
        ('localhost', 7777),
        ('localhost', 8888),
    ],
    'multicast_order': 'casual', ## either 'casual' or 'total'
    'num_processes': 4,
    'num_snapshots' : 3,
    'sequencer_id' : 1,
    'starting_money' : 100000,
    'starting_iphone' : 100,    
    'message_max_size' : 2048,
    'delay_time' : 10,
    'drop_rate' : 0.2
}

