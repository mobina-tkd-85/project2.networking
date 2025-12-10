# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
from collections import deque
import struct
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from time import time, sleep


class Streamer:
    def __init__(self, dst_ip, dst_port,
                 src_ip=INADDR_ANY, src_port=0):
        """Default values listen on all network interfaces, chooses a random source port,
           and does not introduce any simulated packet loss."""
        # socket setups
        self.socket = LossyUDP()
        self.socket.bind((src_ip, src_port))
        # ds setups
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        # recieve setups
        self.sequence_num = 0 # you use it while creating the packets
        self.recv_buffer = {}
        self.expected = 0
        self.last_ack = -1

        # thread setups
        self.closed = False
        self.lock = Lock()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.executor.submit(self.listener) 



    def send(self, data_bytes: bytes) -> None:

        for chunk in self.split_into_chunks(data_bytes):
            packet = self.make_packet("DATA", chunk)

            while True:
                self.socket.sendto(packet, (self.dst_ip, self.dst_port))
                start = time()

                while time() - start < 0.3:
                    with self.lock :
                        print(f"last {self.last_ack} and seq {self.expected}")
                        if self.last_ack == self.sequence_num :
                            self.sequence_num += 1
                            break
                    sleep(0.01)
                else:
                    continue
                    
                break


    def make_packet(self, p_type, payload) :
        t = 1 if p_type == "DATA" else 2
        
        header = struct.pack(("!B H"),t, self.sequence_num)
        return header + payload


    def split_into_chunks(self, payload) :
        max_payload = 1471
        offset = 0
        chunks = []

        while offset < len(payload) :
            data = payload[offset : offset + max_payload]
            offset += max_payload
            chunks.append(data)
        return chunks
            
        


    def recv(self) -> bytes:
        with self.lock:
            if self.expected in self.recv_buffer:
                payload = self.recv_buffer.pop(self.expected)
                self.expected += 1
                return payload



    def listener(self):
        while not self.closed:
            try:
                data, addr = self.socket.recvfrom()
                packet_type, seq, payload = self.parse_packet(data)

                if packet_type == "DATA" :
                    with self.lock :
                        self.recv_buffer[seq] = payload
                        self.send_ack(seq)
                        

                elif packet_type == "ACK":
                    with self.lock :
                        self.last_ack += 1
                        print(f"recieving ack for {self.last_ack}")

            except Exception as e:
                print("listener died :)" + e) 
                break

        
    def send_ack(self, seq) :
        packet = self.make_packet("ACK", b"")
        self.socket.sendto(packet, (self.dst_ip, self.dst_port))



    def parse_packet(self, data) :
        t, seq = struct.unpack("!B H", data[:3])
        payload = data[3:]
        if t == 1:
            return "DATA", seq, payload
        else :
            return "ACK", seq, b""
    
        
                
            
    def close(self) -> None:
        self.closed = True 
        self.socket.stoprecv()
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.
        pass
