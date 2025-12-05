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
        max_payload = 1471
        offset = 0

        while offset < len(data_bytes):
            chunk = data_bytes[offset : offset + max_payload]
            offset += max_payload

            # 2-byte header for seq
            header = struct.pack("!H", self.sequence_num)
            packet = header + chunk

            self.socket.sendto(packet, (self.dst_ip, self.dst_port))

            # increment sequence number
            self.sequence_num += 1
            if self.sequence_num > 1000:
                self.sequence_num = 0  # wrap around



    def recv(self) -> bytes:
        packet, addr = self.socket.recvfrom(2048)

        # unpack 2-byte sequence number
        seq, = struct.unpack("!H", packet[:2])
        payload = packet[2:]

        # initialize buffer & expected in __init__ if not already
        if not hasattr(self, 'recv_buffer'):
            self.recv_buffer = {}
            self.expected = 0

        # in-order packet
        if seq == self.expected:
            self.expected += 1
            result = payload

            # flush any buffered packets
            while self.expected in self.recv_buffer:
                result += self.recv_buffer.pop(self.expected)
                self.expected += 1
            return result

        # out-of-order
        elif seq > self.expected:
            self.recv_buffer[seq] = payload
            return b""  # nothing ready

        # duplicate / old packet
        else:
            return b""


            
                
            
    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.
        pass
