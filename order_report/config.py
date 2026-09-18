"""Konfiguration och sökvägar."""

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ReportConfig:
    """Sökvägar som används när rapporten skapas."""

    input_file: Path = PROJECT_ROOT / "data" / "orders.csv"
    output_folder: Path = PROJECT_ROOT / "output"

    def output_path(self, filename: str) -> Path:
        return self.output_folder / filename
