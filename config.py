
config = {
    'hosts': [ ## hosts is a list of (IP address, port)
        ('localhost', 16400),
        ('localhost', 16401),
        ('localhost', 16402),
        ('localhost', 16403),
        ('localhost', 16404),
        ('localhost', 16405),
    ],
    'multicast_order': 'casual', ## either 'casual' or 'total'
    'num_processes': 5,
    'num_snapshots' : 3,
    'sequencer_id' : 1,
    'starting_money' : 100000,
    'starting_iphone' : 100,    
    'message_max_size' : 2048,
    'delay_time' : 10,
    'drop_rate' : 0.2

}

