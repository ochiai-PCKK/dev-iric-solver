import argparse
import os
import shutil
import subprocess
from datetime import datetime
from xml.etree import ElementTree
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 or earlier
    tomllib = None


def _load_config(path: Path) -> dict:
    # TOML設定を読み込む
    if not path.exists():
        raise FileNotFoundError(f"config が見つかりません: {path}")
    if tomllib is None:
        raise RuntimeError("tomllib が使用できません。Python 3.11+ を使用してください。")
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _apply_overrides(cfg: dict, args: argparse.Namespace) -> dict:
    # コマンドライン引数で上書きする
    if args.python:
        cfg["python_path"] = args.python
    if args.cgns:
        cfg["cgns_path"] = args.cgns
    if args.workdir:
        cfg["workdir"] = args.workdir
    if args.output_dir:
        cfg["output_dir"] = args.output_dir
    if args.args is not None:
        cfg["args"] = args.args
    return cfg


def _check_cgns_open_close(cgns_path: Path) -> None:
    # iRIC API でCGNSの開閉を検証する
    try:
        import iric
    except Exception as exc:
        raise RuntimeError(f"failed to import iric: {exc}") from exc
    try:
        fid = iric.cg_iRIC_Open(str(cgns_path), iric.IRIC_MODE_READ)
    except Exception as exc:
        raise RuntimeError(f"failed to open CGNS: {cgns_path}") from exc
    try:
        iric.cg_iRIC_Close(fid)
    except Exception as exc:
        raise RuntimeError(f"failed to close CGNS: {cgns_path}") from exc


def _load_executable(definition_path: Path) -> str:
    # definition.xml から executable を取得する
    if not definition_path.exists():
        raise FileNotFoundError(f"definition.xml が見つかりません: {definition_path}")
    root = ElementTree.parse(definition_path).getroot()
    executable = root.attrib.get("executable")
    if not executable:
        raise ValueError("definition.xml に executable がありません")
    return executable


def _build_command(cfg: dict) -> list[str]:
    # definition.xml の executable を起点にコマンドを構築する
    python_path = cfg.get("python_path")
    definition_path = Path("src/definition.xml")
    entry = _load_executable(definition_path)
    cgns_path = cfg.get("cgns_path")
    output_dir = cfg.get("output_dir")
    if not python_path:
        raise ValueError("python_path は必須です")
    if not entry:
        raise ValueError("executable が空です")
    entry_path = Path(entry)
    if not entry_path.is_absolute():
        entry_path = definition_path.parent / entry_path
    if not entry_path.exists():
        raise FileNotFoundError(f"executable が存在しません: {entry_path}")
    if not cgns_path:
        raise ValueError("cgns_path は必須です")
    cgns_path_obj = Path(str(cgns_path))
    if not cgns_path_obj.exists():
        raise FileNotFoundError(f"cgns_path が存在しません: {cgns_path_obj}")
    if output_dir:
        # 出力先に日時サブディレクトリを作成しコピーする
        output_dir_obj = Path(str(output_dir))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir_obj = output_dir_obj / timestamp
        output_dir_obj.mkdir(parents=True, exist_ok=True)
        copied_path = output_dir_obj / cgns_path_obj.name
        shutil.copy2(cgns_path_obj, copied_path)
        cgns_path_obj = copied_path
    cmd = [python_path, str(entry_path), str(cgns_path_obj)]
    extra_args = cfg.get("args") or []
    if not isinstance(extra_args, list):
        raise ValueError("args は配列で指定してください")
    cmd.extend(str(a) for a in extra_args)
    return cmd


def main() -> int:
    # 設定読み込み -> 検証 -> 実行
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="tests/config.toml")
    parser.add_argument("--python")
    parser.add_argument("--cgns")
    parser.add_argument("--workdir")
    parser.add_argument("--output-dir")
    parser.add_argument("--args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    cfg = _load_config(Path(args.config))
    cfg = _apply_overrides(cfg, args)

    workdir = Path(cfg.get("workdir") or ".").resolve()
    output_dir = cfg.get("output_dir")
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    check_cgns = bool(cfg.get("check_cgns", False))
    if check_cgns:
        cgns_path = Path(cfg.get("cgns_path") or "")
        _check_cgns_open_close(cgns_path)

    cmd = _build_command(cfg)
    env = os.environ.copy()
    env_overrides = cfg.get("env") or {}
    if not isinstance(env_overrides, dict):
        raise ValueError("env は辞書で指定してください")
    env.update({str(k): str(v) for k, v in env_overrides.items()})

    print("実行:", " ".join(cmd))
    print("作業ディレクトリ:", workdir)
    result = subprocess.run(cmd, cwd=str(workdir), env=env)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
