# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
from collections import deque
import struct


class Streamer:
    def __init__(self, dst_ip, dst_port,
                 src_ip=INADDR_ANY, src_port=0):
        """Default values listen on all network interfaces, chooses a random source port,
           and does not introduce any simulated packet loss."""
        self.socket = LossyUDP()
        self.socket.bind((src_ip, src_port))
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.sequence_num = 0
        self.buff = {}
        self.expected = 0


    def send(self, data_bytes: bytes) -> None:
        data_string = data_bytes.decode('utf-8')
        self.buff = ''
        splited_data = data_string.split(" ")
        for i in splited_data:
            if(len(self.buff) + len(i) < 1471) :
                self.buff += i + " "
            else : 
                data_bytes = self.buff.encode('utf-8')
                header = struct.pack("!B", self.sequence_num)
                packet = header + data_bytes
                self.sequence_num += 1
                self.socket.sendto(packet, (self.dst_ip, self.dst_port))
                self.buff = i + " "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
        data_bytes = self.buff.encode('utf-8')
        header = struct.pack("!B", self.sequence_num)
        packet = header + data_bytes
        self.sequence_num += 1
        self.socket.sendto(packet, (self.dst_ip, self.dst_port))



    def recv(self) -> bytes:
        
        packet, addr = self.socket.recvfrom()
        sequence_num = packet[0]
        data = packet[1:]
        if sequence_num == self.expected :
            self.expected += 1
            return data
        
        else :
            self.buff[sequence_num] = data

        while self.expected in self.buff:
            data = self.buff.pop(self.expected)
            self.expected += 1
            print("2")
            return data
        
        

        
            
        
    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.
        pass
