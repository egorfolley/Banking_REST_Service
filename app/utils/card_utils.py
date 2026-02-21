import hashlib


def hash_card_number(card_number: str) -> str:
    return hashlib.sha256(card_number.encode("utf-8")).hexdigest()


def last_four(card_number: str) -> str:
    return card_number[-4:]
