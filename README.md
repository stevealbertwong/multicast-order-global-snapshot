# GSMOServer (Global Snapshot Multicast Ordering)

Distributed in memory K/V storage service that supports multicast ordering and global snapshot


## what is this distributed server used for
- whenever multicast/broadcast involving multiple packets or peers
	- logical ordering packets sequence
	- distributedly save/snapshot process state as logs

## DS architecture
- simulates DS with python multi-process running on same machine
	- process uses sockets to communicate with each other
	- IP: same machine, port: node ID

- synchronization
	- python multi-threaded handlers 
	- should not be race condition since single threaded message handler

## Global Snapshot


- updates global snapshot channels when total or causal deliver() 
	- i.e. deliver() -> updates channels + KV data list




## Mulitcast Ordering 


### Causal Ordering 



### Total Ordering 





## Reference:

- UIUC cloud class
	- https://courses.engr.illinois.edu/cs425/fa2017/lectures.html 

- https://www.youtube.com/watch?v=x0VYs3n2YR4 - Natarajan Meghanathan, Jackson State University
	- http://www.jsums.edu/compscience/dr-natarajan-meghanathan/

- https://www.youtube.com/watch?v=_t1nyGjPMNc - simulation 
	- https://github.com/jonanh/PanChat 

- https://www.youtube.com/watch?v=ao58xine3jM - Microsoft Research 

The presentation slide and the complete schedule of Dr. TLA+ Series are available at https://github.com/tlaplus/DrTLAPlus. 

A snapshot of the state of a running program is useful in several ways. For example, it can serve as a check point from which to restart the execution, in case the rest of the execution fails in some way. Another example use of a snapshot is to detect that some stable condition, such as a deadlock, has occurred. 

This lecture will discuss algorithms for capturing a global snapshot of a distributed, asynchronous system. It will focus on writing a formal specification of such algorithms. 

Chapter 10, Parallel Program Design, by K. M. Chandy and J. Misra (Addison-Wesley, 1988) - "Distributed Snapshots: Determining Global States of Distributed Systems", K. M. Chandy and L. Lamport, ACM TOCS, 3:1 (1985) - "The Distributed Snapshot of K. M. Chandy and L. Lamport", in Control Flow and Data Flow, ed. M. Broy (Springer, 1985), a version of which is found as EWD 864



## TODO
- this is first draft have not tested yet
- unit testing
- error handling