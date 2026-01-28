from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


# 設定一式（calculation condition 由来）
@dataclass(frozen=True)
class Settings:
    asc_folder: Path
    output_folder: Path
    encoding: int
    flip_y: bool
    start_index: int
    num_steps: int
    zero_pad: int
    dt_seconds: float
    t0_seconds: float
    enabled_vars: List[str]


# ASCヘッダ情報
@dataclass(frozen=True)
class AscHeader:
    ncols: int
    nrows: int
    xllcorner: float
    yllcorner: float
    nodata_value: float
    dx: float
    dy: float


# 変数ごとの時系列データ
@dataclass
class VariableSeries:
    name: str
    header: AscHeader
    values_by_step: Dict[int, List[float]]


# グループ化キー（格子サイズ一致）
HeaderKey = Tuple[int, int, float, float, float, float]


# グループ単位の出力情報
@dataclass
class Group:
    key: HeaderKey
    header: AscHeader
    variables: List[VariableSeries]
    name: str
