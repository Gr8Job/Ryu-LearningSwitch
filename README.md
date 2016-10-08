# Ryu-LearningSwitch
This SDN Ryu application is intended to fix the behaviour of the simple_switch_13.py sample application.
The simple_switch_13.py application is limited to learn only 1 MAC address per switch interface & hence keep forwarding packets to the controller when connecting multiple hosts to the same port using another switch.
The issue was solved by adding two analysis tables to the switch (one for the source MAC address analysis tolearn the IP/MAC mapping of the source node & the other for the destination MAC address analysis to forward the packet to the correct port). The ethernet farme should be verified versus both tables before being forwrded or sent to the controller (in case of table miss for any of the 2 analysis tables).
