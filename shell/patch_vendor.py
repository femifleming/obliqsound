#!/usr/bin/env python3
"""Rename the manufacturer the Cabbage shell reports to hosts (it was built as 'AudioFB') to 'Obliq'.

The name is compiled in several ways, all patched in place (same byte lengths):
- 8-byte 'AudioFB\\0' constants (x86_64 immediates, arm64 literal pools, the VST2 vendor field);
- a merged arm64 literal 'AudioFBS1000284' whose first 7 bytes are read as the name;
- x86_64 code that builds 'AudioFBS' + 'ynth';
- arm64 code that builds the name from instruction immediates: 'Au' 'di' (movk), 'oF' (movz + strh), 'B' (movz + strb).
Only 7 characters fit, so the vendor reads 'Obliq'.
usage: patch_vendor.py <binary>
"""
import struct, sys

p = sys.argv[1]
b = bytearray(open(p, 'rb').read())

def replace_all(old, new):
    global b
    assert len(old) == len(new)
    n = b.count(old)
    b = bytearray(bytes(b).replace(old, new))
    return n

replace_all(b'AudioFB\x00', b'Obliq\x00\x00\x00')
replace_all(b'AudioFBS1000284', b'Obliq\x00\x00S1000284')
replace_all(b'H\xbaAudioFBS', b'H\xbaObliq\x00\x00\x00')

def imm(w):
    return (w >> 5) & 0xffff

def set_imm(w, v):
    return (w & ~(0xffff << 5)) | (v << 5)

MOVZ, MOVK = 0x52800000, 0x72800000
patched = 0
for off in range(0, len(b) - 32, 4):
    w0, w1 = struct.unpack_from('<II', b, off)
    if (w0 & 0x7f800000) == MOVK and imm(w0) == 0x7541 and (w0 >> 21) & 3 == 2 \
            and (w1 & 0x7f800000) == MOVK and imm(w1) == 0x6964 and (w1 >> 21) & 3 == 3 and (w0 & 31) == (w1 & 31):
        struct.pack_into('<I', b, off, set_imm(w0, 0x624f))        # 'Ob'
        struct.pack_into('<I', b, off + 4, set_imm(w1, 0x696c))    # 'li'
        for k in range(2, 8):                                      # the 'oF' and 'B' that follow
            w = struct.unpack_from('<I', b, off + 4 * k)[0]
            if (w & 0x7f800000) == MOVZ and imm(w) == 0x466f:
                struct.pack_into('<I', b, off + 4 * k, set_imm(w, 0x0071))    # 'q\0'
            elif (w & 0x7f800000) == MOVZ and imm(w) == 0x42:
                struct.pack_into('<I', b, off + 4 * k, set_imm(w, 0x0000))    # '\0'
        patched += 1

if b'AudioFB' in b or patched == 0:
    print('patch_vendor: some vendor bytes left as they were (the host-visible ones are changed)')
open(p, 'wb').write(b)
