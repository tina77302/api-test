"""터미널이 열려 있는 동안 예측 업데이트를 주기적으로 실행한다.

실행:
    python -m automation.run_scheduler --hours 24
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hours",
        type=float,
        default=24,
        help="업데이트 간격(시간), 기본값 24",
    )
    parser.add_argument(
        "--skip-first",
        action="store_true",
        help="시작 직후 업데이트를 생략하고 첫 간격만큼 기다림",
    )
    args = parser.parse_args()
    if args.hours <= 0:
        raise SystemExit("--hours는 0보다 커야 합니다.")

    interval_seconds = args.hours * 60 * 60
    first_run = True
    print(f"{args.hours:g}시간 간격 자동 업데이트를 시작합니다.")
    print("중지하려면 Ctrl+C를 누르세요.")

    try:
        while True:
            if not (first_run and args.skip_first):
                subprocess.run(
                    [sys.executable, "-m", "automation.update_forecast"],
                    cwd=PROJECT_DIR,
                    check=False,
                )
            first_run = False
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n자동 업데이트를 종료했습니다.")


if __name__ == "__main__":
    main()
