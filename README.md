# 重要事項説明書 作成支援ツール

管理規約・重要事項に係る調査報告書のPDFをアップロードするだけで、重要事項説明書に必要な26項目を自動抽出するWebアプリです。

---

## 公開URLで使えるようにする手順（Render.com）

一度設定すれば、URLを共有するだけで誰でも使えるようになります。

---

### Step 1：GitHubにコードをアップロードする

1. [GitHub](https://github.com/) にアクセスし、アカウントを作成（または既存のアカウントでログイン）
2. 右上の「＋」→「New repository」をクリック
3. Repository name に `jyusetsu-app` と入力し、「Create repository」をクリック
4. 作成されたページの指示に従い、このフォルダのファイルをアップロード
   - 「uploading an existing file」リンクをクリック
   - このフォルダの中のファイルをすべてドラッグ＆ドロップ（`.env` ファイルは**アップロードしない**）
   - 「Commit changes」をクリック

---

### Step 2：Render.com でアプリを公開する

1. [Render.com](https://render.com/) にアクセスし、「Get Started for Free」でアカウント作成（GitHubアカウントでログイン可）
2. ダッシュボードで「New +」→「Web Service」をクリック
3. 「Connect a repository」で先ほど作成した `jyusetsu-app` を選択し「Connect」
4. 以下の項目を確認・入力：
   - **Name**：任意（例：`jyusetsu-app`）
   - **Region**：`Singapore` または `Oregon` を選択
   - **Branch**：`main`
   - **Build Command**：`pip install -r requirements.txt`
   - **Start Command**：`python app.py`
   - **Instance Type**：`Free`（無料）を選択
5. 「Advanced」を開き、「Add Environment Variable」で以下を追加：

   | Key | Value |
   |-----|-------|
   | `ANTHROPIC_API_KEY` | あなたのAnthropicのAPIキー |
   | `APP_PASSWORD` | アプリに設定したいパスワード（任意の文字列） |

6. 「Create Web Service」をクリック

---

### Step 3：URLを共有する

デプロイが完了すると（5〜10分程度）、以下のような形式のURLが発行されます：

```
https://jyusetsu-app-xxxx.onrender.com
```

このURLとパスワードを共有するだけで、誰でもどこからでも使えます。

> **注意：** 無料プランはしばらく使われないとスリープします。最初のアクセスから起動まで1〜2分かかる場合があります。

---

## コードを更新したいとき

GitHubのリポジトリにファイルをアップロードし直すと、Renderが自動的に再デプロイします。

---

## 料金の目安

- **Render.com**：無料プランで利用可能
- **Anthropic API**：1回の分析で約 $0.10〜$0.50 程度（PDF枚数・内容による）

---

## ローカルで動かしたい場合

```bash
pip install -r requirements.txt
# .env ファイルを作成してAPIキーを記入
python app.py
# → http://localhost:5000 で起動
```
