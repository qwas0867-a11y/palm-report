"""
데모/테스트용 손바닥 '샘플' 이미지를 프로그램으로 생성한다.
(실제 고객 사진이 없으므로, 파이프라인 검증용 예시 이미지를 직접 그려서 대체한다.)

실제 서비스에서는 이 파일을 쓰지 않고, 고객이 업로드한 실제 손 사진 4장
(왼손 정면 / 오른손 정면 / 주 사용 손 클로즈업 / 45도 손날)을 그대로 사용한다.
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(exist_ok=True)

SKIN = (222, 178, 148)
SKIN_SHADOW = (196, 150, 122)
BG = (214, 222, 226)

LINE_COLORS = {
    "life": (214, 90, 70),        # 생명선 - 빨강
    "head": (70, 120, 200),       # 두뇌선 - 파랑
    "heart": (80, 165, 110),      # 감정선 - 초록
    "fate": (120, 90, 170),       # 운명선 - 보라
    "sun": (200, 160, 60),        # 태양선 - 골드
}


def _smooth_path(points, steps=60):
    """제어점 목록을 캣멀롬 스타일로 부드럽게 보간."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for t in [j / steps for j in range(steps)]:
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    return out


def draw_hand(draw: ImageDraw.ImageDraw, cx, cy, w, h, mirror=False):
    """손바닥 + 손가락 5개를 단순한 도형으로 그린다."""
    sign = -1 if mirror else 1
    palm_box = [cx - w * 0.42, cy - h * 0.15, cx + w * 0.42, cy + h * 0.55]
    draw.rounded_rectangle(palm_box, radius=int(w * 0.18), fill=SKIN)

    finger_w = w * 0.13
    finger_lens = [0.55, 0.72, 0.78, 0.68, 0.42]
    offsets = [-0.34, -0.16, 0.02, 0.20, 0.36]
    for off, flen in zip(offsets, finger_lens):
        fx = cx + sign * off * w
        top = cy - h * 0.15 - h * flen * 0.55
        box = [fx - finger_w / 2, top, fx + finger_w / 2, cy - h * 0.15 + h * 0.06]
        draw.rounded_rectangle(box, radius=int(finger_w * 0.45), fill=SKIN)

    # 엄지
    tx = cx - sign * w * 0.46
    ty = cy + h * 0.05
    draw.ellipse([tx - w * 0.11, ty - h * 0.14, tx + w * 0.11, ty + h * 0.14], fill=SKIN)

    return palm_box


def draw_crease(draw, points, color, width=3, alpha=255):
    smooth = _smooth_path(points)
    for i in range(len(smooth) - 1):
        draw.line([smooth[i], smooth[i + 1]], fill=color + (alpha,), width=width)


def make_palm_image(path, mirror=False, hand_label="오른손", seed=1):
    random.seed(seed)
    W, H = 820, 1000
    img = Image.new("RGBA", (W, H), BG + (255,))
    draw = ImageDraw.Draw(img)

    cx, cy, w, h = W / 2, H * 0.42, W * 0.62, H * 0.62
    palm_box = draw_hand(draw, cx, cy, w, h, mirror=mirror)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    sign = -1 if mirror else 1
    px0, py0, px1, py1 = palm_box

    # 생명선: 엄지 뿌리를 감싸며 손목쪽으로
    life = [
        (cx - sign * w * 0.18, py0 + (py1 - py0) * 0.10),
        (cx - sign * w * 0.30, py0 + (py1 - py0) * 0.35),
        (cx - sign * w * 0.27, py0 + (py1 - py0) * 0.65),
        (cx - sign * w * 0.16, py1 - (py1 - py0) * 0.05),
    ]
    draw_crease(odraw, life, LINE_COLORS["life"], width=5)

    # 두뇌선: 손날쪽으로 거의 수평
    head = [
        (cx - sign * w * 0.20, py0 + (py1 - py0) * 0.22),
        (cx, py0 + (py1 - py0) * 0.30),
        (cx + sign * w * 0.20, py0 + (py1 - py0) * 0.42),
        (cx + sign * w * 0.30, py0 + (py1 - py0) * 0.50),
    ]
    draw_crease(odraw, head, LINE_COLORS["head"], width=5)

    # 감정선: 검지-중지 사이에서 손날쪽으로
    heart = [
        (cx + sign * w * 0.18, py0 + (py1 - py0) * 0.06),
        (cx - sign * w * 0.02, py0 + (py1 - py0) * 0.10),
        (cx - sign * w * 0.22, py0 + (py1 - py0) * 0.14),
        (cx - sign * w * 0.34, py0 + (py1 - py0) * 0.10),
    ]
    draw_crease(odraw, heart, LINE_COLORS["heart"], width=5)

    # 운명선: 손목에서 중지 방향으로
    fate = [
        (cx + sign * w * 0.02, py1 - (py1 - py0) * 0.02),
        (cx + sign * w * 0.03, py0 + (py1 - py0) * 0.55),
        (cx + sign * w * 0.05, py0 + (py1 - py0) * 0.20),
    ]
    draw_crease(odraw, fate, LINE_COLORS["fate"], width=4)

    # 태양선: 약지 뿌리 아래 짧게
    sun = [
        (cx + sign * w * 0.20, py0 + (py1 - py0) * 0.28),
        (cx + sign * w * 0.20, py0 + (py1 - py0) * 0.14),
    ]
    draw_crease(odraw, sun, LINE_COLORS["sun"], width=4)

    overlay = overlay.filter(ImageFilter.GaussianBlur(0.4))
    img = Image.alpha_composite(img, overlay)
    img = img.filter(ImageFilter.SMOOTH)
    img.convert("RGB").save(path, quality=92)
    return path


if __name__ == "__main__":
    make_palm_image(ASSETS / "sample_left.jpg", mirror=True, hand_label="왼손", seed=1)
    make_palm_image(ASSETS / "sample_right.jpg", mirror=False, hand_label="오른손", seed=2)
    print("샘플 이미지 생성 완료:", list(ASSETS.glob("*.jpg")))
