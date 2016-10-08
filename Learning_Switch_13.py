######################################
# Description: This application is written to override the 
# one MAC per port limitation found in the simple_switch_13.py sample app
# In a setup of 4 hosts connected to 2 switces, the switches keep sending
# packets to the controller
#
# The main difference is the dependence over 2 tables over the switch to
# check both the source & destination MAC address to stop forwarding the 
# traffic to the controller
#
# Author: Mohammad Mousa
# Date: 8 Oct 2016
########################################


from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

class LearningSwitch13(app_manager.RyuApp):  
    
    # Static Class Members  
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # Constructor Definition
    def __init__(self, *args, **kwargs):
        super(LearningSwitch13, self).__init__(*args, **kwargs)  
        self.mac_to_port = {}                   # create the MAC forwarding table for each object

    # A method initialize the switches to send all traffic to the controller
    # Table 0 for checking Source MAC & table 1 for checking Destination MAC 
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER) 
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, 0, match, actions)
        self.add_flow(datapath, 0, 1, match, actions)


    # A method to build analysis tables when receiving a packet from the switch
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        
        # Create a new table for every switch if not created & log the receiving a packet
        self.mac_to_port.setdefault(dpid, {})
        self.logger.info("packet in event: Switch ID:%s, Input Port:%s, Src MAC:%s, Dst MAC:%s", dpid, in_port, src, dst)

        # Check source MAC versus the Controller MAC address table
        # If doesnt exist ==> update the controller table & both tables of the switch
        if src not in self.mac_to_port[dpid] :
          self.mac_to_port[dpid][src] = in_port
          match = parser.OFPMatch(eth_src=src)
          inst = [parser.OFPInstructionGotoTable(1)]
          mod = parser.OFPFlowMod(datapath=datapath, priority=1, table_id=0, match=match, instructions=inst)
          datapath.send_msg(mod)          


          match = parser.OFPMatch(eth_dst=src)
          actions = [parser.OFPActionOutput(in_port)]
          self.add_flow(datapath, 1, 1, match, actions)


        # Forward the packet based on MAC table or flood
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD        
        actions = [parser.OFPActionOutput(out_port)]
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)



    # A Method used to add an entry to the flow table of the switch
    def add_flow(self, datapath, priority, table_id, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, table_id=table_id, match=match, instructions=inst)
        datapath.send_msg(mod)