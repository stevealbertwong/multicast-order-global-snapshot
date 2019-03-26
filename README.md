# Distributed in memory K/V storage service that supports multicast ordering and global snapshot



## architecture
- simulates DS with python multi-process running on same machine
	- process uses sockets to communicate with each other
	- IP: same machine, port: node ID

- synchronization
	- python multi-threaded handlers 