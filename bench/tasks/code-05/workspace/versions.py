"""Version comparison and sorting."""


def _key(version):
    core = version.split("+")[0].split("-")[0]
    return tuple(int(part) for part in core.split("."))


def compare(a, b):
    ka, kb = _key(a), _key(b)
    return (ka > kb) - (ka < kb)


def sort_versions(versions):
    return sorted(versions, key=_key)
