from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree

from .config import get_section


def _check_cgns_open_close(cgns_path: Path) -> None:
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
    if not definition_path.exists():
        raise FileNotFoundError(f"definition.xml が見つかりません: {definition_path}")
    root = ElementTree.parse(definition_path).getroot()
    executable = root.attrib.get("executable")
    if not executable:
        raise ValueError("definition.xml に executable がありません")
    return executable


def _resolve_path(root: Path, value: str | None, default: str) -> Path:
    if value:
        path = Path(value)
    else:
        path = Path(default)
    return path if path.is_absolute() else root / path


def _build_command(
    cfg: dict,
    definition_path: Path,
    python_path: str,
    cgns_path: Path,
    output_dir: str | None,
) -> list[str]:
    entry = _load_executable(definition_path)
    entry_path = Path(entry)
    if not entry_path.is_absolute():
        entry_path = definition_path.parent / entry_path
    if not entry_path.exists():
        raise FileNotFoundError(f"executable が存在しません: {entry_path}")

    cgns_path_obj = Path(str(cgns_path))
    if not cgns_path_obj.exists():
        raise FileNotFoundError(f"cgns_path が存在しません: {cgns_path_obj}")

    if output_dir:
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


def run_test(args, cfg: dict) -> int:
    repo_root = Path.cwd()
    paths_cfg = get_section(cfg, "paths")
    test_cfg = get_section(cfg, "test")

    definition_path = _resolve_path(
        repo_root,
        args.definition or test_cfg.get("definition_path"),
        str(Path(paths_cfg.get("src_dir", "src")) / "definition.xml"),
    )

    python_path = args.python or test_cfg.get("python_path")
    cgns_path = args.cgns or test_cfg.get("cgns_path")
    workdir = args.workdir or test_cfg.get("workdir") or "."
    output_dir = args.output_dir or test_cfg.get("output_dir")
    check_cgns = bool(test_cfg.get("check_cgns", False)) if args.check_cgns is None else args.check_cgns

    if not python_path:
        raise ValueError("python_path は必須です")
    if not cgns_path:
        raise ValueError("cgns_path は必須です")

    workdir_path = _resolve_path(repo_root, workdir, ".").resolve()

    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    if check_cgns:
        cgns_path_obj = _resolve_path(repo_root, cgns_path, cgns_path)
        _check_cgns_open_close(cgns_path_obj)

    args_list = args.args if args.args is not None else test_cfg.get("args")
    if args_list is not None:
        test_cfg = dict(test_cfg)
        test_cfg["args"] = args_list

    cmd = _build_command(
        test_cfg,
        definition_path,
        python_path,
        _resolve_path(repo_root, cgns_path, cgns_path),
        output_dir,
    )

    env = os.environ.copy()
    env_overrides = test_cfg.get("env") or {}
    if not isinstance(env_overrides, dict):
        raise ValueError("env は辞書で指定してください")
    env.update({str(k): str(v) for k, v in env_overrides.items()})

    print("実行:", " ".join(cmd))
    print("作業ディレクトリ:", workdir_path)
    result = subprocess.run(cmd, cwd=str(workdir_path), env=env)
    return result.returncode
