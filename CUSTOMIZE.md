# 自分たちのタイマーを作る（フォーク・カスタマイズガイド）

UDCタイマーは、地域の活動拠点、学会、イベント、勉強会などの発表用タイマーへ改造できるよう、ソースコードを公開しています。

**プログラムはGPL-3.0-onlyです。ロゴ・画像・音声の扱いは [ASSETS_LICENSE.md](ASSETS_LICENSE.md) を必ず確認してください。**

## 1. GitHubでフォークする

1. [元のリポジトリ](https://github.com/yo-1/udc-presentation-timer)を開きます。
2. 右上の **Fork** → **Create fork** を選択します。
3. 自分のGitHubアカウントにコピーされたリポジトリを開きます。
4. GitHubの編集画面、またはPCのエディターで変更します。

最初はブラウザ版の改造が簡単です。PythonやEXEのビルド環境は不要です。

## 2. どのファイルを変更するか

| やりたいこと | 主な変更先 |
| --- | --- |
| ブラウザ版の名称・見出し・配色 | `web/index.html` |
| PWA版の名称・見出し・配色 | `pwa/index.html` |
| ホーム画面に表示するPWA名 | `pwa/manifest.webmanifest` |
| PWAアイコンの差し替え | `pwa/icons/icon-192.png`、`icon-512.png` |
| ロゴ・ベル画像・音声の差し替え | `assets/udc_logo.png`、`bell_image.png`、`bell.mp3` |
| オフラインで保存するファイルの変更 | `pwa/service-worker.js` |
| Windows版の画面・動作 | `windows/udc_timer.py` |

現在のブラウザ版とPWA版は別々のHTMLファイルです。両方を同じデザインにする場合は、**両方を変更**してください。

## 3. 名称・色・画像を変える

1. `web/index.html` の `<title>`、見出し、CSSの色設定を変更します。
2. PWA版も使う場合は `pwa/index.html` の同じ箇所を変更します。
3. `pwa/manifest.webmanifest` の `name`、`short_name`、`theme_color` を変更します。
4. UDCロゴなどの素材を、自分で利用権限を持つものに差し替えます。画像・音声を変更した場合、HTMLやサービスワーカー内のファイルパスも確認してください。
5. PWAの変更を配信した場合は、`pwa/service-worker.js` の `CACHE` 名も更新して、古いキャッシュの残存を防ぎます。

**注意：** `assets/` はブラウザ版とPWA版で共有しています。ファイルを同名で置き換えると両方に影響します。別々の画像を使う場合は、別名ファイルを追加して各HTMLの参照先を変更してください。

## 4. 発表時間・ベルの設定

利用時の発表時間、各ベルの鳴動時刻、ON/OFF、音量は画面から変更・保存できます。まずはコードを編集せずに設定を試してください。

初期値やベル回数を変更したい場合は、各版のソース内で初期設定値と鳴動処理を確認して変更します。ベル1～4は現状、1・2・3・8回です。

## 5. 自分のGitHub Pagesで公開する

1. フォークしたリポジトリの **Settings → Pages** を開きます。
2. **Deploy from a branch** を選び、`main` と `/(root)` を指定して保存します。
3. 公開後、`https://<GitHubユーザー名>.github.io/<リポジトリ名>/web/` を開きます。
4. PWA版は末尾を `/pwa/` に変えて開きます。
5. ロゴ・ベル音・アイコンの表示、ベル試聴、設定保存、iPadオフライン動作を確認します。

GitHub Pagesの利用条件・公開設定はご自身のリポジトリで確認してください。PWAのオフライン利用は初回オンライン読み込みが必要です。

## 6. 改良を元のUDCタイマーへ還元する

バグ修正や汎用的な新機能は、[Issues](https://github.com/yo-1/udc-presentation-timer/issues) で提案し、Pull Requestを送ることができます。詳しくは [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## 7. ライセンスと表示

ソースコードを配布する場合は、GPL-3.0-onlyの条件（ライセンス文、著作権表示、対応するソースコードの提供等）を守ってください。改変した場合は変更を示してください。ロゴ・音声などはGPLとは別の扱いです。
