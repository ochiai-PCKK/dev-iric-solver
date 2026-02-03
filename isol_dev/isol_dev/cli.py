from __future__ import annotations

import argparse
import sys

from .build import run_build
from .config import load_config, resolve_config_path
from .init import run_init
from .test import run_test


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="isol-dev")
    parser.add_argument("--config", help="設定ファイルパス (既定: ./isol_dev.toml)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    p_init = subparsers.add_parser("init", help="テンプレートを生成する")
    p_init.add_argument("--root", help="生成先ルートディレクトリ (既定: .)")
    p_init.add_argument("--src-dir", help="src ディレクトリ名 (既定: src)")
    p_init.add_argument("--force", action="store_true", help="既存ファイルを上書きする")

    p_build = subparsers.add_parser("build", help="配布用ソルバーをビルドする")
    p_build.add_argument("--solver-dir-name")
    p_build.add_argument("--date", dest="date_stamp")
    p_build.add_argument("--force", action="store_true")
    p_build.add_argument("--release", action="store_true")
    p_build.add_argument("--dev", action="store_true")
    p_build.add_argument("--zip-version", action="store_true")
    p_build.add_argument("--src-dir", help="src ディレクトリ (既定: config.paths.src_dir)")
    p_build.add_argument("--dist-dir", help="dist ディレクトリ (既定: config.paths.dist_dir)")

    p_test = subparsers.add_parser("test", help="ソルバー実行フローを再現する")
    p_test.add_argument("--python")
    p_test.add_argument("--cgns")
    p_test.add_argument("--workdir")
    p_test.add_argument("--output-dir")
    p_test.add_argument("--definition", help="definition.xml パス (既定: src/definition.xml)")
    p_test.add_argument("--check-cgns", dest="check_cgns", action="store_true", default=None)
    p_test.add_argument("--no-check-cgns", dest="check_cgns", action="store_false")
    p_test.add_argument("--args", nargs=argparse.REMAINDER)

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "init":
        return run_init(args)

    config_path = resolve_config_path(args.config)
    cfg = load_config(config_path)

    if args.command == "build":
        return run_build(args, cfg)
    if args.command == "test":
        return run_test(args, cfg)

    print("不明なコマンドです。", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
