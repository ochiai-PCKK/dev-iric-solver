from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from models import AscHeader, Settings, VariableSeries


# ヘッダの表記揺れ対応
_KEY_ALIASES = {
    "ncols": "ncols",
    "nrows": "nrows",
    "xllcorner": "xllcorner",
    "yllcorner": "yllcorner",
    "xllcenter": "xllcenter",
    "yllcenter": "yllcenter",
    "cellsize": "cellsize",
    "dx": "dx",
    "dy": "dy",
    "nodata_value": "nodata",
    "nodata-value": "nodata",
    "nodata": "nodata",
    "no_data": "nodata",
    "nodata_value(s)": "nodata",
}


def _iter_lines(path: Path, encoding: int) -> List[str]:
    # encoding 指定に従って行を読み込む（Autoは cp932 -> utf-8）
    data = path.read_bytes()
    if encoding == 1:
        return data.decode("cp932").splitlines()
    if encoding == 2:
        return data.decode("utf-8").splitlines()
    for enc in ("cp932", "utf-8"):
        try:
            return data.decode(enc).splitlines()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8", data, 0, 1, "デコードに失敗しました")


def _parse_header(lines: List[str]) -> Tuple[AscHeader, int]:
    # ヘッダ部分を解析し、データ開始行を返す
    values: Dict[str, float] = {}
    data_start: Optional[int] = None

    for idx, raw in enumerate(lines):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            key_raw = parts[0].strip().lower()
            key = _KEY_ALIASES.get(key_raw)
            if key is not None:
                values[key] = float(parts[1])
                continue
        if _header_complete(values):
            data_start = idx
            break
        raise ValueError(f"ヘッダが不完全な状態で不明な行が現れました: {line}")

    if not _header_complete(values):
        raise ValueError("ヘッダ情報が不足しています")
    if data_start is None:
        data_start = len(lines)

    ncols = int(values["ncols"])
    nrows = int(values["nrows"])
    dx, dy = _resolve_cellsize(values)
    xllcorner, yllcorner = _resolve_origin(values, dx, dy)
    nodata_value = values["nodata"]

    return (
        AscHeader(
            ncols=ncols,
            nrows=nrows,
            xllcorner=xllcorner,
            yllcorner=yllcorner,
            nodata_value=nodata_value,
            dx=dx,
            dy=dy,
        ),
        data_start,
    )


def _header_complete(values: Dict[str, float]) -> bool:
    # 必須キーが揃っているか
    if "ncols" not in values or "nrows" not in values:
        return False
    has_x = "xllcorner" in values or "xllcenter" in values
    has_y = "yllcorner" in values or "yllcenter" in values
    has_cell = "cellsize" in values or ("dx" in values and "dy" in values)
    has_nodata = "nodata" in values
    return has_x and has_y and has_cell and has_nodata


def _resolve_cellsize(values: Dict[str, float]) -> Tuple[float, float]:
    # cellsize/dx/dy の優先順位を決める
    if "dx" in values and "dy" in values:
        dx = float(values["dx"])
        dy = float(values["dy"])
        return dx, dy
    if "cellsize" in values:
        cellsize = float(values["cellsize"])
        return cellsize, cellsize
    raise ValueError("cellsize もしくは dx/dy が指定されていません")


def _resolve_origin(values: Dict[str, float], dx: float, dy: float) -> Tuple[float, float]:
    # xllcenter/yllcenter を角座標に変換する
    if "xllcorner" in values:
        xllcorner = float(values["xllcorner"])
    else:
        xllcorner = float(values["xllcenter"]) - dx / 2.0
    if "yllcorner" in values:
        yllcorner = float(values["yllcorner"])
    else:
        yllcorner = float(values["yllcenter"]) - dy / 2.0
    return xllcorner, yllcorner


def _read_values(
    lines: List[str],
    start: int,
    header: AscHeader,
    flip_y: bool,
) -> List[List[float]]:
    # データ行を読み取り、NoDataをNaNに変換する
    rows: List[List[float]] = []
    line_idx = start
    while line_idx < len(lines) and len(rows) < header.nrows:
        raw = lines[line_idx].strip()
        line_idx += 1
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split()
        if len(parts) != header.ncols:
            raise ValueError(
                f"列数が一致しません: expected={header.ncols}, actual={len(parts)}"
            )
        row: List[float] = []
        for v in parts:
            val = float(v)
            if math.isclose(val, header.nodata_value, rel_tol=0.0, abs_tol=1e-9):
                val = float("nan")
            row.append(val)
        rows.append(row)

    if len(rows) != header.nrows:
        raise ValueError(f"行数が不足しています: expected={header.nrows}, actual={len(rows)}")

    if flip_y:
        rows = list(reversed(rows))
    return rows


def _flatten_column_major(values: List[List[float]]) -> List[float]:
    # 行優先で1次元化（C順）
    flat: List[float] = []
    for row in values:
        flat.extend(row)
    return flat


def read_asc(path: Path, encoding: int, flip_y: bool) -> Tuple[AscHeader, List[float]]:
    # ASC 1枚を読み込み、ヘッダと1次元配列を返す
    lines = _iter_lines(path, encoding)
    header, data_start = _parse_header(lines)
    values_2d = _read_values(lines, data_start, header, flip_y)
    flat = _flatten_column_major(values_2d)
    return header, flat


def _detect_max_index(
    asc_folder: Path, variables: Iterable[str], zero_pad: int
) -> Optional[int]:
    # ファイル名から最大インデックスを検出する
    max_index: Optional[int] = None
    pattern_cache: Dict[str, re.Pattern[str]] = {}
    for var in variables:
        pattern_cache[var] = re.compile(rf"^{re.escape(var)}_(\d+)[.]asc$", re.IGNORECASE)
    for path in asc_folder.glob("*.asc"):
        name = path.name
        for var, pattern in pattern_cache.items():
            match = pattern.match(name)
            if not match:
                continue
            index = int(match.group(1))
            if len(match.group(1)) != zero_pad:
                continue
            if max_index is None or index > max_index:
                max_index = index
    return max_index


def collect_variable_series(settings: Settings) -> Tuple[List[int], List[VariableSeries]]:
    # 設定に従って変数ごとの時系列を収集する
    asc_folder = settings.asc_folder
    if not asc_folder.exists():
        raise FileNotFoundError(f"asc_folder が存在しません: {asc_folder}")

    if settings.num_steps == 0:
        max_index = _detect_max_index(asc_folder, settings.enabled_vars, settings.zero_pad)
        if max_index is None:
            raise ValueError("ASCファイルが見つかりません")
        num_steps = max_index - settings.start_index + 1
        if num_steps <= 0:
            raise ValueError("自動検出したステップ数が不正です")
        print(f"ステップ自動検出: start={settings.start_index} max={max_index} num_steps={num_steps}")
    else:
        num_steps = settings.num_steps
        print(f"ステップ指定: start={settings.start_index} num_steps={num_steps}")

    steps = [settings.start_index + i for i in range(num_steps)]

    series_list: List[VariableSeries] = []
    for var in settings.enabled_vars:
        # ヘッダ参照を最初の存在ファイルから取得する
        header_ref: Optional[AscHeader] = None
        for step in steps:
            path = asc_folder / f"{var}_{step:0{settings.zero_pad}d}.asc"
            if path.exists():
                header_ref, _ = read_asc(path, settings.encoding, settings.flip_y)
                break
        if header_ref is None:
            print(f"警告: {var} のASCファイルが見つかりません")
            continue

        # ステップごとの値配列を保持する
        values_by_step: Dict[int, List[float]] = {}
        missing_count = 0
        for step in steps:
            path = asc_folder / f"{var}_{step:0{settings.zero_pad}d}.asc"
            if path.exists():
                header, values = read_asc(path, settings.encoding, settings.flip_y)
                if header != header_ref:
                    print(
                        f"警告: {var} のヘッダが一致しません。{path} を欠損として扱います"
                    )
                    values = _nan_values(header_ref)
                    missing_count += 1
            else:
                print(f"警告: {var} のファイルが欠損しています: {path}")
                values = _nan_values(header_ref)
                missing_count += 1
            values_by_step[step] = values

        print(f"変数収集: {var} 欠損={missing_count}/{len(steps)}")
        series_list.append(
            VariableSeries(name=var, header=header_ref, values_by_step=values_by_step)
        )

    return steps, series_list


def _nan_values(header: AscHeader) -> List[float]:
    # 欠損時に使うNaN配列
    size = header.ncols * header.nrows
    return [float("nan")] * size
