from __future__ import annotations
from dataclasses import dataclass
import struct

class ProtocolError(Exception):
    pass

@dataclass
class Frame:
    cmd: int
    payload: bytes
    seq: int = 0
    status: int = 0


# Protocolo H3S (Serviço a002)
# TX: [FE DC BA] [C0] [FF] [LEN_16] [SEQ] [CMD] [PARAM_LEN] [PARAMS] [EF]
# RX: [FE DC BA] [00] [FF] [LEN_16] [STATUS] [SEQ] [CMD] [PARAM_LEN] [PARAMS] [EF]

def build_frame(cmd: int, params: bytes, seq: int = 0, flags: int = 0xC0, cls: int = 0xFF) -> bytes:
    """Monta um pacote no formato H3S."""
    # O payload real para TX é: [SEQ] [CMD] [PARAM_LEN] [PARAMS]
    param_len = len(params)
    inner_payload = bytes([seq, cmd, param_len]) + params
    
    # Len é big endian (2 bytes)
    length = len(inner_payload)
    len_bytes = struct.pack(">H", length)
    
    # Montagem final
    frame = b"\xFE\xDC\xBA" + bytes([flags, cls]) + len_bytes + inner_payload + b"\xEF"
    return frame


class FrameParser:
    """Decodificador de streaming para o protocolo H3S."""
    
    def __init__(self):
        self.buffer = bytearray()
        
    def feed(self, data: bytes) -> list[Frame]:
        self.buffer.extend(data)
        frames = []
        
        while True:
            # Procurar assinatura mágica
            idx = self.buffer.find(b"\xFE\xDC\xBA")
            if idx == -1:
                # Manter os últimos 2 bytes caso seja uma assinatura parcial
                if len(self.buffer) > 2:
                    self.buffer = self.buffer[-2:]
                break
                
            # Descartar lixo antes da assinatura
            if idx > 0:
                self.buffer = self.buffer[idx:]
                
            # Tamanho mínimo: 3(Magic)+1(Flags)+1(Cls)+2(Len)+1(Status)+1(Seq)+1(Cmd)+1(PLen)+1(EOF) = 11 bytes
            if len(self.buffer) < 7:
                break
                
            # Ler length (big endian)
            payload_len = struct.unpack(">H", self.buffer[5:7])[0]
            
            # O tamanho total do pacote = 7 bytes header + payload_len + 1 byte EOF
            total_len = 7 + payload_len + 1
            
            if len(self.buffer) < total_len:
                break
                
            # Pacote completo!
            packet = self.buffer[:total_len]
            self.buffer = self.buffer[total_len:]
            
            flags = packet[3]
            cls = packet[4]
            inner_payload = packet[7:-1]
            eof = packet[-1]
            
            if eof != 0xEF:
                # Pacote corrompido, procurar próxima assinatura
                continue
                
            # Tratamento RX normal (Device -> App, flags == 0x00)
            if flags == 0x00 and len(inner_payload) >= 4:
                status = inner_payload[0]
                seq = inner_payload[1]
                cmd = inner_payload[2]
                param_len = inner_payload[3]
                params = inner_payload[4:4+param_len]
                frames.append(Frame(cmd=cmd, payload=params, seq=seq, status=status))
            # Tratamento RX espelho/eco (TX echo, flags == 0xC0, raro mas pode acontecer no Wireshark)
            elif flags == 0xC0 and len(inner_payload) >= 3:
                seq = inner_payload[0]
                cmd = inner_payload[1]
                param_len = inner_payload[2]
                params = inner_payload[3:3+param_len]
                frames.append(Frame(cmd=cmd, payload=params, seq=seq))
            else:
                # Pacote genérico que não encaixa (ex: 03, C1, etc)
                if len(inner_payload) >= 2:
                    # Chute de segurança
                    frames.append(Frame(cmd=inner_payload[1], payload=inner_payload[2:], seq=inner_payload[0]))

        return frames

    def reset(self):
        self.buffer.clear()
