def unique_name(space, base, name=None):
    if not name or name in space:
        base = strip_number(name or base)
        name, num = f"{base}_0", 0
        while name in space:
            num += 1
            name = f"{base}_{num}"
    return name


def strip_number(name, sep='_'):
    base, _, num = name.rpartition(sep)
    try:
        int(num)
    except ValueError:
        return name
    else:
        return base

