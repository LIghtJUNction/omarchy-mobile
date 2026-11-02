#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate one OpenSSH public key before packing it into a probe."""
import base64
from pathlib import Path
import struct
import sys


def validate(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(32769)
    if len(raw) > 32768 or len(raw.splitlines()) != 1:
        raise ValueError('expected one public key')
    fields = raw.decode('utf-8').split()
    if len(fields) < 2 or fields[0] not in ('ssh-ed25519', 'ssh-rsa', 'ecdsa-sha2-nistp256'):
        raise ValueError('expected an OpenSSH public key, never a private key')
    wire = base64.b64decode(fields[1], validate=True)
    offset = 0

    def string():
        nonlocal offset
        if len(wire) - offset < 4:
            raise ValueError('truncated public-key payload')
        size, = struct.unpack_from('>I', wire, offset)
        offset += 4
        if size > len(wire) - offset:
            raise ValueError('truncated public-key field')
        result = wire[offset:offset + size]
        offset += size
        return result

    valid = string().decode('ascii') == fields[0]
    if fields[0] == 'ssh-ed25519':
        valid &= len(string()) == 32
    elif fields[0] == 'ssh-rsa':
        valid &= bool(string()) and bool(string())
    else:
        curve, point = string(), string()
        valid &= curve == b'nistp256' and len(point) == 65 and point[:1] == b'\x04'
    if not valid or offset != len(wire):
        raise ValueError('invalid public-key payload')


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('usage: ssh-public-key.py PUBLIC_KEY')
        validate(sys.argv[1])
    except (ValueError, OSError, struct.error, UnicodeError) as error:
        sys.exit(str(error))
