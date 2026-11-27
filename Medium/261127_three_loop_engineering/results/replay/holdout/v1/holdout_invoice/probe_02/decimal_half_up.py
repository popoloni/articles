from decimal import Decimal, ROUND_HALF_UP, localcontext

def transform(value: str) -> int:
    with localcontext() as ctx:
        ctx.prec = max(28, len(value) + 4)
        return int((Decimal(value) * 100).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP))
