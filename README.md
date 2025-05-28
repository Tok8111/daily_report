# 業務日報作成アプリ

## 📌 概要

このアプリは、就労移行支援・就労継続A型支援事業所に通う利用者が、日々の業務内容や体調を記録・提出できるWebアプリです。記録内容は職員によって確認・フィードバックが可能です。

## 🧑‍💼 主なユーザー

| ユーザー | 主な操作内容 |
|----------|--------------|
| 利用者   | 業務終了後に日報を入力・確認 |
| 職員     | 利用者の日報を確認し、コメントを入力 |

## ✨ 主な機能

- 利用者向け
  - ログイン
  - 日報の入力（出退勤時間、体調、作業内容、コメント）
  - 職員が入力したコメントを閲覧
  
- 職員向け
  - ログイン
  - 利用者ごとの日報一覧表示
  - 職員コメントの入力

## 🛠 使用技術

| 項目 | 使用技術 |
|-|-|
| フロントエンド | HTML / CSS / JavaScript |
| バックエンド | Python (Flask) |
| データベース | SQLite |
| 開発環境 | VSCode (ローカル開発) |
| バージョン管理 | Git / GitHub |
| その他 | Jinja2テンプレート、Flask-Session |

## 🚀 セットアップ方法

```
1. Pythonと必要なパッケージをインストール
pip install flask

2. データベースを初期化
python init_db.py

3. アプリを起動
python app.py

4. ブラウザで以下にアクセス
http://127.0.0.1:5000/
```

※ ユーザーアカウント情報は `init_db.py` にて仮登録済

## 📂 ディレクトリ構成

```plaintext
production_training/
├── app.py                         Flask アプリ本体
│
├── init_db.py                     データベース初期化、テーブル作成ファイル
│
├── your_database.db               データベース(テーブル:users、reports、report_tasks)
│
├── static/                        静的ファイル(CSS)
│   └── style.css                  スタイルシート
│
├── templates/                     HTMLファイル
│   ├── login.html                 G1.ログイン画面
│   ├── login_failure.html         G2.ログイン失敗画面
│   ├── main.html                  G3.メイン画面
│   ├── daily_report_input.html    G4.日報入力画面(利用者のみ閲覧可)
│   ├── report_list.html           G5.日報一覧画面(職員のみ閲覧可)
│   └── logout.html                G6.ログアウト画面
│
├── document/                      ドキュメントファイル
│   ├── class_diagram              クラス図
│   ├── data_structure             データ構造
│   ├── display_draft              画面設計ドラフト
│   ├── er_diagram                 ER図
│   ├── requirements               要求定義書
│   ├── screen_transition_diagram  画面遷移図
│   └── wire_frame                 ワイヤーフレーム
│
└── README.md                      プロジェクトの説明
```

## 🗓 開発スケジュール

| 日付(目安) | 作業内容 |
|-|-|
| 1日目（2025年5月15日） | 要件定義・画面設計 |
| 2日目（2025年5月16日） | 画面デザイン |
| 3日目（2025年5月20日） | ログイン機能、日報投稿画面の実装 |
| 4日目（2025年5月21日） | 日報の閲覧機能の実装 |
| 5日目（2025年5月22日） | 職員側の機能（一覧表示、コメント入力）実装 |
| 6日目（2025年5月23日） | UI調整・スマホ対応 |
| 7日目（2025年5月26日） | 動作確認・バグ修正 |
| 8日目（2025年5月27日） | ドキュメント(マニュアル)作成・発表資料作成/準備 |
| 9日目（2025年5月28日） | （バッファ） |

## 📄 詳細資料
- 要件定義書：document/requirements/requirements.md
- ER図：document/er_diagram/er_diagram.png
- 画面遷移図：document/screen_transition_diagram/screen_transition.png
- ワイヤーフレーム：document/wire_frame/

## 📝 ライセンス
本プロジェクトは2025年1月～5月の職業訓練課程における教育・研修目的でのみ利用されます。
商用利用・転載はご遠慮ください。

## 🙏 THANKS
本アプリは「Java＋Pythonプログラマー養成科(2025年1月開講)」制作実習の一環として作成されました。
