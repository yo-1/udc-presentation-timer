# Windows版 セキュリティ監査・比較検証

監査日：2026年10月17日（日本時間）。正式配布判定：**保留**。

## 対象と証拠の範囲

基準ソース：`6703a98d7a317137a39e1bc1ce673a0baf02c5cc`。
監査開始時に `git ls-remote origin HEAD refs/heads/main` で最新mainとの一致を確認した。
Python・HTML・JavaScript、バッチ、Actions、依存宣言、Git履歴を確認した。
検出済みEXEは取得・実行・隔離解除していない。新規EXEもこのLinux環境では実行しない。

旧 `UDC_Timer.exe` の情報は利用者提供：検出識別子 `ATC25475`、
`fileHash=967de53ae24e8522a6a66b6f418be50bce325d2d`、隔離成功。
40桁の16進表記でありSHA-1の長さに一致するが、製品ログの仕様確認前に算法を断定しない。
元の検出ログ、旧ファイルのSHA-256、署名、ビルド元コミット、依存一覧は未入手。
Git履歴にはEXE/DLL/ZIPの追跡記録がなく、旧バイナリと現行ソースの同一性は証明できない。
ファイル名の変更も誤検知解消や安全性の根拠にはならない。

## 静的監査

| 領域 | 確認結果・限界 |
| --- | --- |
| Windowsソースの全import・呼出し | 標準ライブラリのみ。Tkinter GUI、時間計測、スレッド、JSON設定、Windows winmm/MCI。ネットワーク、外部プロセス、eval/exec、レジストリ自動起動、権限昇格、認証情報収集は見当たらない。悪意の不在や配布バイナリの安全性を証明するものではない。 |
| ネイティブ呼出し | `ctypes.windll.winmm.mciSendStringW` による固定MP3の再生。シェルを経由しない。MCIの戻り値を確認せず、再生失敗の診断が不足する。MP3とOSデコーダも確認対象。 |
| ディスク書込 | import時の設定ディレクトリ作成、ユーザーのAPPDATA配下のJSON読書き。例外の握りつぶし、型・範囲・ファイルサイズの検証不足がある。ローカル設定改変で動作不良を起こし得るが、JSONをコードとして評価する処理はない。 |
| ソース直接実行 | `BASE`がwindowsディレクトリになるため、MP3を`windows/assets/bell.mp3`から探す。実際の素材はリポジトリ直下assetsにあり、直接実行時の音声欠落がある。PyInstallerの配置とは区別する。 |
| UI・タイマー | 手動試聴の`ring`はON/OFFを確認しない。ワーカースレッドからTk変数/UIへアクセスし、停止直後の再開でafterコールバックが重なる可能性がある。時計は単調時計でなく`time.time()`。これらは動作上の課題で、ウイルス検出原因とは確認されていない。アプリコードは今回変更していない。 |
| Web/PWA | 外部CDN・解析送信はない。固定素材のAudio、localStorage、PWAの同一サイトキャッシュを使用。HTML生成とlocalStorageからの値の扱いには追加の入力検証余地がある。今回の差分で公開運用は変更しない。 |

静的に確認した不審処理の不在と、第三者依存・ネイティブbootloader・OSデコーダを含む実行ファイルの安全性は別の問題である。

## 比較ビルド #5

[GitHub Actions 38953010619](https://github.com/yo-1/udc-presentation-timer/actions/runs/38953010619)
は基準コミットのworkflow_dispatch。API上の両ジョブと各工程はsuccess。
実行時刻は2026年10月17日04:11:01〜04:11:47（日本時間）。

| 成果物 | ZIPバイト数 | GitHubが公開するアーカイブSHA-256 |
| --- | ---: | --- |
| Comparison_onefile | 11248830 | `59a7762149c018eac53dd43dfe75cfac7754fed54b46f44bc85f2694b3cd5d43` |
| Comparison_onedir | 11804106 | `d198e56b59613d068083af2c681e84be934c65a60df33f922ba408992a528628` |
| Metadata_onefile | 583 | `cb53a4b714c0a7554dae4cf75c58520dbed95e3b11490993322840d4e55a4702` |
| Metadata_onedir | 45955 | `ebeebc83719d4972a306c846a0dd30d1ba1c4f7a960ef9c05b7a6018ad8bcb72` |

これらはZIPのダイジェストであり、EXE本体のハッシュではない。
onefileは起動時に内包ファイルを一時展開する方式、onedirは別ファイルを同梱する方式。
展開方式やbootloaderの差は検出差の仮説になり得るが、ATC25475の原因とは未確認。
onedirへの変更やUPX無効化だけで誤検知と判断しない。

## ビルドの改善

- `requirements-build.txt`をPyInstaller 6.22.3と推移依存を含む7パッケージの完全固定・wheel SHA-256検証に変更。
- Windows x64のCPython 3.13.16を固定。公式actions/python-versionsのmanifestで提供を確認。3.12系列のWindows配布が3.12.10で止まっているため、単に古い3.12.10へ固定せず保守対象系列へ移した。旧ビルドとの差を調べる場合は、このランタイム変更と依存更新も変数として扱う。
- 公式checkout/setup-python/upload-artifactのNode.js 24対応v6を取得時の完全コミットへ固定。タグの移動による差を防ぐ。
- contents:readを維持し、checkoutの資格情報永続化を無効化。pull_request_targetやsecretsは使用しない。PR用CI、15分上限、欠落成果物のエラー化を追加。
- CIとローカルで共通PowerShellスクリプトを使用。隔離venv、固定依存、pip check、テスト、`--noupx`、モード別出力を使用し、成果物は実行しない。
- install report、pip inspect/freeze、Python/pip・runner image・コミット・dirty状態・入力ハッシュ・ビルド警告とxref・全同梱ファイルのサイズ/SHA-256/SHA-1を保存。
- SHA-1は旧検出との識別補助のみ。整合性判定はSHA-256で行う。メタデータ自体の真正性も信頼できるGitHub実行とZIPダイジェストで確認する。
- Windows runner image、OS、pipのvenv同梱版、圧縮・時刻・署名等まで固定しておらず、バイト単位の再現性を保証しない。imageとpip版は記録する。未署名であることも記録対象。

[依存メタデータ](build-dependencies-2026-10-17.json)には公式PyPIのRequires-Dist、
Requires-Python、選択wheelのSHA-256、取得時のvulnerabilitiesを記録した。
全7wheelを取得してSHA-256照合し、pipのWindows対象ダウンロードも成功。
PyPIが返した該当版のvulnerabilitiesは全件空だったが、未知の脆弱性や別DBの見落としを否定しない。
インストール済み旧依存と新ロックは区別して比較する。

## 今回の検証結果と取得制限

改善コミット `b09ca6ab3357e0bef17b42e2341e3d906efa3a1e` の
[Windows CI 38955554555](https://github.com/yo-1/udc-presentation-timer/actions/runs/38955554555)
はonefile・onedirともsuccess。両ジョブでインストール、pip check、テスト、ビルド、
全ファイルinventoryの作成・照合とアップロードが成功した。両check-runのannotationsは空で、
旧実行にあったNode.js 20警告はこの実行では記録されていない。
Linuxではinventoryの6テストが全件成功（skipなし）、既存の構造assertionも成功。
Windowsログ本文をまだ取得できないため、Windows側の個別テスト件数・skip数は未確認。

| 新成果物 | ZIPバイト数 | APIに記録されたZIP SHA-256 |
| --- | ---: | --- |
| Comparison_onefile | 11532326 | `c938675353a239c6d960fabb2c48b2d475c419dc59e10043fc032e80ee36506e` |
| Comparison_onedir | 12026034 | `dbf1d80e0ad51d16eb55cfd5084aec939253b77493cf32fbda549d28bb04b43d` |
| Metadata_onefile | 53746 | `e5b828462895e17da286592b4a0eceee609124654cab433e5476bebea9820d6f` |
| Metadata_onedir | 126432 | `b75b324dfe0cc9b7248d9064892016d6382a63fa6a081cfca3c32af40575d63a` |

上記はAPIの記録確認であり、ダウンロードしたZIPの実測照合とは区別する。
旧比較runのアーカイブ取得はリダイレクト先`productionresultssa15.blob.core.windows.net`、
ログ取得は`results-receiver.actions.githubusercontent.com`への接続が403で止まった。
GitHubの成功ステータスだけで、ログ本文・旧依存一覧・EXE個別ハッシュ・内包ファイルを確認したとは記さない。
旧新の同梱物・依存の実物比較、旧EXEとのSHA-1/SHA-256照合、AV検査は未完了。
APIで確認できるZIPサイズは上表と旧run表のとおりだが、ランタイムと依存も変わっているため、方式だけの影響は推定しない。

GitHub API、成果物・ログ保存先、Microsoft/PyInstaller/Trend Micro公式資料のための
接続先を環境設定のネットワークドラフトへ追加保存した。ドラフト保存は実行環境への反映・公開ではない。
Trend Micro公式ページとPyInstaller公式サイトの閲覧も403で完了していない。
接続設定の反映後に失敗した取得を再実行し、表の実測照合と残課題を更新する。
新しい認証情報を追加する必要性は確認されていない。

## 検出原因と配布判定

`ATC25475`を特定のマルウェア名・挙動・PyInstaller誤検知へ結び付ける公式根拠は得られていない。
Trend Microへの問い合わせには検出画面・製品版・パターン版・時刻・フルパス・検出段階・ハッシュを添える。
旧サンプルを復元する必要がある場合は一般利用者に隔離解除を促さず、製品サポートの安全な手順を確認する。

SmartScreenはファイル・署名・評価情報に基づく警告を含み、ウイルスバスターの検出とは別に記録する。
警告だけで感染を断定せず、未検出やビルド成功だけで安全とも判断しない。
[Microsoft公式説明](https://learn.microsoft.com/en-us/windows/security/operating-system-security/virus-and-threat-protection/microsoft-defender-smartscreen/)を確認した。

配布再開には旧検出の照会結果、候補ハッシュの整合性、両方式の最新スキャンと隔離環境での試験、
同梱物・署名・残存リスクの確認と担当者の明示的判断が必要。
**現時点では正式配布保留を維持する。**

詳細な試験手順・残課題・結果様式は[WINDOWS_VALIDATION.md](WINDOWS_VALIDATION.md)を参照。
