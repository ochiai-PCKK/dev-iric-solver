from __future__ import annotations

from typing import Dict, List

from models import Group, HeaderKey, VariableSeries


def _header_key(series: VariableSeries) -> HeaderKey:
    # グループ化キーの生成
    h = series.header
    return (h.ncols, h.nrows, h.xllcorner, h.yllcorner, h.dx, h.dy)


def group_by_header(series_list: List[VariableSeries]) -> List[Group]:
    # ヘッダ一致でグループ化する
    groups: Dict[HeaderKey, List[VariableSeries]] = {}
    for series in series_list:
        key = _header_key(series)
        groups.setdefault(key, []).append(series)

    result: List[Group] = []
    for key, vars_list in groups.items():
        names = sorted(v.name for v in vars_list)
        group_name = "_".join(names)
        header = vars_list[0].header
        result.append(Group(key=key, header=header, variables=vars_list, name=group_name))

    return result
