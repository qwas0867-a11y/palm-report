"""전체 파이프라인: 사진 -> (비전 API) -> (문장 API) -> 차트 -> PDF."""
import datetime
import random
from pathlib import Path

from src.vision_analysis import analyze_palm_images
from src.narrative_generation import generate_narrative
from src.chart import render_radar_png
from src.scoring import compute_scores
from src.render_pdf import render_html, html_to_pdf

ROOT = Path(__file__).resolve().parent.parent


def run(image_paths: list[str], customer: dict, out_pdf: str):
    # 1) [API 지점 1] 사진 -> 구조화 특징(원본 손금 API가 점수까지 매기면
    #    확신이 없을 때 전부 0으로 반환하는 문제가 있어, 점수는 항상 여기서
    #    별도로 결정론적으로 계산한다 - src/scoring.py 참고)
    features = analyze_palm_images(image_paths)
    features["scores"] = compute_scores(features.get("lines", {}))

    # 2) [API 지점 2] 특징 + 고객 맥락 -> 리포트 문장
    narrative = generate_narrative(features, customer)

    # 3) 레이더 차트 이미지 생성 (로컬 계산, API 아님)
    radar_png = render_radar_png(features["scores"])

    # 4) HTML 렌더링 -> PDF 변환
    context = {
        "customer": customer,
        "features": features,
        "narrative": narrative,
        "radar_png": radar_png,
        "sample_image": str(ROOT / "assets" / "sample_right.jpg"),
        "mascot": {name: str(ROOT / "assets" / "character" / "hana_emblem.png")
                   for name in ["greeting", "thinking", "wow", "cheer"]},
        "report_no": datetime.date.today().strftime("%Y%m%d") + f"-{random.randint(1000,9999)}",
        "issue_date": datetime.date.today().strftime("%Y. %m. %d."),
    }
    html = render_html(context)
    html_to_pdf(html, out_pdf)
    return out_pdf
