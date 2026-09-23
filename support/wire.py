"""Bounded binary RPC envelope for the opt-in Omerta private client.

The game's own serialized gameplay payloads remain opaque bytes.
This is a new protocol, NOT an implementation of the official login service.
"""
import struct

MAX_FRAME = 8 * 1024 * 1024
MAX_ITEMS = 20000
MAX_DEPTH = 24


def encode(value, depth=0):
    if depth > MAX_DEPTH:
        raise ValueError('nesting limit')
    if value is None:
        return b'z'
    if value is False:
        return b'f'
    if value is True:
        return b't'
    if isinstance(value, int):
        data = str(value).encode('ascii')
        return b'n' + struct.pack('>I', len(data)) + data
    if isinstance(value, str):
        value = value.encode('utf-8')
    if isinstance(value, bytes):
        if len(value) > MAX_FRAME:
            raise ValueError('string limit')
        return b's' + struct.pack('>I', len(value)) + value
    if isinstance(value, (list, tuple)):
        value = dict(enumerate(value, 1))
    if isinstance(value, dict):
        if len(value) > MAX_ITEMS:
            raise ValueError('table limit')
        return b'm' + struct.pack('>I', len(value)) + b''.join(
            encode(k, depth + 1) + encode(v, depth + 1) for k, v in value.items())
    raise ValueError('unsupported value type')


def decode(data):
    offset = 0
    budget = MAX_ITEMS * 2

    def take(count):
        nonlocal offset
        if count < 0 or offset + count > len(data):
            raise ValueError('truncated value')
        result = data[offset:offset + count]
        offset += count
        return result

    def value(depth=0):
        nonlocal budget
        budget -= 1
        if depth > MAX_DEPTH or budget < 0:
            raise ValueError('complexity limit')
        tag = take(1)
        if tag == b'z':
            return None
        if tag == b'f':
            return False
        if tag == b't':
            return True
        if tag in (b'n', b's'):
            size = struct.unpack('>I', take(4))[0]
            if size > MAX_FRAME or (tag == b'n' and size > 12):
                raise ValueError('value size limit')
            raw = take(size)
            return int(raw) if tag == b'n' else raw
        if tag == b'm':
            count = struct.unpack('>I', take(4))[0]
            if count > MAX_ITEMS:
                raise ValueError('table limit')
            result = {}
            for _ in range(count):
                key = value(depth + 1)
                if not isinstance(key, (bytes, int)) or isinstance(key, bool):
                    raise ValueError('invalid table key')
                if key in result:
                    raise ValueError('duplicate table key')
                result[key] = value(depth + 1)
            return result
        raise ValueError('unknown tag')

    result = value()
    if offset != len(data):
        raise ValueError('trailing data')
    return result


def rpc_packet(name, *args):
    body = encode({b'n': len(args) + 1, 1: name,
                   **{i + 2: arg for i, arg in enumerate(args)}})
    if len(body) > MAX_FRAME:
        raise ValueError('frame limit')
    return struct.pack('>I', len(body)) + body


def unpack_rpc(body):
    packet = decode(body)
    if not isinstance(packet, dict):
        raise ValueError('expected RPC table')
    count = packet.get(b'n')
    if type(count) is not int or not 1 <= count <= 32:
        raise ValueError('argument count')
    name = packet.get(1)
    if not isinstance(name, bytes) or len(name) > 80:
        raise ValueError('RPC name')
    return name.decode('ascii'), [packet.get(i) for i in range(2, count + 1)]
