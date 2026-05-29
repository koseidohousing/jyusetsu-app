import os
import base64
import anthropic
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")

EXTRACTION_PROMPT = """あなたは不動産取引の専門家です。
添付されたPDFファイル（管理規約または重要事項に係る調査報告書）を精読し、
重要事項説明書の作成に必要な以下の項目を抽出してください。

【出力ルール】
- 各項目は必ず「項目」「内容」「参照元」の3つで出力してください。
- 参照元には、書類名と該当ページ番号または条文番号を記載してください（例：管理規約 第○条、調査報告書 p.3）。
- 書類に記載がない、または不明な項目については、絶対に推測せず「内容：記載なし」と記述してください。
- 金額・面積・日付・制限内容などの数値・条件は、原本の表現を尊重して正確に抜き出してください。
- 出力はMarkdown形式で、各項目を以下のテンプレートで統一してください。

【出力テンプレート（1項目ごと）】
### [項目名]
- **内容**：〇〇〇〇
- **参照元**：〇〇〇〇

---

【抽出する項目一覧】

### 1. 共用部分の範囲
### 2. 共用部分の持分の割合
### 3. 用途制限および制限の内容
### 4. ペットの飼育の制限および制限の内容
### 5. フローリングの制限および制限の内容
### 6. 楽器の使用の制限および制限の内容
### 7. 専用使用権に関する規約等の定め（名称・専用使用をなしうる者・専用使用料の有無とその帰属先）
### 8. 対象不動産に付随する専用使用権（名称・使用部分・面積・期間・料金等）
### 9. 駐車場の空き状況および料金
### 10. 駐輪場・バイク置場の空き状況および料金
### 11. 所有者が負担すべき費用を特定の者にのみ減免する旨の規約等の定め
### 12. 計画修繕積立金制度の有無
### 13. 修繕積立金の月額
### 14. すでに積み立てられている額（明確に会計が区分されている修繕積立金）
### 15. 修繕積立金の滞納の有無・当該一棟の建物に係る滞納額・専有部分に係る滞納額
### 16. 通常の管理費の月額
### 17. 管理費の滞納の有無・当該一棟の建物に係る滞納額・専有部分に係る滞納額
### 18. 修繕積立金・管理費以外の月額費用の有無および内容・滞納額
### 19. 管理組合の名称
### 20. 管理の形態（全部委託管理・一部委託管理・自主管理）
### 21. 管理委託先の内容（名称・電話番号・所在・マンション管理適正化法による登録番号）
### 22. 共用部分の維持修繕の実施状況の記録の有無および内容
### 23. 建物状況調査の実施の有無（有の場合は結果の概要）
### 24. アスベスト使用調査の有無
### 25. 耐震診断の有無
### 26. 特記事項（その他、買主に告知すべき重要な事項や独自のルール）

上記の項目を漏れなく、順番通りに出力してください。"""


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if APP_PASSWORD and not session.get("authenticated"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def encode_pdf(file_bytes: bytes) -> str:
    return base64.standard_b64encode(file_bytes).decode("utf-8")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == APP_PASSWORD:
            session["authenticated"] = True
            return redirect(url_for("index"))
        return redirect(url_for("login") + "?error=1")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template("index.html", password_enabled=bool(APP_PASSWORD))


@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    files = request.files.getlist("pdfs")
    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "PDFファイルをアップロードしてください"}), 400

    content_blocks = []
    file_names = []

    for f in files:
        if f.filename == "":
            continue
        pdf_bytes = f.read()
        b64 = encode_pdf(pdf_bytes)
        file_names.append(f.filename)
        content_blocks.append({
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": b64,
            },
            "title": f.filename,
        })

    content_blocks.append({
        "type": "text",
        "text": EXTRACTION_PROMPT,
    })

    try:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=8000,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": content_blocks}],
            betas=["pdfs-2024-09-25"],
        )

        result_text = ""
        for block in response.content:
            if block.type == "text":
                result_text = block.text
                break

        return jsonify({
            "result": result_text,
            "files": file_names,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        })

    except anthropic.APIError as e:
        return jsonify({"error": f"API エラー: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"エラー: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
