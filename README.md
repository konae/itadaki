# Café Itadaki — ホームページ編集元

ビルド不要の静的HTML・CSSサイト。画像を含め、たたき台から取得して整理しました。

## 編集箇所
- `index.html`：文章、営業時間、メニュー、リンク、画像の指定
- `styles.css`：デザインとスマートフォン表示
- `*.png`：ロゴと仮の写真

## 確認方法
```sh
python3 check_site.py
python3 -m http.server 8080 --bind 127.0.0.1
```
ブラウザで http://127.0.0.1:8080 を開きます。

## GitHubの確認用サイト
Settings → Pages → Build and deploymentで、Deploy from a branch、main、/(root)を選びます。
mainの更新に合わせてGitHub Pagesが確認用サイトを更新します。
通常、確認ページはインターネットから閲覧できます。noindexとrobots.txtはアクセス制限ではありません。

## 本番公開と今後の設定
2026年11月13日にBluehostへFTPSで本番公開済みです。本番の掲載内容はf395cd6を基準とし、検索除外の解除とindex.htmlの優先設定を適用しています。公開前に上書き対象をローカルへ非公開でバックアップしています。
GitHubからBluehostへの公開処理は設定・動作確認済みです。確認した版の完全なSHAを.publication-request.jsonに保存すると、本番転送のGitHub Actionsが実行されます。通常の編集は本番転送を起動しません。詳しくは[公開処理の説明](automation/README.md)を参照してください。検証成功：https://github.com/konae/itadaki/actions/runs/43429582596
オーナーの共有PJへの参加・接続からの一連の操作は未確認です。Notionは未接続です。素材のDrive保存はAIの編集手順に組み込み、店舗写真・掲載画像・メニュー資料を保存済みです。
本番転送では、確認したコミットと同じ内容を使用し、本番固有の設定差分を記録します。本番転送対象はHTML・CSS・掲載画像・favicon・robots.txtおよび必要なサーバー設定です。仕様書や原本・バックアップは転送しません。

## 公開前の確認事項
HEROはユーザー提供の実店舗写真から、AIで着席しているお客さん2名を除去した hero-cafe-interior-no-customers.jpg を使用しています。カウンター内のスタッフは残しています。原本は hero-cafe-interior.jpg です。
おにぎり作りの写真には、たたき台のサンプルが残っています。
料理一覧3枚はお店の写真をもとに、AIで背景と光をそろえた補正案を使用しています。
掲載用はomurice-plain-retouched.jpg、curry-retouched.jpg、ramen-retouched.jpg。原本は残しています。おにぎり原本：（共有Driveの場所は非公開の引き継ぎ資料を参照）
カレー原本はメニュー素材08-pork-katsu-curry.jpg。ラーメン原本は共有Driveの12-2 Spicy Chashu Miso_Angle.pngです：
（共有Driveの場所は非公開の引き継ぎ資料を参照）
元写真の辛味噌トッピングも残しています。営業時間はドリンク・デザートメニューv28に合わせ、日〜金9:00〜17:30（L.O.17:00）、土9:00〜19:30（L.O.19:00）に修正済みです。
Featured DishはPork Katsu Classic Omurice（$21.95）。料理名・説明・価格の根拠はフードメニューr18のPork Katsu Classicです。特集には既存のカツのせオムライス写真を使用しています。
確認サイトでは検索除外を維持し、本番ではnoindexを外しrobots.txtでクロールを許可済みです。

たたき台: https://cafe-itadaki-clean.michiya65371.chatgpt.site/

料理一覧はオムライス・カレー・ラーメンの順です。オムライスはカツなしの写真を使用し、原本は共有Driveの10-3 Classic Omurice Plain_Angle.pngです：
（共有Driveの場所は非公開の引き継ぎ資料を参照）

## オーナー向け引き継ぎ

- [サイト仕様書](site-specification.md)
- [編集と公開の手順](owner-editing-guide.md)
