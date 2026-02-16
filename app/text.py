from typing import Any


def align_center(text: str, width: int, fill: str = "=") -> str:
    left = fill * int(width / 2 - len(text) / 2)
    right = fill * (int(width / 2 - len(text) / 2) + (1 if width % 2 else 0))
    return f"{left}{text}{right}"


def justify(*values: Any, width: int = 30, border: str | None = "|") -> str:
    parts = [str(v) for v in values]
    left_border = f"{border} " if border else ""
    right_border = f" {border}" if border else ""
    content_length = sum(len(p) for p in parts)
    border_length = len(left_border) + len(right_border)
    gaps = max(len(parts) - 1, 1)
    fixed_length = content_length + border_length
    total_spaces = width - fixed_length
    base_space = total_spaces // gaps
    extra = total_spaces % gaps
    justified = []

    for i, part in enumerate(parts):
        justified.append(part)

        if i < gaps:
            space = base_space + (1 if i < extra else 0)
            justified.append(" " * space)

    return f"{left_border}{''.join(justified)}{right_border}"
