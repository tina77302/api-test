"""전체 데이터 수집과 예측 생성을 한 번 실행한다.

실행:
    python -m automation.update_forecast
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
STATUS_PATH = OUTPUT_DIR / "update_status.json"
LOCK_PATH = OUTPUT_DIR / ".update.lock"
STEPS = [
    "data_pipeline.collect_ecos_data",
    "data_pipeline.collect_live_features",
    "ml.compare_real_models",
    "ml.predict_live",
    "ml.post_pandemic_forecast",
    "ml.tune_post_pandemic_models",
    "ml.reliability_forecast",
    "ml.visualize_live_prediction",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_status(payload: dict) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    temporary_path = STATUS_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(STATUS_PATH)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    try:
        lock_descriptor = os.open(
            LOCK_PATH,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        )
    except FileExistsError:
        raise SystemExit("다른 업데이트가 이미 실행 중입니다.")

    started_at = utc_now()
    status = {
        "state": "running",
        "started_at": started_at,
        "finished_at": None,
        "current_step": None,
        "completed_steps": [],
        "error": None,
    }
    save_status(status)

    try:
        for module in STEPS:
            status["current_step"] = module
            save_status(status)
            print(f"\n[자동 업데이트] {module}")
            subprocess.run(
                [sys.executable, "-m", module],
                cwd=PROJECT_DIR,
                check=True,
            )
            status["completed_steps"].append(module)

        status.update(
            {
                "state": "success",
                "finished_at": utc_now(),
                "current_step": None,
            }
        )
        save_status(status)
        print("\n전체 업데이트가 완료됐습니다.")
    except Exception as exc:
        status.update(
            {
                "state": "failed",
                "finished_at": utc_now(),
                "error": str(exc),
            }
        )
        save_status(status)
        raise
    finally:
        os.close(lock_descriptor)
        LOCK_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
