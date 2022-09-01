import struct
import sys
import io



bchr = chr
if sys.version > '3':
    bchr = lambda x: bytes([x])


def ser_str(s):
    if len(s) < 253: return bchr(len(s)) + s
    elif len(s) < 254: return bchr(253) + struct.pack(b"<H", len(s)) + s
    elif len(s) < 255: return bchr(254) + struct.pack(b"<I", len(s)) + s
    return bchr(255) + struct.pack(b"<Q", len(s)) + s


def deser_str(f):
    nit = struct.unpack(b"<B", f.read(1))[0]
    if nit == 253:
        nit = struct.unpack(b"<H", f.read(2))[0]
    elif nit == 254:
        nit = struct.unpack(b"<I", f.read(4))[0]
    elif nit == 255:
        nit = struct.unpack(b"<Q", f.read(8))[0]
    return f.read(nit)