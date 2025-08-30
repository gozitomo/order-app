# order-app
# 注文アプリ
このアプリケーションは、農園の業務効率化を目的とした業務用注文Webアプリです。

## 概要
農園では、スーパーや飲食店からの注文をLINEやメールで受け付けており、情報が複数の場所に散在し、管理が複雑になるという課題がありました。この問題を解決するため、スタッフ全員がリアルタイムで注文状況を確認できる一元管理システムとして、本アプリを開発しました。

## 主な機能
注文管理：新規注文の登録、既存注文の編集、削除が可能です。

顧客管理：取引先の情報（連絡先、配送先など）を一元管理します。

注文状況の可視化：注文ステータス（受付済み、発送済みなど）を一覧で確認できます。

## 使い方
アプリケーションにログインします。

ダッシュボードで、現在の注文状況を確認できます。

新しい注文が入った場合は、「新規注文作成」ボタンから詳細を入力し、登録します。

注文内容に変更があった場合は、該当する注文を選択し、編集・更新します。

## 開発環境
フロントエンド：javascript

バックエンド：Django

データベース：SQLite3

## セットアップ方法

### 1.リポジトリをクローンします。

```bash
git clone https://github.com/gozitomo/order-app.git
cd order-app
```

### 2.Djangoセットアップ

```bash
pip install -r requirements.txt
python manage.py migrate
```

### 3.データベースの初期設定
アプリの管理ユーザーを作成

```bash
python create_superuser.py
```

### 商品データの登録

```bash
python create_initial_products.py
```

### ユーザーグループの登録

```bash
python create_initial_usergroup.py
```

### 4.サーバーを起動します
```bash
python manage.py runserver
```