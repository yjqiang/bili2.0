from enum import IntEnum
from struct import Struct
from typing import Tuple, Iterator


class Header:
    pack_size = 4
    header_size = 2
    ver_size = 2
    operation_size = 4
    seq_id_size = 4

    # header_struct.size == raw_header_size
    header_struct = Struct('>I2H2I')
    raw_header_size = pack_size + header_size + ver_size + operation_size + seq_id_size

    @staticmethod
    def pack(len_pack: int, len_header: int, ver: int, opt: int, seq: int) -> bytes:
        if len_header == Header.raw_header_size:
            return Header.header_struct.pack(len_pack, len_header, ver, opt, seq)
        raise ValueError('len_header != Header.raw_header_size')

    @staticmethod
    def unpack(header: bytes) -> Tuple[int, int, int, int, int]:
        len_pack, len_header, ver, opt, seq = Header.header_struct.unpack_from(header)
        if len_header == Header.raw_header_size:
            return len_pack, len_header, ver, opt, seq
        raise ValueError('len_header != Header.raw_header_size')


class Pack:
    @staticmethod
    def pack(str_body: str, ver: int, opt: int, seq: int) -> bytes:
        body = str_body.encode('utf-8')
        len_header = Header.raw_header_size
        len_pack = len(body) + len_header
        header = Header.pack(len_pack, len_header, ver, opt, seq)
        return header + body

    @staticmethod
    def unpack(packs: bytes) -> Iterator[Tuple[int, bytes]]:
        pack_l = 0
        len_packs = len(packs)
        while pack_l != len_packs:
            len_pack, _, _, opt, _ = Header.unpack(packs[pack_l:pack_l+Header.raw_header_size])
            next_pack_l = pack_l + len_pack
            body = packs[pack_l + Header.raw_header_size:next_pack_l]
            yield opt, body
            pack_l = next_pack_l


class Opt(IntEnum):
    HANDSHAKE = 0
    HANDSHAKE_REPLY = 1

    HEARTBEAT = 2
    HEARTBEAT_REPLY = 3

    SEND_MSG = 4
    SEND_MSG_REPLY = 5

    DISCONNECT_REPLY = 6

    AUTH = 7
    AUTH_REPLY = 8

    RAW = 9

    PROTO_READY = 10
    PROTO_FINISH = 11

    CHANGE_ROOM = 12
    CHANGE_ROOM_REPLY = 13

    REGISTER = 14
    REGISTER_REPLY = 15

    UNREGISTER = 16
    UNREGISTER_REPLY = 17

    # B站业务自定义OP
    # MinBusinessOp = 1000
    # MaxBusinessOp = 10000
