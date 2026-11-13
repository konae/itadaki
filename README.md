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

## 今後の設定
Bluehostへの本番転送、ChatGPTから本番公開を起動する接続、Drive・Notion自動同期はまだ設定していません。
今後の本番転送では、確認したコミットと同じファイルを使用します。本番転送対象はHTML・CSS・画像・faviconです。

## 公開前の確認事項
トップとおにぎり作りの写真には、たたき台のサンプルが残っています。
料理一覧3枚はお店の写真に差し替え済みです。おにぎり原本：https://drive.google.com/file/d/1JwYWIko9GXo3jvrYaGWMns6r_K_z8GV-/view
カレーはメニュー素材08-pork-katsu-curry.jpg、オムライスはメニュー素材06-pork-katsu-served-on-omurice.pngを使用しています。営業時間は未確認です。
Featured DishはPork Katsu Classic Omurice（$21.95）。料理名・説明・価格の根拠はフードメニューr18のPork Katsu Classicです。特集には既存のカツのせオムライス写真を使用しています。
本番では確認用のnoindex・robots.txtを見直します。

たたき台: https://cafe-itadaki-clean.michiya65371.chatgpt.site/
