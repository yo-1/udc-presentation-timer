# 公開・配布チェックリスト

## ソースコード・コミュニティ
- [x] プログラムのライセンスをGPL-3.0-onlyとし、LICENSEを登録
- [x] ロゴ・画像・音声・PWAアイコンをGPL対象外として区別（ASSETS_LICENSE.md）
- [x] フォーク・改造手順を公開（CUSTOMIZE.md）
- [x] Issue・Pull Requestの貢献ガイドを公開（CONTRIBUTING.md）
- [x] READMEに利用者向けリンクと派生開発の案内を掲載
- [ ] 素材の第三者による再配布・改変条件を個別に明文化（未許諾の場合は差し替え）
- [ ] 既存コードの著作権・第三者由来コードのライセンス整合性を最終確認

## ブラウザ版・PWA版
- [x] GitHub Pagesを有効化し、公開URLで表示を確認
- [x] iPad実機でホーム画面追加とオフライン基本機能を確認
- [ ] 長時間の計時精度、画面スリープ・画面遷移時の挙動を追加検証

## Windows EXE版（正式配布保留）
- [x] GitHub Actionsでビルド、Windows実機で基本機能を確認
- [x] ソース静的監査とビルド証跡・安全な試験手順を作成（[監査報告](docs/security/WINDOWS_AUDIT.md)、[検証手順](docs/security/WINDOWS_VALIDATION.md)）
- [ ] SmartScreen警告とウイルスバスター検出の原因を調査（ATC25475の意味と旧EXEの由来は未確定）
- [ ] ソース・依存関係の安全性確認、ビルド方式の比較試験
- [ ] 安全性を確認したうえでGitHub ReleasesにEXEを掲載
