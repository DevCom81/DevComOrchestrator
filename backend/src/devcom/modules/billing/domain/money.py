from __future__ import annotations

from decimal import ROUND_CEILING, Decimal, localcontext
from fractions import Fraction

EUR_MICROS_PER_EURO = 1_000_000
USD_MICROS_PER_DOLLAR = 1_000_000


def ceil_to_int(value: Decimal | Fraction | str) -> int:
    if isinstance(value, Fraction):
        with localcontext() as ctx:
            ctx.rounding = ROUND_CEILING
            decimal_value = Decimal(value.numerator) / Decimal(value.denominator)
            return int(decimal_value.to_integral_value(rounding=ROUND_CEILING))
    with localcontext() as ctx:
        ctx.rounding = ROUND_CEILING
        number = value if isinstance(value, Decimal) else Decimal(value)
        return int(number.to_integral_value(rounding=ROUND_CEILING))


def usd_micros_from_tokens(
    *,
    input_tokens: int,
    output_tokens: int,
    input_usd_per_mtok: str,
    output_usd_per_mtok: str,
    uplift_ratio: str = "0",
) -> int:
    """Cost in millionths of USD, ceiling after rational math."""
    pin = Fraction(input_usd_per_mtok)
    pout = Fraction(output_usd_per_mtok)
    uplift = Fraction(1) + Fraction(uplift_ratio)
    usd = (
        (Fraction(input_tokens) * pin + Fraction(output_tokens) * pout)
        / Fraction(1_000_000)
    ) * uplift
    return ceil_to_int(usd * Fraction(USD_MICROS_PER_DOLLAR))


def eur_micros_from_usd_micros(
    usd_micros: int,
    *,
    usd_to_eur: str,
    fx_margin_ratio: str,
) -> int:
    rate = Fraction(usd_to_eur) * (Fraction(1) + Fraction(fx_margin_ratio))
    eur = Fraction(usd_micros, USD_MICROS_PER_DOLLAR) * rate
    return ceil_to_int(eur * Fraction(EUR_MICROS_PER_EURO))


def format_eur_micros(micros: int) -> str:
    whole = micros // EUR_MICROS_PER_EURO
    frac = abs(micros) % EUR_MICROS_PER_EURO
    return f"{whole}.{frac:06d}"
