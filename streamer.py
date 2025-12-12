# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
from collections import deque
import struct
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from time import time, sleep
import hashlib


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

        # fin setups
        self.fin_send = False
        self.fin_ack_received = False
        self.fin_received = False

        # thread setups
        self.closed = False
        self.lock = Lock()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.executor.submit(self.listener) 





    def send(self, data_bytes: bytes) -> None:

        for chunk in self.split_into_chunks(data_bytes):
            digest = hashlib.md5(chunk).digest()
            packet = self.make_packet("DATA", self.sequence_num, digest, chunk)

            while True:
                self.socket.sendto(packet, (self.dst_ip, self.dst_port))
                start = time()

                while time() - start < 0.3:
                    with self.lock :
                        print(f"last {self.last_ack} and seq {self.sequence_num}")
                        if self.last_ack == self.sequence_num :
                            self.sequence_num += 1
                            break
                    sleep(0.01)
                else:
                    continue
                    
                break


    def make_packet(self, p_type, seq, digest, payload) :
        if p_type == "DATA":
            t = 1
        elif p_type == "ACK":
            t = 2
        elif p_type == "FIN":
            t = 3 
        elif p_type == "FIN_ACK":
            t = 4 
        
        header = struct.pack(("!B H"),t, seq)
        return header + digest + payload


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
                packet_type, seq, digest, payload = self.parse_packet(data)


                

                if packet_type == "DATA" :
                    calc_md5 = hashlib.md5(payload).digest()
                    if calc_md5 != digest:
                        print("Coruption accured")
                        continue

                    with self.lock :
                        self.recv_buffer[seq] = payload
                        self.send_ack(seq)
                        

                elif packet_type == "ACK":
                    with self.lock :
                        self.last_ack += 1
                        print(f"recieving ack for {self.last_ack} + {self.sequence_num}")

                elif packet_type == "FIN":
                    with self.lock :
                        self.fin_received = True
                        self.send_fin_ack(self.sequence_num)

                elif packet_type == "FIN_ACK":
                    with self.lock :
                        self.fin_ack_received = True
                    # i suppose you can close the connection

                else :
                    print("unknown packet type")


            except Exception as e:
                print("listener died :)" + e) 
                break

        
    def send_ack(self, seq) :
        packet = self.make_packet("ACK", seq,b"", b"")
        self.socket.sendto(packet, (self.dst_ip, self.dst_port))

    def send_fin_ack(self, seq) :
        packet = self.make_packet("FIN_ACK", seq,b"", b"")
        self.socket.sendto(packet, (self.dst_ip, self.dst_port))



    def parse_packet(self, data) :
        t, seq = struct.unpack("!B H", data[:3])
        if t == 1:
            digest = data[3:19]
            payload = data[19:]
            return "DATA", seq, digest, payload
        elif t == 2 :
            return "ACK", seq, None, None
        elif t == 3 :
            return "FIN", seq, None, None
        elif t == 4 :
            return "FIN_ACK", seq, None, None
        else :
            return "Unknown", None, None, None
            print(f"Unknown type...{t}")
    
        
    
        
                
            
    def close(self) -> None:

        while self.last_ack + 1 != self.sequence_num:
            print("all packets arrived till now..........")
            sleep(0.01) 

        fin_packet = self.make_packet("FIN", self.sequence_num + 1, b"", b"")


        while not self.fin_ack_received :
            self.socket.sendto(fin_packet, (self.dst_ip, self.dst_port))
            start = time() 

            while time() - start < 0.25 :
                if self.fin_ack_received :
                    break
                sleep(0.01)

        while not self.fin_received :
            sleep(0.01)

         
        sleep(2)

        self.closed = True
        self.socket.stoprecv()
                    


        
