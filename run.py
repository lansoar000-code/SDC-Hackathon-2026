"""直接在 PyCharm 运行此文件，随后访问 http://127.0.0.1:8000。"""

import uvicorn

from backend.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
