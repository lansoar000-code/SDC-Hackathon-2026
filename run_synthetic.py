"""在独立模拟库运行网站：http://127.0.0.1:8002；不会切换普通业务数据库。"""

import uvicorn

from backend.config import PROJECT_ROOT, Settings
from backend.main import create_app

if __name__ == "__main__":
    folder = PROJECT_ROOT / "data/synthetic/v1"
    if not (folder / "training_report.json").exists():
        raise SystemExit("请先运行 prepare_synthetic.py，生成数据与模型。")
    new_model = PROJECT_ROOT / "models/synthetic/xgboost-v2/final_model.json"
    model_path = (
        new_model if new_model.exists() else PROJECT_ROOT / "models/synthetic/v1/final_model.json"
    )
    app = create_app(
        Settings(
            database_path=folder / "training.sqlite3",
            model_path=model_path,
        )
    )
    uvicorn.run(app, host="127.0.0.1", port=8002)
