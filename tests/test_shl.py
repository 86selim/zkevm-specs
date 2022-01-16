import secrets

from zkevm_specs.encoding import u256_to_u8s, U256, u8s_to_u64s, U8
from zkevm_specs.opcode.shl import check_shl, BitslevelTable, Pow64Table


def gen_shl_witness(a, shift):
    b = a << shift
    a8s = u256_to_u8s(U256(a))
    b8s = u256_to_u8s(U256(b))
    shift_div_by_64 = shift // 64
    shift_mod_by_64_div_by_8 = shift % 64 // 8
    shift_mod_by_64 = shift % 64
    shift_mod_by_64_pow = 1 << shift_mod_by_64
    shift_mod_by_64_decpow = (1 << 64) // shift_mod_by_64_pow
    shift_mod_by_8 = shift % 8
    a64s = u8s_to_u64s(a8s)
    a_slice_front = [U8(0)] * 32
    a_slice_back = [U8(0)] * 32
    for virtual_idx in range(0, 4):
        if shift_mod_by_64 == 0:
            slice_back = a64s[virtual_idx]
            slice_front = 0
        else:
            slice_back = a64s[virtual_idx] % (1 << (64 - shift_mod_by_64))
            slice_front = a64s[virtual_idx] // (1 << (64 - shift_mod_by_64))
        for idx in range(0, 8):
            now_idx = virtual_idx * 8 + idx
            a_slice_back[now_idx] = U8(slice_back % (1 << 8))
            a_slice_front[now_idx] = U8(slice_front % (1 << 8))
            slice_back = slice_back >> 8
            slice_front = slice_front >> 8
    return (
        b8s,
        a_slice_front,
        a_slice_back,
        shift_div_by_64,
        shift_mod_by_64_decpow,
        shift_mod_by_64_div_by_8,
        shift_mod_by_64_pow,
        shift_mod_by_8,
    )


def test_shl():
    a = secrets.randbelow(2 ** 256)
    bits_level_table = BitslevelTable()
    pow64_table = Pow64Table()
    a_bits = len(bin(a)) - 2
    shift = [U8(0)] * 32
    shift[0] = U8(secrets.randbelow(256))
    (
        b,
        a_slice_front,
        a_slice_back,
        shift_div_by_64,
        shift_mod_by_64_decpow,
        shift_mod_by_64_div_by_8,
        shift_mod_by_64_pow,
        shift_mod_by_8
    ) = gen_shl_witness(a, shift[0])
    check_shl(
        u256_to_u8s(U256(a)),
        b,
        shift,
        a_slice_front,
        a_slice_back,
        shift_div_by_64,
        shift_mod_by_64_decpow,
        shift_mod_by_64_div_by_8,
        shift_mod_by_64_pow,
        shift_mod_by_8,
        bits_level_table,
        pow64_table)