import re


def normalize_text(value):
    if not value:
        return None

    value = value.strip()
    value = re.sub(r'\s+', ' ', value)

    return value


def normalize_email(value):
    if not value:
        return None

    return value.strip().lower()


def normalize_phone(value):
    if not value:
        return None

    digits = re.sub(r'\D', '', value)

    if len(digits) == 11:
        return f'({digits[:2]}) {digits[2:7]}-{digits[7:]}'

    if len(digits) == 10:
        return f'({digits[:2]}) {digits[2:6]}-{digits[6:]}'

    return digits


def only_digits(value):
    if not value:
        return None

    return re.sub(r'\D', '', value)