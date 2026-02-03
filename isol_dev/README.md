# isol-dev

iRIC ソルバー開発向けの補助 CLI。

## すぐ使う (最短手順)
1. インストール
```
pip install -e ./isol_dev
```

2. 初期化 (テンプレ生成)
```
isol-dev init
```

3. 設定ファイルを編集
- `isol_dev.toml` の `test.python_path` と `test.cgns_path` を実環境に合わせる

4. テスト実行
```
isol-dev test
```

5. ビルド
```
isol-dev build --dev
```

## 設定ファイル
- 既定の設定ファイルは `isol_dev.toml` (実行ディレクトリ)。
- `--config` で任意のパスを指定可能。

### 編集が必要
- `build.solver_dir_name`
- `test.python_path`
- `test.cgns_path`

### 変更しなくてOK
- `paths.*`
- `test.args`
- `test.output_dir`
- `test.check_cgns`

### 任意
- `test.env`

## init の挙動
- `src/` と `src/definition.xml`、`src/main.py` を生成
- `isol_dev.toml` を生成
- iRIC Python の自動検出を試みる
  - 環境変数 `IRIC_PYTHON` があれば最優先
  - それ以外は一般的なパスを探索
  - 見つからない場合は `isol_dev.toml` を手動修正

## テストの考え方
iRIC のプロジェクトを「開発中ソルバー」で保存した CGNS を使用する。
計算条件や入力格子を保存した後の CGNS を使うことで、テストの反復が高速になる。

テストで出力された CGNS は iRIC の GUI で開くことができ、結果の可視化が可能。

## ビルドの考え方
`build` は `src/` 以下を配布用ソルバーディレクトリにまとめる。
開発用ビルドは `dist/dev/<solver_dir_name>_<YYYYMMDD>_<HHMMSS>` に出力される。

リリースビルドは `dist/release/<solver_dir_name>` に出力し、ZIP も生成する。
`--zip-version` を付けると `definition.xml` の `version` を使って ZIP 名を作成する。

### リリース例
```
isol-dev build --release --zip-version
```
