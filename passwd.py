import os

def generate():
    # generate a password of 8 characters from a set of 64 ascii characters
    lower = 'abcdefghijkmnopqrstuvwxyz'
    upper = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
    digits = '234567923456789'
    chars = ''.join([lower, upper, digits])
    assert len(chars) == 1<<6 # 6 bits
    while 1:
        r = os.urandom(3)
        p = []
        has_lower = has_upper = has_digits = has_symbols = False
        for pos in range(0, 23, 6):
            i, s = divmod(pos, 8)
            x = ord(r[i]) >> s
            if s > 2:
                x += ord(r[i+1]) << (8-s)
            x &= 0x3f
            c = chars[x]
            if c in lower: has_lower = True
            elif c in upper: has_upper = True
            else: has_digits = True; assert c in digits
            p.append(c)
        if has_lower and has_upper and has_digits:
            break
    return ''.join(p)

if __name__ == '__main__':
    print generate()
