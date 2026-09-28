"""
6개 지표(생명력/사고력/감정/재물/직업운/인연) 점수 계산.

주의: 이 점수는 비전 API가 직접 매기지 않는다. "생명력이 몇 점이냐"는 이미
해석이 섞인 판단이라, 비전 모델에게 시키면 확신이 없을 때 전부 0으로
반환해버리는 문제가 있었다(실제로 도식화된 샘플 이미지에서 이 현상이
재현됨). 그래서 비전 API는 "관찰 가능한 사실"(길이 비율, 두께, 갈래 수 등)
까지만 뽑고, 그 사실을 0~100 점수로 바꾸는 건 여기 코드가 결정론적으로
계산한다. 같은 입력이면 항상 같은 점수가 나오고, 절대 0으로 죽지 않는다.
"""

CONF_WEIGHT = {"확신": 1.0, "보통": 0.85, "낮음": 0.7, "참고": 0.6}


def _conf(line: dict) -> float:
    c = str(line.get("confidence", "보통"))
    for key, w in CONF_WEIGHT.items():
        if key in c:
            return w
    return 0.75


def _clip(v, lo=15, hi=95):
    return max(lo, min(hi, round(v)))


def compute_scores(lines: dict) -> dict:
    life = lines.get("life", {})
    head = lines.get("head", {})
    heart = lines.get("heart", {})
    fate = lines.get("fate", {})
    sun = lines.get("sun", {})
    money = lines.get("money", {})

    # 생명력: 생명선 길이비율 + 두께 보너스
    thick_bonus = 10 if "굵" in str(life.get("thickness", "")) or "두꺼" in str(life.get("thickness", "")) else 0
    vitality = 40 + life.get("length_ratio", 0.6) * 60 * _conf(life) + thick_bonus

    # 사고력: 두뇌선 길이비율
    thinking = 35 + head.get("length_ratio", 0.6) * 70 * _conf(head)

    # 감정: 감정선 길이비율 (너무 길지도 짧지도 않은 중간을 선호하는 대신,
    # 단순화를 위해 길이에 비례 + branching이 있으면 표현력 보너스)
    branch_bonus = 8 if "갈래" in str(heart.get("branching", "")) or heart.get("branching") not in (None, "", "관찰되지 않음(단일 선)") else 0
    emotion = 40 + heart.get("length_ratio", 0.6) * 55 * _conf(heart) + branch_bonus

    # 재물: 재물선 개수 + 길이비율
    money_score = 30 + money.get("count", 1) * 8 + money.get("length_ratio", 0.1) * 100
    money_score = min(money_score, 90)

    # 직업운: 운명선이 뚜렷할수록(끊긴 지점이 적을수록) 높게
    breaks = len(fate.get("break_points", []) or [])
    career = 70 - breaks * 10
    career = max(35, career)

    # 인연: 감정선 + 태양선(가벼운 보조 지표)을 함께 반영
    bonds = 45 + heart.get("length_ratio", 0.6) * 40 + sun.get("length_ratio", 0.1) * 30

    return {
        "생명력": _clip(vitality),
        "사고력": _clip(thinking),
        "감정": _clip(emotion),
        "재물": _clip(money_score),
        "직업운": _clip(career),
        "인연": _clip(bonds),
    }
