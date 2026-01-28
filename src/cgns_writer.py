from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

import iric

from models import Group, Settings


@dataclass
class Array1D:
    data: List[float]

    @property
    def size(self) -> int:  # required by iric.py
        return len(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> float:
        return self.data[idx]


def prepare_output_dir(output_folder: Path) -> Path:
    # 日時サブディレクトリを作成する
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = output_folder / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def write_groups(
    input_cgns: Path,
    groups: List[Group],
    settings: Settings,
    steps: List[int],
    output_root: Path,
) -> None:
    # グループごとにCGNSをコピーして書き込む
    for group in groups:
        out_path = output_root / f"{group.name}.cgn"
        print(f"出力開始: {group.name} -> {out_path}")
        shutil.copy2(input_cgns, out_path)
        _write_group(out_path, group, settings, steps)
        print(f"出力完了: {group.name}")


def _write_group(
    out_path: Path, group: Group, settings: Settings, steps: List[int]
) -> None:
    # グループ単位の書き込み処理
    fid = iric.cg_iRIC_Open(str(out_path), iric.IRIC_MODE_MODIFY)
    try:
        # 2D構造格子を書き込む
        _write_grid(fid, group)
        iric.cg_iRIC_Write_Sol_Start(fid)
        for step in steps:
            time_val = settings.t0_seconds + settings.dt_seconds * step
            iric.cg_iRIC_Write_Sol_Time(fid, float(time_val))
            if step == steps[0]:
                print(f"時系列書込: step={step} time={time_val}")
            for series in group.variables:
                values = series.values_by_step.get(step)
                if values is None:
                    values = _nan_values(series.header.ncols * series.header.nrows)
                # セル値として書き込む
                iric.cg_iRIC_Write_Sol_Cell_Real(
                    fid, series.name, Array1D(values)
                )
        iric.cg_iRIC_Write_Sol_End(fid)
    finally:
        iric.cg_iRIC_Close(fid)


def _write_grid(fid: int, group: Group) -> None:
    # ASCヘッダから格子座標を構築する
    header = group.header
    isize = header.ncols + 1
    jsize = header.nrows + 1
    x_arr: List[float] = []
    y_arr: List[float] = []
    for j in range(jsize):
        y = header.yllcorner + j * header.dy
        for i in range(isize):
            x = header.xllcorner + i * header.dx
            x_arr.append(x)
            y_arr.append(y)
    iric.cg_iRIC_Write_Grid2d_Coords(fid, isize, jsize, Array1D(x_arr), Array1D(y_arr))


def _nan_values(size: int) -> List[float]:
    # 欠損値用のNaN配列
    return [float("nan")] * size
