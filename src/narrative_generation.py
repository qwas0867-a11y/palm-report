"""
[API 연결 지점 2] 구조화된 특징(JSON) + 고객 정보 -> 리포트에 들어갈 실제 문장

vision_analysis.py 가 "관찰된 사실"만 뽑아냈다면, 이 파일은 그 사실을
1) 전통 손금 해석 지식(KNOWLEDGE_BASE) 과 연결하고
2) 고객이 설문에서 준 맥락(직업, 고민)을 반영해서
자연스러운 한국어 문장으로 바꾸는 역할을 한다. (역할을 분리해두면 나중에
지식베이스만 바꿔도 되고, 사진 인식 모델만 바꿔도 되므로 유지보수가 쉬워진다.)

ANTHROPIC_API_KEY 가 없으면 fixtures/sample_narrative.json 을 그대로 반환한다.
"""
import json
import os
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"

# 실제 서비스에서는 이 부분을 훨씬 두껍게(수십~수백 KB) 만들어서
# 파일이나 벡터DB로 관리하고 RAG로 필요한 부분만 프롬프트에 넣는 것을 권장한다.
# 지금은 프로토타입이라 프롬프트에 직접 박아 넣은 '요약본' 형태로 둔다.
PALMISTRY_KNOWLEDGE_BASE = """\
- 생명선: 굵고 끊김 없이 길면 체력 회복이 빠름. 손목 쪽에서 갈라지면 후반부 방향 전환.
- 두뇌선: 길고 손날쪽으로 완만히 하강하면 계획형+창의형 결합. 끝이 갈라지면 다관점 사고,
  단 결정 지연 가능성. 시작점이 생명선과 붙어 있으면 신중형.
- 감정선: 검지 쪽까지 이어지면 이상 추구형 애정관, 중지 아래서 끝나면 현실형.
  끝이 여러 갈래면 표현을 아끼고 상대를 배려하는 경향.
- 운명선: 손목에서 곧게 올라오면 자기 힘으로 방향을 세운 삶. 중간에 흐려졌다 다시
  짙어지면 진로/업종 전환 경험. 두뇌선 높이에서 얇아지는 것은 재구조화 시기.
- 재물선(새끼손가락 아래 잔금): 굵고 한 줄이면 안정적 단일 수입원, 가늘고 여러
  갈래면 다수입원이거나 지출 통로가 분산된 상태.
- 태양선: 짧고 위쪽에만 있으면 인정이 늦게 따라오는 대기만성형.
"""

NARRATIVE_SYSTEM_PROMPT = f"""\
당신은 손금연구소 '해나' 톤으로 리포트를 쓰는 카피라이터입니다.
아래 전통 손금 해석 지식을 참고하되, 절대 확정적 예언처럼 쓰지 말고
"~한 편입니다", "~로 읽힙니다" 같은 관찰/해석 어조를 씁니다.
의학적 판단, 확정적 미래 예측, 불안을 조장하는 표현은 금지합니다.
고객의 직업/고민 맥락이 주어지면 그 맥락에 맞는 구체적 예시(예: 사업 미팅,
거래처, 지출 관리)를 문장에 자연스럽게 녹여 개인화하세요.

[개인화 입력값 활용 방법]
- age(나이): 타임라인 페이지의 현재 구간을 짚어주고, 실행 팁의 시간 단위나
  생활 맥락(예: 20대 초반이면 "이직/첫 창업", 40대면 "확장/승계")을 나이대에
  맞게 조정하세요.
- biggest_interest(가장 궁금한 주제 - 연애/재물/직업/건강/전반적인 삶 중 하나):
  이 주제와 직접 연결되는 손금선(연애→감정선·결혼선, 재물→재물선·금성대,
  직업→운명선·두뇌선, 건강→생명선·건강선)의 observation/interpretation을
  더 길고 구체적으로 쓰고, closing 문단도 이 주제를 중심으로 마무리하세요.
  다른 선은 기존 분량대로 짧게 유지해 대비를 주세요.
- gender(성별): 문체나 호칭에 영향을 주지 않습니다(한국어 리포트 톤은 성별
  중립을 유지). 성별에 따라 성격이나 능력을 다르게 단정짓는 표현, 고정관념적
  묘사는 절대 쓰지 마세요. gender는 참고만 하고 실제 해석 내용을 바꾸지
  않는 것이 원칙입니다.

[전통 손금 해석 지식]
{PALMISTRY_KNOWLEDGE_BASE}

리포트에는 '손금 도사' 마스코트 캐릭터가 함께 등장합니다. 아래 필드에는
캐릭터가 실제로 말하듯 짧고 구어체로("~네요", "~군요", "~할게요") 한 줄만
쓰세요(진지한 해석 문장과 톤을 분리합니다):
  - comic: [{{"mascot": "greeting|thinking|wow|cheer", "text": str}}] 4개
    (인사 -> 생각 -> 놀람/발견 -> 응원 순서)
  - lines.<life|head|heart>.mascot_note: 각 선에 대한 한 줄 코멘트
  - mascot_distinctive, mascot_action: 각각 한 줄 코멘트

출력은 지정된 JSON 스키마로만 하세요.
"""


def generate_narrative(features: dict, customer: dict, model: str = "claude-sonnet-5") -> dict:
    """
    features: vision_analysis.analyze_palm_images() 의 반환값
    customer: {"name": str, "job_context": str, "concern": str}
    반환: 리포트 템플릿이 그대로 꽂아 쓸 수 있는 문장 JSON
          (fixtures/sample_narrative.json 과 동일한 구조)
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        with open(FIXTURES / "sample_narrative.json", encoding="utf-8") as f:
            return json.load(f)

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    # 모델이 실제로 어떤 키/구조로 응답해야 하는지 예시 JSON 자체를 보여준다
    # (파일 경로만 알려주면 모델이 그 파일을 열어볼 수 없으므로 반드시 내용을 넣어야 함)
    with open(FIXTURES / "sample_narrative.json", encoding="utf-8") as f:
        schema_example = json.load(f)
    schema_example.pop("_comment", None)

    user_payload = {
        "customer": customer,
        "features": features,
        "instruction": "아래 output_schema_example과 완전히 동일한 키 구조로, "
                        "내용만 features/customer에 맞게 새로 써서 JSON으로만 답하세요. "
                        "코드블록이나 설명 문구 없이 JSON 객체 하나만 출력하세요.",
        "output_schema_example": schema_example,
    }

    resp = client.messages.create(
        model=model,
        max_tokens=8000,
        thinking={"type": "disabled"},  # 구조화 JSON 출력만 필요하므로 추론 단계는 끔(토큰 절약)
        system=NARRATIVE_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": json.dumps(user_payload, ensure_ascii=False),
        }],
    )

    from src.util import extract_json, response_text
    return extract_json(response_text(resp))
