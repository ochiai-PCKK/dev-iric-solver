# Build Scripts

このディレクトリにビルド用スクリプトを置く。
配布用ソルバー一式は `dist/dev/<solver_dir_name>_<YYYYMMDD>_<HHMMSS>` に出力する。
`--release` 指定時は `dist/release/<solver_dir_name>` に出力し、ZIPは `dist/release/<solver_dir_name>_<YYYYMMDD>.zip` を生成する。
`--zip-version` を付けると `definition.xml` の `version` を使い、`dist/release/<solver_dir_name>-v<version>.zip` を生成する。
実行時は `--dev` か `--release` を明示的に指定する。

## build.py
- `src/` 配下を再帰的に収集して出力する
- 既存の出力がある場合は `--force` で上書き
- ソルバー名は以下の優先度で決定する
  1) `--solver-dir-name` 引数
  2) `build/build.config.toml`

### 例
```
C:\Users\yuuta.ochiai\iRIC_v4\Miniconda3\envs\iric\python.exe build\build.py --solver-dir-name rriresultviewer --dev
```

### Release 例
```
C:\Users\yuuta.ochiai\iRIC_v4\Miniconda3\envs\iric\python.exe build\build.py --solver-dir-name rriresultviewer --release
```

### Release + バージョンZIP 例
```
C:\Users\yuuta.ochiai\iRIC_v4\Miniconda3\envs\iric\python.exe build\build.py  --release --zip-version
```
