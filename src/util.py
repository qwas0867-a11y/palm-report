"""공용 유틸: API 응답 텍스트에서 JSON만 안전하게 뽑아낸다.
(모델이 ```json 코드블록으로 감싸거나 앞뒤에 설명을 붙이는 경우가 있어 방어적으로 처리)
"""
import json
import re


def response_text(resp) -> str:
    """Anthropic 응답의 content 블록 중 실제 텍스트 블록만 골라 이어붙인다.
    (extended thinking이 켜져 있으면 content[0]이 ThinkingBlock이라 .text가 없음)"""
    parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
    return "\n".join(parts)


def extract_json(text: str) -> dict:
    text = text.strip()
    # ```json ... ``` 또는 ``` ... ``` 코드펜스 제거
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    else:
        # 첫 '{' 부터 마지막 '}' 까지만 추출 (앞뒤 설명 문구 방어)
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # LLM이 만든 JSON에 흔한 실수(이스케이프 안 된 따옴표, 트레일링 콤마 등)를
        # json_repair 라이브러리로 복구 시도
        from json_repair import repair_json
        return json.loads(repair_json(text))
