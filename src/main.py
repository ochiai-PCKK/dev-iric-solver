import sys
from pathlib import Path

from asc_reader import collect_variable_series
from cgns_writer import prepare_output_dir, write_groups
from config_reader import read_settings
from grouping import group_by_header


def main() -> int:
    # 入口: CGNSパスは第1引数で受け取る
    if len(sys.argv) < 2:
        print("使い方: main.py <cgns_path>", file=sys.stderr)
        return 2

    cgns_path = Path(sys.argv[1])
    if not cgns_path.exists():
        print(f"CGNSが存在しません: {cgns_path}", file=sys.stderr)
        return 2

    # iRIClibで設定を読み取り、ASC時系列を収集する
    print("設定読取: 開始")
    settings = read_settings(str(cgns_path))
    print(f"設定読取: 完了 asc_folder={settings.asc_folder} output_folder={settings.output_folder}")
    print("ASC収集: 開始")
    steps, series_list = collect_variable_series(settings)
    print(f"ASC収集: 完了 変数数={len(series_list)} ステップ数={len(steps)}")
    if not series_list:
        print("有効な変数がありません", file=sys.stderr)
        return 2

    # グリッドヘッダでグループ化し、グループ単位で出力する
    groups = group_by_header(series_list)
    print(f"グループ化: {len(groups)} グループ")
    output_root = prepare_output_dir(settings.output_folder)
    print(f"出力先: {output_root}")
    write_groups(cgns_path, groups, settings, steps, output_root)
    print(f"出力完了: {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
