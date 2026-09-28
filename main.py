"""
사용법:
  python3 main.py                         # 목(mock) 모드로 데모 PDF 생성 (API 키 불필요)
  ANTHROPIC_API_KEY=sk-ant-... python3 main.py \
      --images left.jpg right.jpg closeup.jpg side.jpg \
      --name 홍길동 --age 34 --gender 여성 --interest 재물 \
      --concern "매출은 있는데 현금이 안 모인다"
"""
import argparse
from pathlib import Path

from src.pipeline import run

ROOT = Path(__file__).resolve().parent

INTEREST_CHOICES = ["연애", "재물", "직업", "건강", "전반적인 삶"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", nargs="*", default=[
        str(ROOT / "assets" / "sample_left.jpg"),
        str(ROOT / "assets" / "sample_right.jpg"),
    ])
    parser.add_argument("--name", default="홍길동")
    parser.add_argument("--age", type=int, default=34, help="고객 나이(만 나이)")
    parser.add_argument("--gender", default="선택 안 함",
                         choices=["여성", "남성", "선택 안 함"])
    parser.add_argument("--interest", default="재물", choices=INTEREST_CHOICES,
                         help="가장 궁금한 주제 - 리포트에서 이 부분을 더 두껍게 다룸")
    parser.add_argument("--job", default="1인 온라인 쇼핑몰 운영, 창업 3년차",
                         help="직업/상황 맥락(선택)")
    parser.add_argument("--concern", default="매출은 있는데 현금이 안 모인다")
    parser.add_argument("--out", default=str(ROOT / "output" / "palm_report_demo.pdf"))
    args = parser.parse_args()

    customer = {
        "name": args.name,
        "age": args.age,
        "gender": args.gender,
        "biggest_interest": args.interest,
        "job_context": args.job,
        "concern": args.concern,
    }
    out = run(args.images, customer, args.out)
    print("생성 완료:", out)


if __name__ == "__main__":
    main()
