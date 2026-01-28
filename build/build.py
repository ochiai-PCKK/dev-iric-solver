"""ビルドスクリプト。

src/ 配下のファイルを再帰的に収集して dist/ に出力する。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import shutil
import sys
from pathlib import Path


def _load_config(config_path: Path) -> dict[str, object]:
    if not config_path.exists():
        return {}
    try:
        import tomllib
    except ImportError:
        print("エラー: TOMLの読み込みにはPython 3.11以降が必要です。", file=sys.stderr)
        return {}
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _read_release_date(definition_path: Path) -> str | None:
    if not definition_path.exists():
        return None
    try:
        text = definition_path.read_text(encoding="utf-8")
    except Exception:
        return None
    start = text.find("<SolverDefinition")
    if start == -1:
        return None
    key = 'release="'
    idx = text.find(key, start)
    if idx == -1:
        return None
    idx += len(key)
    end_idx = text.find("\"", idx)
    if end_idx == -1:
        return None
    return text[idx:end_idx].strip() or None


def _read_version(definition_path: Path) -> str | None:
    if not definition_path.exists():
        return None
    try:
        text = definition_path.read_text(encoding="utf-8")
    except Exception:
        return None
    start = text.find("<SolverDefinition")
    if start == -1:
        return None
    key = 'version="'
    idx = text.find(key, start)
    if idx == -1:
        return None
    idx += len(key)
    end_idx = text.find("\"", idx)
    if end_idx == -1:
        return None
    return text[idx:end_idx].strip() or None


def _normalize_release_date(value: str) -> str | None:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) == 8:
        return digits
    return None


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    dist_root = repo_root / "dist"
    dev_root = dist_root / "dev"
    release_root = dist_root / "release"
    config_path = Path(__file__).with_name("build.config.toml")

    parser = argparse.ArgumentParser()
    parser.add_argument("--solver-dir-name", dest="solver_dir_name")
    parser.add_argument("--date", dest="date_stamp")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--dev", action="store_true")
    parser.add_argument("--zip-version", action="store_true")
    args = parser.parse_args()

    if args.release and args.dev:
        print("エラー: --release と --dev は同時に指定できません。", file=sys.stderr)
        return 2

    if not args.release and not args.dev:
        print("エラー: --dev か --release を指定してください。", file=sys.stderr)
        return 2

    if args.release:
        date_stamp = args.date_stamp or _dt.datetime.now().strftime("%Y%m%d")
    else:
        date_stamp = args.date_stamp or _dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    solver_dir_name = args.solver_dir_name
    if not solver_dir_name:
        config = _load_config(config_path)
        build_cfg = config.get("build") if isinstance(config.get("build"), dict) else {}
        solver_dir_name = build_cfg.get("solver_dir_name") or None

    if not solver_dir_name:
        print(
            "ソルバーディレクトリ名が未設定です。--solver-dir-name か build/build.config.toml を設定してください。",
            file=sys.stderr,
        )
        return 2

    if args.release:
        out_dir = release_root / f"{solver_dir_name}"
    else:
        out_dir = dev_root / f"{solver_dir_name}_{date_stamp}"

    zip_path = None
    if args.release:
        zip_suffix = date_stamp
        if args.zip_version:
            definition_path = repo_root / "src" / "definition.xml"
            version = _read_version(definition_path)
            if version:
                zip_suffix = f"v{version}"
            else:
                print(
                    "警告: definition.xml の version が読み取れません。日付でZIP名を作成します。",
                    file=sys.stderr,
                )
        zip_path = release_root / f"{solver_dir_name}-{zip_suffix}.zip"
    if out_dir.exists():
        if args.force:
            shutil.rmtree(out_dir)
        else:
            print(f"出力先が既に存在します: {out_dir}。上書きする場合は --force を付けてください。", file=sys.stderr)
            return 1

    out_dir.mkdir(parents=True, exist_ok=False)

    # Copy all files under src recursively
    if not src_dir.exists():
        print(f"src ディレクトリが見つかりません: {src_dir}", file=sys.stderr)
        return 1

    if args.release:
        definition_path = repo_root / "src" / "definition.xml"
        release_raw = _read_release_date(definition_path)
        release_norm = _normalize_release_date(release_raw) if release_raw else None
        if release_norm is None:
            print(
                "警告: definition.xml の release が読み取れません。日付が正しいか確認してください。",
                file=sys.stderr,
            )
        elif release_norm != date_stamp:
            print(
                "警告: definition.xml の release 日付が一致しません。"
                "definition.xml の release を更新してください。",
                file=sys.stderr,
            )

    for path in src_dir.rglob("*"):
        rel = path.relative_to(src_dir)
        if "__pycache__" in rel.parts:
            continue
        if path.is_file() and path.suffix.lower() == ".pyc":
            continue
        dest = out_dir / rel
        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)

    if args.release and zip_path is not None:
        if zip_path.exists():
            if args.force:
                zip_path.unlink()
            else:
                print(f"ZIPが既に存在します: {zip_path}。上書きする場合は --force を付けてください。", file=sys.stderr)
                return 1
        archive_base = str(zip_path.with_suffix(""))
        shutil.make_archive(archive_base, "zip", root_dir=release_root, base_dir=solver_dir_name)
        print(f"出力完了: {out_dir}")
        print(f"ZIP作成: {zip_path}")
    else:
        print(f"出力完了: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
