from typing import Optional


def parse_full_name(
    full_name: str,
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    parts = full_name.strip().split()
    given_name = addl_name = family_name = None
    if len(parts) == 1:
        given_name = parts[0]
    elif len(parts) == 2:
        given_name, family_name = parts
    elif len(parts) >= 3:
        given_name = parts[0]
        addl_name = " ".join(parts[1:-1])
        family_name = parts[-1]
    return given_name, addl_name, family_name


def get_full_name(given_name: str, addl_name: Optional[str], family_name: str) -> str:
    if addl_name:
        return f"{given_name} {addl_name} {family_name}"
    return f"{given_name} {family_name}"
