"""6각 레이더 차트(생명력·사고력·감정·재물·직업운·인연)를 그려 base64 PNG로 반환."""
import base64
import io
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

for _path in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]:
    try:
        fm.fontManager.addfont(_path)
    except Exception:
        pass
plt.rcParams["font.family"] = "Noto Sans CJK JP"  # 실제 등록명(글리프는 한글 포함 CJK 통합)
plt.rcParams["axes.unicode_minus"] = False


def render_radar_png(scores: dict, accent="#a97142") -> str:
    labels = list(scores.keys())
    values = list(scores.values())
    n = len(labels)
    angles = [i / n * 2 * math.pi for i in range(n)]
    angles += angles[:1]
    values_closed = values + values[:1]

    fig = plt.figure(figsize=(4.2, 4.2), dpi=160)
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)

    ax.plot(angles, values_closed, color=accent, linewidth=2)
    ax.fill(angles, values_closed, color=accent, alpha=0.25)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=11, color="#3a332c")
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels([])
    ax.spines["polar"].set_color("#d8cdbd")
    ax.grid(color="#e3d9c8", linewidth=0.8)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
