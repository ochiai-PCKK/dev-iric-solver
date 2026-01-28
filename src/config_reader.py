from __future__ import annotations

from pathlib import Path
from typing import List

import iric

from models import Settings


# 取り込み対象の変数一覧
VARIABLES = [
    "gampt_ff",
    "hf",
    "hg",
    "hr",
    "hs",
    "qr",
    "qrs",
]


def _read_string(fid: int, name: str) -> str:
    # 文字列項目の取得
    return iric.cg_iRIC_Read_String(fid, name)


def _read_integer(fid: int, name: str) -> int:
    # 整数項目の取得
    return iric.cg_iRIC_Read_Integer(fid, name)


def _read_real(fid: int, name: str) -> float:
    # 実数項目の取得
    return iric.cg_iRIC_Read_Real(fid, name)


def read_settings(cgns_path: str) -> Settings:
    # calculation condition を読み取る
    fid = iric.cg_iRIC_Open(cgns_path, iric.IRIC_MODE_READ)
    try:
        asc_folder = _read_string(fid, "asc_folder")
        output_folder = _read_string(fid, "output_folder")
        encoding = _read_integer(fid, "encoding")
        flip_y = _read_integer(fid, "flip_y") == 1
        start_index = _read_integer(fid, "start_index")
        num_steps = _read_integer(fid, "num_steps")
        zero_pad = _read_integer(fid, "zero_pad")
        dt_seconds = float(_read_real(fid, "dt_seconds"))
        t0_seconds = float(_read_real(fid, "t0_seconds"))

        # 変数スイッチの読み取り
        enabled_vars: List[str] = []
        for var in VARIABLES:
            flag = _read_integer(fid, f"use_{var}")
            if flag == 1:
                enabled_vars.append(var)
    finally:
        iric.cg_iRIC_Close(fid)

    # 必須項目の簡易チェック
    if not asc_folder:
        raise ValueError("asc_folder が未設定です")
    if not output_folder:
        raise ValueError("output_folder が未設定です")

    return Settings(
        asc_folder=Path(asc_folder),
        output_folder=Path(output_folder),
        encoding=encoding,
        flip_y=flip_y,
        start_index=start_index,
        num_steps=num_steps,
        zero_pad=zero_pad,
        dt_seconds=dt_seconds,
        t0_seconds=t0_seconds,
        enabled_vars=enabled_vars,
    )
