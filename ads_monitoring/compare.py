from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComparisonResult:
    new_pairs: set[tuple[str, str]]
    removed_pairs: set[tuple[str, str]]

    @property
    def has_changes(self) -> bool:
        return bool(self.new_pairs or self.removed_pairs)


def compare_pairs(
    current_pairs: set[tuple[str, str]],
    previous_pairs: set[tuple[str, str]],
) -> ComparisonResult:
    return ComparisonResult(
        new_pairs=current_pairs - previous_pairs,
        removed_pairs=previous_pairs - current_pairs,
    )


def format_comparison(result: ComparisonResult) -> str:
    if not result.has_changes:
        return "Изменений нет."

    lines: list[str] = []
    if result.new_pairs:
        lines.append("Новые пары (domain + sale):")
        for domain, sale in sorted(result.new_pairs):
            lines.append(f"+ {domain} | {sale}")

    if result.removed_pairs:
        if lines:
            lines.append("")
        lines.append("Удаленные пары (domain + sale):")
        for domain, sale in sorted(result.removed_pairs):
            lines.append(f"- {domain} | {sale}")

    return "\n".join(lines)
