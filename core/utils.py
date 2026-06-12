from django.conf import settings
from hashids import Hashids

# 初始化 Hashids 實例
hashids = Hashids(salt=settings.HASHIDS_SALT, min_length=settings.HASHIDS_MIN_LENGTH)

def encode_id(raw_id):
    """將整數 ID 加密成字串 (例如：12 -> 'J8xKp2y9')"""
    if not raw_id:
        return None
    return hashids.encode(raw_id)

def decode_id(hash_string):
    """將字串解密回整數 ID (例如：'J8xKp2y9' -> 12)"""
    if not hash_string:
        return None
    decoded = hashids.decode(hash_string)
    # 如果解密成功，decode 會回傳一個 tuple (12,)，所以我們取 [0]
    if decoded:
        return decoded[0]
    return None # 如果有人亂打網址，解密失敗會回傳 None