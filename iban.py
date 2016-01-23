import string

ibanlength = { 'AL': 28, 'AD': 24, 'AZ': 28, 'BH': 22, 'BE': 16,
               'BA': 20, 'BR': 29, 'BG': 22, 'CR': 21, 'DK': 18,
               'DE': 22, 'DO': 28, 'EE': 20, 'FO': 18, 'FI': 18,
               'FR': 27, 'GF': 27, 'PF': 27, 'TF': 27, 'GE': 22,
               'GI': 23, 'GR': 27, 'GL': 18, 'GP': 27, 'GT': 28,
               'HK': 16, 'IE': 22, 'IS': 26, 'IL': 23, 'IT': 27,
               'VG': 24, 'KZ': 20, 'HR': 21, 'KW': 30, 'LV': 21,
               'LB': 28, 'LI': 21, 'LT': 20, 'LU': 20, 'MT': 31,
               'MA': 24, 'MQ': 27, 'MR': 27, 'MU': 30, 'YT': 27,
               'MK': 19, 'MD': 24, 'MC': 27, 'ME': 22, 'NC': 27,
               'NL': 18, 'NO': 15, 'AT': 20, 'PK': 24, 'PS': 29,
               'PL': 28, 'PT': 25, 'RE': 27, 'RO': 24, 'BL': 27,
               'MF': 27, 'SM': 27, 'SA': 24, 'SE': 24, 'CH': 21,
               'RS': 22, 'SK': 24, 'SI': 19, 'ES': 24, 'PM': 27,
               'CZ': 24, 'TN': 24, 'TR': 26, 'HU': 28, 'AE': 23,
               'GB': 22, 'WF': 27, 'CY': 28}

def ibanvalid(iban, germany_only=False):
    iban = iban.replace(' ', '').upper()
    if iban[:2] not in ibanlength: return False
    if germany_only and iban[:2] != 'DE': return False
    if len(iban) != ibanlength[iban[:2]]: return False
    iban = iban[4:] + iban[:4]
    for i, c in enumerate(string.ascii_uppercase):
        iban = iban.replace(c, str(i+10))
    if not iban.isdigit(): return False
    return int(iban) % 97 == 1
