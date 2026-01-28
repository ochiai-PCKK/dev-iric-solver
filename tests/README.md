# Tests

このディレクトリは、ソルバー実行フローを再現するための軽量スクリプトを置く。

- iRIC の Python インタープリタを使う。
- 設定ファイル（TOML）で引数や環境変数を切り替える。
- 実行対象は `src/definition.xml` の `executable` を読む。
- CGNS パスはエントリの第1引数として渡す。
- `check_cgns = true` の場合のみ iRIC API で CGNS を開閉できるかを事前に検証する。
- 実行時は `output_dir` 配下に日時サブディレクトリを作成し、CGNSをコピーしてから処理する。

## ファイル
- run_solver.py: 設定を読み、ソルバーのエントリを実行する。
- config.toml: 実行用設定。

## 使い方
```
C:\Users\yuuta.ochiai\iRIC_v4\Miniconda3\envs\iric\python.exe tests\run_solver.py --config tests\config.toml
```
