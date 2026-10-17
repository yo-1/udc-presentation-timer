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
- Windows x64のCPython 3.13.16を固定。公式actions/python-versionsのmanifestで提供を確認。3.12系列のWindows配布が3.12.10で止まっているため、単に古い3.12.10へ固定せず保守対象系列へ移した。旧ビルドとの差を調べる場合は、ランタイム変更・隔離環境・依存固定化を区別する（取得後、7件の共通ビルド依存の版は旧新で同じと確認）。
- 公式checkout/setup-python/upload-artifactのNode.js 24対応v6を取得時の完全コミットへ固定。タグの移動による差を防ぐ。
- contents:readを維持し、checkoutの資格情報永続化を無効化。pull_request_targetやsecretsは使用しない。PR用CI、15分上限、欠落成果物のエラー化を追加。
- CIとローカルで共通PowerShellスクリプトを使用。隔離venv、固定依存、pip check、テスト、`--noupx`、モード別出力を使用し、成果物は実行しない。
- install report、pip inspect/freeze、Python/pip・runner image・コミット・dirty状態・入力ハッシュ・ビルド警告とxref・全同梱ファイルのサイズ/SHA-256/SHA-1を保存。
- SHA-1は旧検出との識別補助のみ。整合性判定はSHA-256で行う。メタデータ自体の真正性も信頼できるGitHub実行とZIPダイジェストで確認する。
- ビルド時の`PYTHONHASHSEED=0`と、コミット時刻に基づく`SOURCE_DATE_EPOCH`を追加。Python子プロセス終了後は元の値へ戻す。前者はZIP格納順の差、後者はPEビルド時刻の差を抑える。実行アプリの環境設定は変更しない。
- Windows runner image、OS、pipのvenv同梱版、絶対パスや署名等まで固定しておらず、バイト単位の完全な再現性は保証しない。imageとpip版は記録する。

[依存メタデータ](build-dependencies-2026-10-17.json)には公式PyPIのRequires-Dist、
Requires-Python、選択wheelのSHA-256、取得時のvulnerabilitiesを記録した。
全7wheelを取得してSHA-256照合し、pipのWindows対象ダウンロードも成功。
PyPIが返した該当版のvulnerabilitiesは全件空だったが、未知の脆弱性や別DBの見落としを否定しない。
インストール済み旧依存と新ロックは区別して比較する。

## 取得後の実物比較（2026年10月17日追記）

旧run #5 `38953010619`と、新PR run `38955830019`の各4ZIPおよびログ本文を取得した。
全8ZIPについてGitHub APIのSHA-256を実測照合し、全payloadについて対応metadataの
全ファイルハッシュと件数も照合した。新runでは両モードの6テストが全件成功、skipなしとログで確認した。
初回の403による取得制限はこの2runについて解消しており、未取得という前回の状態は更新する。

新run APIのheadは`a97ecc8f12dd217a37a3e9ae83c3f07a55b05345`だが、
PR用checkoutは合成マージコミット`30f897ad597fcec7b18f63a24d8d4d4e71969187`。
metadataはこのcheckoutのSHAを正しく記録していた。入力6ファイルのハッシュを作業ブランチと照合した
（Windows checkoutのCRLFも考慮）。APIのPR headとビルドしたcheckout SHAを混同しない。

| run | 方式 | EXEバイト数 | EXE SHA-256 |
| --- | --- | ---: | --- |
| 38953010619 | onefile | 11514780 | `b50e329c8acf0b66b3b854d6677973a3711732f994b31a10d575bc317f8ee7bd` |
| 38953010619 | onedir | 1821680 | `b3a8303a212782b7da79b58eed28148e556417268de510bb8cb7973ca6d85cdb` |
| 38955830019 | onefile | 11780175 | `05b8bdab8428f161c74d12f82d902873b28e7b4b2724229ed767d10ffd8e59fc` |
| 38955830019 | onedir | 1929239 | `bcfc26e228e7eb814ed9c7746f73aed68d6f32426311ac40aaa31da157b1abe5` |

上表はEXE本体の実測値。ZIPダイジェスト・SHA-1・PE情報・詳細比較は
[機械可読な検証記録](comparison-evidence-2026-10-17.json)に保存した。
旧検出fileHashをSHA-1と仮定すれば4件とも一致しないが、製品側の算法は未確認であり、
隔離された旧`UDC_Timer.exe`の同一性や安全性の結論には使わない。

### 同じrun内のonefileとonedir

- 両runともonedirは988ファイル（EXE 1件＋`_internal` 987件）。onefileのCArchiveは997件、onedir EXEのCArchiveは10件。
- onefileの格納名のWindows区切りを正規化して比較。外部987件のうち986件がバイト一致し、差は`base_library.zip`だけだった。欠落・余分な格納物はなかった。
- ZIPをさらに静的に解析すると、旧版155件・新版154件のメンバー内容とメタデータはそれぞれ両方式で一致し、格納順だけが異なった。バイトコードの差とは扱わない。
- アプリ本体`udc_timer`を含む、両EXE内の共通10格納物もすべてバイト一致。外部59件のDLL/PYDとMP3も一致した。
- 4EXEはPE x64 (`0x8664`) / GUI subsystem (`2`)。組み込みAuthenticode証明書テーブルは0バイト。Windows側の署名・評判確認は別途必要。
- PEの静的importはUSER32、COMCTL32、KERNEL32、ADVAPI32、GDI32。これだけでPython経由の通信有無や安全性は判断できない。

### 旧runと新run

- 7件のビルド依存は版がすべて同じだった。旧freezeの追加7件（argcomplete、click、colorama、filelock、pipx、platformdirs、userpath）はランナーの共存パッケージで、新しい隔離venvには含まれない。両runのPYZモジュール名にもこれらはなかった。
- 新freezeは`--all`によりpip 26.2.1も記録するため、旧freezeと単純な行数比較をしない。PYZのモジュール数は112→119。socket/subprocess/urllib等の標準モジュールも含まれるが、同梱だけで実行や通信の証拠とは扱わない。
- `_internal`の同一パス971件がバイト一致、15件が変化し、python312.dllがpython313.dllへ置換された。変化したファイルの一覧はJSONに保存した。
- PEの版情報はPython 3.12.10→3.13.16、OpenSSL 3.0.16→3.5.9、VC runtime 14.42.34438.0→14.51.36247.0。Tcl/Tkは両方8.6.15、zlibは両方1.3.1。版情報が同じでもTcl/Tk・zlibのバイナリハッシュは異なった。
- 新runのrunner imageは`20261012.333.1`。素材MP3はリポジトリおよび全候補と一致。Python同梱のネイティブライブラリはpip依存の脆弱性照会だけでは評価できず、AV検査と別の版・脆弱性確認が必要。

### 再現性と再利用可能な検証

`windows/compare_builds.py`は信頼済みPyInstaller/pefileでCArchive・PEを静的に読み、
両方式の格納物とZIPメンバーを比較する。payloadをimport/実行しない。
Windows区切り、格納名の重複・不正パス、内容改変とZIP順序差の区別を検証する3テストを追加し、
既存6件と合わせた9テストがLinuxで成功。旧・新の実ファイルでもこのCLIを実行して結果を保存した。

PyInstaller公式ソースの[再現性説明](https://github.com/pyinstaller/pyinstaller/blob/v6.22.3/doc/advanced-topics.rst)
を確認し、ビルド時のハッシュseedとPE時刻を固定した。設定後のWindows CIは後続の検証で確認する。
Trend Micro公式ページは引き続き取得できず、ATCコードの解釈は未確定。
通信ドラフトには新成果物の保存先`productionresultssa4.blob.core.windows.net`を追加保存した。
ドラフトの保存自体は実行設定の反映・公開を意味しない。実際の取得成功と設定状態は区別する。

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
