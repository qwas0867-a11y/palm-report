"""
'손금 도사' 마스코트 캐릭터를 플랫 벡터 스타일로 직접 그려서
표정/포즈별 PNG(투명 배경)로 저장한다. 외부 이미지 생성 API 없이
PIL만으로 그리므로 비용이 들지 않고, 캐릭터가 항상 100% 동일하게
재현된다(생성형 이미지 모델의 '캐릭터 일관성 문제'가 원천적으로 없음).

표정 4종:
  greeting  - 인사(기본, 표지용)
  thinking  - 생각(해석 문장 옆)
  wow       - 놀람/감탄(당신 손에만 있는 것 페이지)
  cheer     - 응원(액션 플랜 페이지)
"""
from pathlib import Path
from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "mascot"
ASSETS.mkdir(parents=True, exist_ok=True)

ROBE = (167, 113, 66)       # 로브 - 브랜드 골드브라운
ROBE_DARK = (139, 91, 51)
SKIN = (247, 219, 189)
HAIR = (233, 231, 227)      # 백발
ACCENT = (201, 168, 106)    # 골드 포인트
DARK = (36, 33, 29)
BLUSH = (232, 160, 140)

W, H = 400, 460


def _base(draw):
    # 로브(몸통) - 둥근 사다리꼴
    draw.polygon(
        [(120, 460), (280, 460), (255, 250), (145, 250)],
        fill=ROBE,
    )
    draw.polygon([(120, 460), (280, 460), (270, 400), (130, 400)], fill=ROBE_DARK)
    # 옷깃 라인(골드)
    draw.line([(180, 250), (160, 460)], fill=ACCENT, width=5)
    draw.line([(220, 250), (240, 460)], fill=ACCENT, width=5)
    # 가슴 브로치(장식)
    draw.ellipse([188, 300, 212, 324], outline=ACCENT, width=4)
    # 머리(백발, 둥근 번)
    draw.ellipse([115, 90, 285, 260], fill=SKIN)
    draw.pieslice([100, 60, 300, 220], 180, 360, fill=HAIR)
    draw.ellipse([175, 55, 225, 100], fill=HAIR)  # 상투
    draw.ellipse([185, 45, 215, 75], fill=HAIR)
    # 볼터치
    draw.ellipse([133, 175, 163, 197], fill=BLUSH)
    draw.ellipse([237, 175, 267, 197], fill=BLUSH)


def _eyes_closed_smile(draw):
    draw.arc([150, 155, 190, 185], 200, 340, fill=DARK, width=5)
    draw.arc([210, 155, 250, 185], 200, 340, fill=DARK, width=5)
    draw.arc([172, 190, 228, 220], 20, 160, fill=DARK, width=6)  # 미소


def _eyes_open_dot(draw, mouth="o"):
    draw.ellipse([163, 158, 179, 176], fill=DARK)
    draw.ellipse([221, 158, 237, 176], fill=DARK)
    if mouth == "o":
        draw.ellipse([188, 198, 212, 222], fill=DARK)
    elif mouth == "smile":
        draw.arc([172, 190, 228, 224], 10, 170, fill=DARK, width=6)
    elif mouth == "small":
        draw.line([(192, 205), (208, 205)], fill=DARK, width=5)


def _arms_down(draw):
    draw.ellipse([90, 300, 150, 400], fill=ROBE)
    draw.ellipse([250, 300, 310, 400], fill=ROBE)
    draw.ellipse([95, 370, 135, 410], fill=SKIN)
    draw.ellipse([265, 370, 305, 410], fill=SKIN)


def _arms_thinking(draw):
    draw.ellipse([90, 300, 150, 400], fill=ROBE)
    # 오른팔이 턱으로
    draw.polygon([(250, 320), (300, 260), (280, 240), (240, 300)], fill=ROBE)
    draw.ellipse([255, 225, 295, 265], fill=SKIN)


def _arms_up_cheer(draw):
    draw.polygon([(150, 320), (95, 230), (120, 210), (170, 290)], fill=ROBE)
    draw.polygon([(250, 320), (305, 230), (280, 210), (230, 290)], fill=ROBE)
    draw.ellipse([85, 195, 125, 235], fill=SKIN)
    draw.ellipse([275, 195, 315, 235], fill=SKIN)
    # 반짝임
    for (x, y, s) in [(70, 130, 14), (330, 110, 10), (300, 190, 8)]:
        draw.line([(x - s, y), (x + s, y)], fill=ACCENT, width=4)
        draw.line([(x, y - s), (x, y + s)], fill=ACCENT, width=4)


def make(name, arms, face):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    arms(d)
    _base(d)
    face(d)
    img.save(ASSETS / f"{name}.png")


if __name__ == "__main__":
    make("greeting", _arms_down, lambda d: _eyes_closed_smile(d))
    make("thinking", _arms_thinking, lambda d: _eyes_open_dot(d, "small"))
    make("wow", _arms_down, lambda d: _eyes_open_dot(d, "o"))
    make("cheer", _arms_up_cheer, lambda d: _eyes_open_dot(d, "smile"))
    print("마스코트 생성 완료:", list(ASSETS.glob("*.png")))
