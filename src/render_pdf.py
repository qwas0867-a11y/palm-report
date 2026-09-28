"""HTML 템플릿 + 데이터 -> 최종 PDF. Playwright(크로미움)로 인쇄한다.

실행 환경에 따라 크로미움 실행 파일 위치가 다를 수 있어(이 개발 샌드박스와
실제 배포 서버가 다름), 기본은 Playwright가 알아서 찾게 두고, 필요할 때만
PLAYWRIGHT_CHROMIUM_PATH 환경변수로 경로를 지정할 수 있게 했다.
"""
import os
import uuid
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"


def render_html(context: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
    template = env.get_template("report.html.j2")
    return template.render(**context)


def html_to_pdf(html: str, out_path: str):
    # 요청마다 고유한 임시 파일을 써서, 동시에 여러 명이 리포트를 요청해도
    # 서로의 임시 HTML을 덮어쓰지 않게 한다.
    tmp_dir = ROOT / "output"
    tmp_dir.mkdir(exist_ok=True)
    tmp_html = tmp_dir / f"_render_{uuid.uuid4().hex}.html"
    tmp_html.write_text(html, encoding="utf-8")

    launch_kwargs = {"args": ["--no-sandbox"]}
    custom_path = os.environ.get("PLAYWRIGHT_CHROMIUM_PATH")
    if custom_path:
        launch_kwargs["executable_path"] = custom_path

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(**launch_kwargs)
            page = browser.new_page()
            page.goto(f"file://{tmp_html}")
            page.pdf(
                path=out_path,
                width="820px",
                height="1060px",
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
            browser.close()
    finally:
        tmp_html.unlink(missing_ok=True)
