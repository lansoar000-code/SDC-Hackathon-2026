"""编号步骤 4：支持 PyCharm 直接运行；参数说明见 --help。"""

import sys
from pathlib import Path

# 直接运行文件时，Python 默认只查找当前文件夹；补上项目根目录。
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from forecasting.cli import run_step

if __name__ == "__main__":
    run_step(4)
