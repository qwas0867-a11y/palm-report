# 손금 리포트 프로토타입 (사진 → 개인 맞춤 PDF)

손 사진을 받아 "손금연구소 해나" 스타일의 개인 맞춤 PDF 리포트를 자동 생성하는
파이프라인의 최소 동작 버전입니다. **지금은 API 키가 없어도 바로 실행되는
목(mock) 모드로 세팅되어 있습니다.**

**v2 업데이트:** "손금 도사" 마스코트 캐릭터를 추가했습니다(이후 v3에서
브랜드 이미지로 교체). 표지 다음 페이지에 4컷 코믹 요약이 추가됐고, 각
손금선/특징/액션플랜 섹션마다 캐릭터가 말풍선으로 짧게 리액션합니다.

**v3 업데이트 (실제 API 연동 + 개인화 강화):**
- Anthropic API에 실제로 연결해서 끝까지 검증 완료. 실행 중 두 가지를
  고쳤습니다: ① 최신 모델이 추론(thinking) 단계를 먼저 거치며 답변이
  잘리는 문제 → 구조화 JSON 호출에서는 `thinking: disabled`로 끔.
  ② 모델이 가끔 JSON 문법을 살짝 틀리는 경우 → `json-repair`로 자동 복구.
- **점수 계산 로직 분리(버그 수정):** 처음엔 비전 API에게 "생명력/사고력"
  같은 6개 종합 점수까지 매기라고 시켰는데, 사진이 애매하면 모델이 전부
  0점으로 반환해버리는 문제가 있었습니다(실제 재현됨). 그래서 비전
  API는 관찰 가능한 사실(길이 비율, 두께 등)까지만 뽑고, 점수 계산은
  `src/scoring.py`가 결정론적 규칙으로 따로 계산하도록 분리했습니다.
  같은 입력이면 항상 같은 점수가 나오고 절대 0으로 죽지 않습니다.
- **캐릭터를 브랜드 이미지로 교체:** `assets/character/hana_emblem.png`
  (사용자가 준 손금 브랜드 로고를 원형으로 누끼 따서 투명 배경 처리).
  `src/make_mascot.py`로 그린 이전 도사 캐릭터는 `assets/mascot/`에
  남아있지만 현재 리포트에는 쓰이지 않습니다. 되돌리려면
  `src/pipeline.py`의 `mascot` 딕셔너리 경로만 바꾸면 됩니다.
- **개인화 항목 추가:** 나이(`age`), 성별(`gender`), 가장 궁금한 주제
  (`biggest_interest`: 연애/재물/직업/건강/전반적인 삶)를 입력받아 해당
  주제와 연결된 손금선 해설을 더 길고 구체적으로 씁니다. 성별은 문체나
  해석 내용에 영향을 주지 않도록(고정관념 방지) 프롬프트에 명시했습니다.
- **고객 입력 페이지 추가 (`templates/intake.html` + `app.py`):** 이름/
  나이/성별/관심사/고민 + 손 사진 업로드(왼손·오른손 필수, 클로즈업·
  손날 선택)를 받는 웹 폼과, 그 제출을 받아 파이프라인을 돌려 PDF를
  바로 다운로드시켜주는 아주 작은 Flask 서버입니다. 로컬에서는
  `python3 app.py` 후 http://localhost:8000 으로 확인할 수 있습니다.
  다만 **GitHub Pages는 정적 파일만 서빙하고 파이썬 서버를 못 돌리므로**,
  실제 손님을 받으려면 이 부분(`app.py`)만 Render/Railway/Fly.io 같은
  곳에 별도로 올려야 합니다. (에어컨 청소 안내 사이트는 그대로 GitHub
  Pages에 두고, 이 손금 리포트 서비스만 별도 도메인/서버로 운영하는
  구조를 추천합니다.)

## 지금 바로 실행해보기 (비용 없음)

```bash
pip install -r requirements.txt
python3 -m playwright install-deps   # 최초 1회, 시스템에 이미 있으면 생략 가능
python3 main.py
# -> output/palm_report_demo.pdf 생성됨
```

이 상태에서는 `ANTHROPIC_API_KEY`가 설정되어 있지 않기 때문에
`fixtures/sample_features.json`, `fixtures/sample_narrative.json`
(실제 API가 반환했을 법한 값을 미리 채워둔 예시 데이터)을 그대로 읽어
PDF를 만듭니다. 디자인·레이아웃·차트·PDF 변환이 전부 실제로 동작하는지
확인하는 용도입니다.

## 전체 파이프라인 구조

```
손 사진 4장                     구조화 JSON                리포트 문장 JSON
(정면x2,클로즈업,45도손날)          (좌표/비율/신뢰도)              (실제 페이지 문구)
     │                              │                            │
     ▼         [API 지점 1]         ▼        [API 지점 2]         ▼        (로컬 렌더링)
─────────►  src/vision_analysis.py ────►  src/narrative_generation.py ────►  src/render_pdf.py ──► PDF
            (Claude Vision 호출)          (Claude 텍스트 생성 호출)         (Jinja2+Playwright)
```

- **API 지점 1 — `src/vision_analysis.py`의 `analyze_palm_images()`**
  손 사진을 base64로 인코딩해 Anthropic Messages API(비전 지원 모델)에 보내고,
  "관찰 가능한 사실만 이 JSON 스키마로 답하라"는 시스템 프롬프트로 구조화된
  특징(손 유형, 6개 점수, 선별 길이비율/두께/신뢰도 등)을 받아옵니다.
- **API 지점 2 — `src/narrative_generation.py`의 `generate_narrative()`**
  1번의 결과 + 고객이 입력한 맥락(직업, 고민) + 코드에 내장된 전통 손금
  해석 요약(`PALMISTRY_KNOWLEDGE_BASE`)을 함께 Anthropic API에 보내
  실제 리포트 문장(관찰/해석/실행 팁 등)을 받아옵니다.
- 두 곳 다 `ANTHROPIC_API_KEY` 환경변수가 없으면 자동으로 `fixtures/`의
  예시 JSON을 반환하도록 분기되어 있습니다. **실제 서비스로 전환할 때는
  이 두 함수 안의 "목 모드 분기"만 지우면 됩니다(코드 구조는 이미 실제
  API 호출 코드가 들어가 있음).**

## 실제 API로 전환하는 방법

1. https://console.anthropic.com 에서 계정을 만들고 결제 수단을 등록한 뒤
   **Settings → API Keys**에서 키(`sk-ant-...`)를 발급받습니다.
2. `.env.example`을 `.env`로 복사해 키를 채우고 불러옵니다.
   ```bash
   cp .env.example .env
   # .env 파일의 ANTHROPIC_API_KEY= 뒤에 키를 붙여넣기
   export $(cat .env | xargs)
   ```
3. 실제 손 사진 4장을 준비해 실행합니다.
   ```bash
   python3 main.py --images left.jpg right.jpg closeup.jpg side.jpg \
                    --name "고객이름" --job "직업 맥락" --concern "고민"
   ```
   이제 `ANTHROPIC_API_KEY`가 감지되므로 두 함수 모두 실제 API를 호출합니다.

### 비용 감(대략치, 2026년 9월 기준 공식 문서 가격)

- Claude Sonnet 5: 입력 $2 / 출력 $10 (백만 토큰당)
- Claude Haiku 4.5: 입력 $1 / 출력 $5 (백만 토큰당, 비용을 더 낮추고 싶으면 이 모델로 교체 가능)
- 이미지 1장은 해상도에 따라 대략 수백~1,500 토큰 내외로 계산되는 것이 일반적입니다.
  사진 4장 + 프롬프트 + 응답 JSON을 합쳐도 리포트 1건당 입력 수천 토큰, 출력
  수천 토큰 수준이라 **리포트 1건에 실제로 드는 API 비용은 대략 수십 원~100원대**로
  추정됩니다(정확한 값은 실제 프롬프트 길이에 따라 달라지므로, 소량 테스트로
  직접 확인하는 것을 권장합니다). 최신 가격은 항상
  https://platform.claude.com/docs/en/about-claude/pricing 에서 재확인하세요.

## 폴더 구조

```
palm-report/
├── main.py                  # 실행 진입점
├── src/
│   ├── vision_analysis.py   # [API 지점 1]
│   ├── narrative_generation.py  # [API 지점 2]
│   ├── chart.py             # 레이더 차트(6각) 생성
│   ├── render_pdf.py        # HTML→PDF (Playwright)
│   └── pipeline.py          # 전체 오케스트레이션
├── templates/report.html.j2 # 리포트 디자인(HTML/CSS)
├── fixtures/                # API 키 없을 때 쓰는 예시 데이터
├── assets/                  # 데모용 샘플 손 이미지(프로그램으로 생성, 실제 사진 아님)
└── output/                  # 생성된 PDF
```

## 아직 안 만든 것 (다음 단계)

- 고객이 사진 4장 + 이름/직업/고민을 올리는 업로드 폼(웹페이지)
- 결제 연동, 자동 발송(이메일/카카오톡)
- 사진 30일 후 자동 삭제 같은 개인정보 처리 로직
- 실제 손금선 좌표를 사진 위에 색깔로 그려주는 오버레이 렌더링
  (지금은 데모 이미지 자체에 선이 미리 그려진 상태로 대체됨)
