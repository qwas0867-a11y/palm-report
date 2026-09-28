"""
고객이 브라우저에서 사진 + 정보를 입력하면 -> 파이프라인을 돌려서 -> PDF를
바로 다운로드해주는 아주 작은 웹 서버.

로컬에서 확인:
  python3 app.py
  브라우저에서 http://localhost:8000 접속

실제로 손님을 받으려면 이 파일을 Render/Railway/Fly.io 같은 곳에 올려서
공개 URL을 만들어야 합니다(GitHub Pages는 정적 파일만 되고 파이썬 서버를
못 돌리므로, 지금 만들고 계신 에어컨 청소 안내 사이트와는 별도로 이 부분만
따로 호스팅해야 합니다).
"""
import tempfile
import uuid
from pathlib import Path

from flask import Flask, request, render_template, send_file, jsonify

from src.pipeline import run

ROOT = Path(__file__).resolve().parent
UPLOADS = ROOT / "uploads"
UPLOADS.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 사진 4장 기준 넉넉히 25MB 제한


@app.route("/")
def intake_form():
    return render_template("intake.html")


@app.route("/generate", methods=["POST"])
def generate():
    try:
        job_id = uuid.uuid4().hex[:10]
        job_dir = UPLOADS / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        image_paths = []
        for field in ["img_left", "img_right", "img_closeup", "img_side"]:
            f = request.files.get(field)
            if f and f.filename:
                dest = job_dir / f"{field}{Path(f.filename).suffix or '.jpg'}"
                f.save(dest)
                image_paths.append(str(dest))

        if len(image_paths) < 2:
            return jsonify({"error": "왼손/오른손 정면 사진은 필수입니다."}), 400

        customer = {
            "name": request.form.get("name", "고객"),
            "age": int(request.form.get("age") or 0),
            "gender": request.form.get("gender", "선택 안 함"),
            "biggest_interest": request.form.get("interest", "전반적인 삶"),
            "concern": request.form.get("concern", ""),
        }

        out_pdf = job_dir / "palm_report.pdf"
        run(image_paths, customer, str(out_pdf))

        return send_file(out_pdf, as_attachment=True,
                          download_name=f"손금리포트_{customer['name']}.pdf")

    except Exception as e:
        app.logger.exception("리포트 생성 실패")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # debug=True(자동 재시작)는 업로드/PDF 생성처럼 파일을 쓰는 요청 도중에
    # 서버가 재시작되며 응답이 끊길 수 있어 꺼둔다.
    app.run(host="0.0.0.0", port=8000, debug=False)
