
config = {
    'hosts': [ ## hosts is a list of (IP address, port)
        ('localhost', 0000),
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
    'drop_rate' : 0.2,
    "tcp_ip" : "127.0.0.1",
	"total_clients" : [0000,6666,7777,8888],
	"num_processes" : 4,
	"1" : {
		"tcp_port" : 0000
	},
	"2" : {
		"tcp_port" : 6666
	},
	"3" : {
		"tcp_port" : 7777
	},
	"4" : {
		"tcp_port" : 8888
	},
	"reverse_dict" :{
		"8888": {
			"proc_id" : "4"
		},
		"7777": {
			"proc_id" : "3"
		},
		"6666": {
			"proc_id" : "2"
		},
		"0000": {
			"proc_id" : "1"
		}
	}
}

