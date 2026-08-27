"""
wordify.py
----------
Convert a decimal currency amount into words, matching the style seen on
the sample invoices, e.g.:

    16.500  -> "BHD Sixteen 500/1000 Fils Only."
    55.000  -> "BHD Fifty-five Only."
"""

from num2words import num2words


def amount_to_words(amount: float, currency: str = "BHD") -> str:
    amount = round(float(amount) + 1e-9, 3)
    whole = int(amount)
    # 3 decimal places -> fils out of 1000
    fils = int(round((amount - whole) * 1000))

    whole_words = num2words(whole).replace(",", "")
    whole_words = whole_words.capitalize()

    if fils > 0:
        return f"{currency} {whole_words} {fils:03d}/1000 Fils Only."
    return f"{currency} {whole_words} Only."
