"""Trusted patch catalogue. An agent selects an ID, never executable input."""
PATCHES = {
    'float_round': '''def transform(value: str) -> int:
    return round(float(value) * 100)
''',
    'float_truncate': '''def transform(value: str) -> int:
    return int(float(value) * 100)
''',
    'decimal_half_even': '''from decimal import Decimal, ROUND_HALF_EVEN, localcontext

def transform(value: str) -> int:
    with localcontext() as ctx:
        ctx.prec = max(28, len(value) + 4)
        return int((Decimal(value) * 100).quantize(
            Decimal("1"), rounding=ROUND_HALF_EVEN))
''',
    'decimal_half_up': '''from decimal import Decimal, ROUND_HALF_UP, localcontext

def transform(value: str) -> int:
    with localcontext() as ctx:
        ctx.prec = max(28, len(value) + 4)
        return int((Decimal(value) * 100).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP))
''',
    'strip_lower': '''def transform(value: str) -> str:
    return value.strip().lower()
''',
    'strip_only': '''def transform(value: str) -> str:
    return value.strip()
''',
}
# Each route lists its patches in the order a scripted worker tries them.
ROUTES = {'float_first': ('float_round', 'float_truncate'),
          'decimal_exact': ('decimal_half_up', 'decimal_half_even'),
          'normalize': ('strip_lower', 'strip_only')}
FAMILIES = {'money': ('float_round', 'float_truncate', 'decimal_half_up', 'decimal_half_even'),
            'text': ('strip_lower', 'strip_only')}
FAMILY_ROUTES = {'money': ('float_first', 'decimal_exact'), 'text': ('normalize',)}
