# Windows版 安全な比較検証手順と結果様式

## 開発者による再ビルド・照合

旧検出EXEを使わず、レビュー済みコミットからWindows x64/CPython 3.13.16で実施する。
PowerShellでリポジトリ直下から以下を実行する。実行ポリシーの回避やセキュリティ製品の除外はしない。

```powershell
./windows/build_comparison.ps1 -Mode onefile
./windows/build_comparison.ps1 -Mode onedir
python windows/artifact_inventory.py verify dist/onefile build/evidence/onefile/hashes.json
python windows/artifact_inventory.py verify dist/onedir build/evidence/onedir/hashes.json
python windows/artifact_inventory.py compare build/evidence/onefile/hashes.json build/evidence/onedir/hashes.json
```

以前のモード別`dist/<mode>`と`build/evidence/<mode>`が残っている場合は、証拠を保存して別の場所へ移す。
スクリプトは既存出力を上書きしない。ローカルbatは既定でonedirを生成する。
CIでビルドした場合は、同じrun ID/attemptの4成果物を取得し、API記載のZIPダイジェストを照合してから展開する。
Pythonの照合コマンドには**展開したComparisonのルート**と、対応するMetadataの`hashes.json`を渡す。
比較はパスを完全一致で扱うため、onedirの`PresentationTimer/`階層とonefileのルート配置の違いもonly_left/rightとして現れる。

ZIPダイジェスト、ファイルSHA-256、アプリ署名、ベンダーの検出結果を混同しない。
新しいinventoryはSHA-1も記録するが、旧検出ログの算法が未確認の間は一致/不一致の断定に使わない。
同梱物を調べるときはEXEをダブルクリックしない。onefile内部は信頼済みPyInstallerの
`pyi-archive_viewer -l <EXE>`等の静的解析で確認し、DLL・Python・Tk/Tcl・MP3の版/ハッシュをonedirと比較する。
バイナリ解析も更新済みの隔離解析環境で行い、EXE本体は起動しない。

## 実機で必要な最小検証

1. 検出ログの原本を保存し、ATC25475が「検出名」なのか管理用識別子なのか、fileHashの算法をTrend Microへ照会する。旧EXEの隔離は維持する。
2. 候補は新規の信頼できるCI成果物に限る。run/commit/依存/ZIPダイジェスト/各ファイルハッシュを照合し、破損や想定外ファイルがあれば停止する。
3. 更新済みWindowsの使い捨てVMを製品ごとに用意する。Defenderとウイルスバスターを無理に同時稼働させない。共有フォルダ・クリップボードを切り、個人データや認証情報を入れない。スキャン用更新後、機能試験時は通信を制限し、スナップショットを保持する。
4. 起動せずにZIPと展開後のフォルダ全体を各製品でカスタムスキャンする。検出された場合は隔離を維持し、実行せずログを保存する。検出ゼロでも安全の証明とはしない。
5. 一致する候補がスキャンを通り、担当者が試験継続を判断した場合だけ、隔離VMで新候補を通常権限で起動する。SmartScreenや製品がブロックした場合は回避せずそこで停止し、警告とファイルのインターネット由来情報を記録する。
6. 起動できた新候補のみ、開始/停止/リセット、0秒ベル、1/2/3/8回、ON/OFF・試聴、設定保存/再起動、フルスクリーン、スリープ前後の計時を確認する。意図しない通信・プロセス・永続化・ファイル書込も観測する。既知の機能課題は監査報告書と照合する。
7. どちらかだけ検出されても方式が原因と断定しない。同じソース・Python・依存・runner imageで揃え、検出ファイルが外側EXEか同梱DLL等か、保存/展開/スキャン/起動のどの段階かを比較する。

Defenderが稼働している検証VMでは、管理者PowerShellで次のように状態・署名情報を記録できる。
コマンドは候補EXEを実行しない。コマンド終了と検出ログを両方確認し、ゼロ検出を安全保証と扱わない。

```powershell
Get-MpComputerStatus | Select-Object AMProductVersion, AMEngineVersion, AntivirusSignatureVersion, AntivirusSignatureLastUpdated, AMRunningMode, AntivirusEnabled, RealTimeProtectionEnabled
Update-MpSignature
Start-MpScan -ScanType CustomScan -ScanPath 'C:\Audit\candidate'
Get-MpThreatDetection | Select-Object InitialDetectionTime, LastThreatStatusChangeTime, ThreatID, ActionSuccess, Resources
Get-AuthenticodeSignature 'C:\Audit\candidate\PresentationTimer.exe' | Select-Object Status, StatusMessage, SignerCertificate
Get-FileHash 'C:\Audit\candidate\PresentationTimer.exe' -Algorithm SHA256
```

ウイルスバスターでは製品UIのカスタムスキャンと検出履歴を使用し、製品・エンジン・パターン版を保存する。
未知のATCコード解釈や未確認CLIを前提にしない。サンプル送付は製品サポートの正式窓口と共有条件を確認する。
公開マルチエンジンサイトへのアップロードはサンプルの第三者共有を伴うため、この作業では行っていない。

## 結果記録様式（各候補×各製品で1件）

```text
試験ID / 担当者 / 日時（タイムゾーン）:
対象方式: onefile / onedir
GitHub run URL / attempt / commit / dirty状態:
ZIP名 / ZIP SHA-256 / 取得・照合結果:
EXE相対パス / サイズ / SHA-256 / SHA-1（識別補助）:
署名状態 / 発行者 / インターネット由来情報:
Python / PyInstaller / 依存一覧・pip inspect添付:
Windows版・build / VM隔離条件 / runner image:
製品名 / 製品版 / engine / pattern・署名版 / 最終更新:
スキャン対象: ZIP / 展開フォルダ / 同梱ファイル
検出段階: 保存 / 展開 / 明示スキャン / 起動
スキャン完了: はい / いいえ / エラー（未完了を検出ゼロと記さない）
結果: 検出あり / 検出なし / 未実施 / 不明
検出名・識別子 / 対象パス / 製品のhash算法と値 / 処置:
SmartScreen文言 / スクリーンショット / 検出ログ添付:
機能試験: 未実施 / 停止理由 / 各項目の結果
通信 / 子プロセス / 設定以外の書込・永続化:
ベンダー問い合わせ番号 / 回答 / 誤検知判定対象SHA-256:
試験中断・隔離状態 / 残課題 / 配布判断と判断者:
```

## 残課題

- [ ] ATC25475の意味・hash算法と旧EXEの由来を製品サポートで確認する。
- [ ] 旧EXEのSHA-256・署名・ビルド元・依存を、隔離解除や実行をせず入手可能な記録から確定する。
- [ ] #5のEXE/同梱物/依存/ログを照合し、新しい固定ビルドとの差を記録する。
- [x] 新CI 38955554555の両モード成功と4成果物のAPI情報を確認する。
- [ ] 新CIのログ本文、metadataの各項目・個別テスト件数・skip数とダウンロード後ハッシュを確認する。
- [ ] Defender・ウイルスバスターの最新スキャンと新候補の実機試験を行う。
- [ ] 直接実行時MP3パス、手動ベルOFF、Tkのスレッド操作、計時と再開の課題を別途修正・検証する。
- [ ] 署名・再現性・素材再配布条件・依存ライセンス/通知の配布前確認を完了する。
- [ ] 誤検知とする場合は対象SHA-256を指定したベンダー回答を保存し、担当者が配布可否を判断する。
