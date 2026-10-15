# UDCタイマー / プレゼンタイマー Ver.3

ブラウザ版・iPad（PWA）版はUDC向けの「UDCタイマー」、Windows版は汎用の「プレゼンタイマー」です。同じリポジトリで管理しますが、画面デザインは異なります。

## 主な機能

- ベル1：1回
- ベル2：2回
- ベル3：3回
- ベル4：8回
- 各ベル個別のON/OFF
- 0分0秒を含む任意時刻でのベル鳴動
- MP3ベル音
- 音量調整
- 経過時間・残り時間表示
- 設定保存
- フルスクリーン表示
- UDCロゴ・UDCカラー（ブラウザ版・PWA版）

## 構成

- `web/` : ブラウザ版
- `pwa/` : iPad/Safari向けPWA版
- `windows/` : Python版およびWindows EXEビルド用ソース
- `assets/` : ロゴ、ベル画像、ベル音
- `tests/` : 構造確認用テスト

## Windows版：プレゼンタイマー Ver.3

`windows/udc_timer.py` をPythonで起動できます。EXE化する場合は `windows/build_exe.bat` を実行します。

生成ファイル名：`PresentationTimer.exe`。GitHub Actions成果物名：`PresentationTimer_Windows`。

Windows版にはUDCロゴを使用しません。既存の設定を引き継ぐため、設定保存先の旧フォルダ名は変更していません。

**安全性確認中：** Windows EXEはSmartScreen警告およびウイルスバスターの検出報告があるため、原因調査が終わるまで正式配布を保留しています。セキュリティ製品の除外登録や警告の無視は推奨しません。

## ブラウザ版

`web/index.html` をブラウザで開いて使用します。

## iPad版

`pwa/` をHTTPS配下で公開し、Safariから「ホーム画面に追加」して使用します。

## 注意

UDCロゴ・画像・音声素材の再配布条件については、公開前に権利関係を確認してください。
