# UDC Presentation Timer / UDCタイマー Ver.3

UDC向けの学会・発表用タイマーです。Windows、ブラウザ、iPad（PWA）の3種類を同一仕様で提供します。

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
- UDCロゴ・UDCカラー

## 構成

- `web/` : ブラウザ版
- `pwa/` : iPad/Safari向けPWA版
- `windows/` : Python版およびWindows EXEビルド用ソース
- `assets/` : ロゴ、ベル画像、ベル音
- `tests/` : 構造確認用テスト

## Windows版

`windows/udc_timer.py` をPythonで起動できます。

EXE化する場合は `windows/build_exe.bat` を実行します。

## ブラウザ版

`web/index.html` をブラウザで開いて使用します。

## iPad版

`pwa/` をHTTPS配下で公開し、Safariから「ホーム画面に追加」して使用します。

## 注意

UDCロゴ・画像・音声素材の再配布条件については、公開前に権利関係を確認してください。
