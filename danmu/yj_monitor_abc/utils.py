from struct import Struct
from typing import Tuple, Iterator


class Header:
    body_size = 4

    # header_struct.size == raw_header_size
    header_struct = Struct('>I')
    raw_header_size = body_size

    @staticmethod
    def pack(len_body: int) -> bytes:
        return Header.header_struct.pack(len_body)

    @staticmethod
    def unpack(header: bytes) -> Tuple[int]:
        len_body,  = Header.header_struct.unpack_from(header)
        return len_body,


class Pack:
    @staticmethod
    def pack(str_body: str) -> bytes:
        body = str_body.encode('utf-8')
        len_body = len(body)
        header = Header.pack(len_body)
        return header + body

    @staticmethod
    def unpack(packs: bytes) -> Iterator[Tuple[int, bytes]]:
        raise ValueError('NOT SUPPORTED')
