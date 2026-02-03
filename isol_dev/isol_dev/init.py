from __future__ import annotations

import os
import shutil
from pathlib import Path

from .config import DEFAULT_CONFIG_NAME


def _copy_template(template_path: Path, dest_path: Path, force: bool) -> None:
    if dest_path.exists():
        if force:
            if dest_path.is_dir():
                shutil.rmtree(dest_path)
            else:
                dest_path.unlink()
        else:
            print(f"既に存在するためスキップ: {dest_path}")
            return
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_path, dest_path)
    print(f"作成: {dest_path}")


def _find_iric_python() -> Path | None:
    env_path = os.environ.get("IRIC_PYTHON")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path

    home = Path.home()
    candidates = [
        home / "iRIC_v4" / "Miniconda3" / "envs" / "iric" / "python.exe",
        home / "iRIC_v4" / "Miniconda3" / "python.exe",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _write_config_with_detection(template_path: Path, dest_path: Path, force: bool) -> None:
    if dest_path.exists() and not force:
        print(f"既に存在するためスキップ: {dest_path}")
        return
    text = template_path.read_text(encoding="utf-8")
    detected = _find_iric_python()
    if detected:
        text = text.replace("C:/path/to/iric/python.exe", detected.as_posix())
        print(f"検出: iRIC Python = {detected}")
    else:
        print("iRIC Python を検出できませんでした。isol_dev.toml の python_path を手動で設定してください。")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(text, encoding="utf-8")
    print(f"作成: {dest_path}")


def run_init(args) -> int:
    root = Path(args.root or ".").resolve()
    config_path = Path(args.config) if args.config else (root / DEFAULT_CONFIG_NAME)
    src_dir = root / (args.src_dir or "src")
    definition_path = src_dir / "definition.xml"
    main_path = src_dir / "main.py"

    template_dir = Path(__file__).resolve().parent / "templates"
    config_template = template_dir / DEFAULT_CONFIG_NAME
    definition_template = template_dir / "definition.xml"
    main_template = template_dir / "main.py"

    root.mkdir(parents=True, exist_ok=True)
    src_dir.mkdir(parents=True, exist_ok=True)

    if config_template.exists():
        _write_config_with_detection(config_template, config_path, args.force)
    else:
        print(f"テンプレートが見つかりません: {config_template}")

    if definition_template.exists():
        _copy_template(definition_template, definition_path, args.force)
    else:
        print(f"テンプレートが見つかりません: {definition_template}")

    if main_template.exists():
        _copy_template(main_template, main_path, args.force)
    else:
        print(f"テンプレートが見つかりません: {main_template}")

    return 0
