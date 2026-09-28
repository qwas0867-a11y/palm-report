"""
[API 연결 지점 1] 손 사진 -> 구조화된 손금 특징(JSON)

여기서 하는 일:
  1) 고객이 올린 손 사진 파일들을 base64로 인코딩한다.
  2) Anthropic Messages API(비전 지원 모델)에 사진 + "이런 JSON 스키마로만 답하라"는
     프롬프트를 함께 보낸다.
  3) 모델이 돌려준 텍스트를 JSON으로 파싱해서 반환한다.

ANTHROPIC_API_KEY 환경변수가 없으면(=아직 키를 발급받기 전이면)
fixtures/sample_features.json 을 그대로 읽어 반환하는 '목 모드'로 동작한다.
실제 서비스로 넘어갈 때는 이 파일 안의 목 모드 분기만 지우면 된다.
"""
import base64
import json
import os
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"

# 실제 API에 보낼 시스템 프롬프트. 손금 지식 자체를 여기 다 넣지 않고,
# "무엇을 관찰해서 어떤 스키마로 뽑아낼지"만 지시한다. (해석 문장은 다음 단계인
# narrative_generation.py 에서 별도 지식베이스와 함께 생성한다 - 역할 분리)
VISION_SYSTEM_PROMPT = """\
당신은 손 사진에서 손금(주요 손금선)의 위치와 형태적 특징만을 관찰하는
이미지 분석기입니다. 점을 치거나 해석하지 말고, 관찰 가능한 사실만 아래 JSON
스키마로 출력하세요. 확신이 낮으면 confidence 값을 낮게, 애매하면 "판단 어려움"
이라고 정직하게 표기하세요. 출력은 JSON 하나만, 다른 텍스트 없이.

참고: 0~100점 같은 종합 점수는 요청하지 않습니다. 관찰 가능한 형태 정보만
정확하게 채우세요(점수 매기기는 별도 로직이 처리합니다).

스키마:
{
  "hand_shape": {"type": str, "palm_width_to_length_ratio": float, "finger_to_palm_ratio": float},
  "lines": {
    "life":  {"length_ratio": float, "thickness": str, "breaks": int, "confidence": str},
    "head":  {"length_ratio": float, "slope": str, "end_split": bool, "confidence": str},
    "heart": {"length_ratio": float, "branching": str, "confidence": str},
    "fate":  {"break_points": [str], "confidence": str},
    "sun":   {"length_ratio": float, "confidence": str},
    "money": {"count": int, "length_ratio": float, "confidence": str}
  },
  "timeline_segments": [{"age_range": str, "label": str, "basis": str}]
}
"""


def _encode_image(path: Path) -> dict:
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    media_type = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": data},
    }


def analyze_palm_images(image_paths: list[str], model: str = "claude-sonnet-5") -> dict:
    """
    image_paths: [왼손 정면, 오른손 정면, 주 사용 손 클로즈업, 45도 손날] 사진 경로 리스트
    반환: VISION_SYSTEM_PROMPT 스키마와 동일한 구조의 dict
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        # --- 목(mock) 모드: API 키가 없을 때 데모용 데이터를 그대로 반환 ---
        with open(FIXTURES / "sample_features.json", encoding="utf-8") as f:
            return json.load(f)

    # --- 실제 API 호출 (키가 있을 때만 이 경로를 탄다) ---
    import anthropic  # pip install anthropic

    client = anthropic.Anthropic(api_key=api_key)

    content = [_encode_image(Path(p)) for p in image_paths]
    content.append({
        "type": "text",
        "text": "위 손 사진들을 관찰해서 지시된 JSON 스키마로만 답하세요.",
    })

    resp = client.messages.create(
        model=model,                 # 예: "claude-sonnet-5" (발급 시점의 최신 모델 ID는 docs.claude.com/en/docs/about-claude/models 에서 확인)
        max_tokens=3000,
        thinking={"type": "disabled"},  # 구조화 JSON 출력만 필요하므로 추론 단계는 끔(토큰 절약)
        system=VISION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    from src.util import extract_json, response_text
    return extract_json(response_text(resp))
