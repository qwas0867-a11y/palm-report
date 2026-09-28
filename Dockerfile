# Render(또는 다른 Docker 호스팅)용 배포 이미지.
# Playwright가 실제로 쓰는 크로미움 + 필요한 시스템 라이브러리까지
# 이 안에서 전부 설치하므로, 호스팅 쪽에서 별도 설정 없이 그대로 빌드하면 된다.
FROM python:3.11-slim

WORKDIR /app

# 폰트(한글 깨짐 방지) + Playwright 설치에 필요한 최소 도구
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 크로미움 브라우저 + 실행에 필요한 시스템 종속성을 함께 설치
RUN playwright install --with-deps chromium

COPY . .

# Render는 PORT 환경변수로 포트 번호를 넘겨준다
ENV PORT=8000
EXPOSE 8000

# 리포트 1건 생성에 1~2분 걸릴 수 있어 워커 타임아웃을 넉넉히 잡는다
CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 180 --workers 2
