from qcontroly.core.protocol import Frame, FrameParser, build_frame

def test_build_frame_simples():
    # Opcode 0xFE, Payload: b"\x17"
    # Expected: [FE DC BA] [C0] [FF] [LEN=00 04] [SEQ] [FE] [01] [17] [EF]
    out = build_frame(cmd=0xFE, params=b"\x17", seq=0x5A)
    assert out == b"\xfe\xdc\xba\xc0\xff\x00\x04\x5a\xfe\x01\x17\xef"

def test_parser_pacote_completo():
    # RX do H3S: Seq=5A, Cmd=17, Status=00, Params=[01, 04, 00]
    # fe dc ba 00 ff 00 07 00 5a 17 03 01 04 00 ef
    raw = b"\xfe\xdc\xba\x00\xff\x00\x07\x00\x5a\x17\x03\x01\x04\x00\xef"
    out = FrameParser().feed(raw)
    assert len(out) == 1
    assert out[0] == Frame(cmd=0x17, payload=b"\x01\x04\x00", seq=0x5A, status=0x00)

def test_parser_pacotes_em_pedacos():
    raw = b"\xfe\xdc\xba\x00\xff\x00\x07\x00\x5a\x17\x03\x01\x04\x00\xef"
    parser = FrameParser()
    
    # 1 byte por vez
    for b in raw[:-1]:
        assert parser.feed(bytes([b])) == []
    
    # Ultimo byte completa o pacote
    out = parser.feed(bytes([raw[-1]]))
    assert len(out) == 1
    assert out[0].cmd == 0x17

def test_lixo_antes_do_pacote():
    raw = b"LIXO\xfe\xdc\xba\x00\xff\x00\x07\x00\x5a\x17\x03\x01\x04\x00\xef"
    out = FrameParser().feed(raw)
    assert len(out) == 1
    assert out[0].cmd == 0x17

def test_pacote_corrompido():
    # Sem EOF no final
    raw = b"\xfe\xdc\xba\x00\xff\x00\x07\x00\x5a\x17\x03\x01\x04\x00\xEE"
    out = FrameParser().feed(raw)
    assert out == []
