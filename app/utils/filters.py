import re


def brl(value):
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        value = 0.0

    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def cpf_mask(value):
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) != 11:
        return value or ""
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def phone_mask(value):
    digits = re.sub(r"\D", "", str(value or ""))

    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return value or ""