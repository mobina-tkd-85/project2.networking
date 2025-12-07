# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
from collections import deque
import struct
from concurrent.futures import ThreadPoolExecutor
from threading import lock


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
        self.recv_buffer = {}
        self.expected = 0
        self.closed = False
        self.last_ack = -1
        self.lock = lock()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.executor.submit(self.listener) 



    def send(self, data_bytes: bytes) -> None:

        for chunk in self.split_into_chunks(data_bytes):
            packet = self.make_packet("DATA", self.sequence_num)

            while True:
                self.socket.sendto(packet, (self.dst_ip, self.dst_port))
                start = time()

                while time() - start < 0.3:
                    with self.lock :
                        if self.last_ack == self.sequence_num :
                            self.sequence_num += 1
                            break
                    sleep(0.01)
                # this else runs just when the loop did not break
                else:
                    continue
                    
                break

        # intil modify recv()





        
        
        # you need to add a packet type later
        header = struct.pack("!H", self.sequence_num)
        packet = header + data
        self.socket.sendto(packet, (self.dst_ip, self.dst_port))
        self.sequence_num += 1

        



    def split_into_chunks(self, payload) :
        max_payload = 1471
        offset = 0
        chunks = []

        while offset < len(data_bytes) :
            data = data_bytes[offset : offset + max_payload]
            offset += max_payload
            chunks.append(data)
            
        


    def recv(self) -> bytes:
        with self.lock:
            if self.sequence_num in self.recv_buffer:
                payload = self.recv_buffer.pop(sequence_num)
                self.expected += 1
                return payload



    def listener(self):
        while not self.closed:
            try:
                data, addr = self.socket.recvfrom()
                packet_type, sequence_num, payload = self.parse_packet(data)

                if packet_type == "DATA" :
                    with self.lock :
                        self.recv_buffer[sequence_num] = payload
                elif packet_type == "ACK":
                    with self.lock :
                        self.last_ack = sequence_num
            except Exception as e:
                print("listener died :)" + e) 
                break

    def parse_packet(self, data) :
        seq, = struct.unpack("!H H", data[:2], data[2:4])
        payload = data[4:]
        
            
                
            
    def close(self) -> None:
        self.closed = True 
        self.socket.stoprecv()
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.
        pass
