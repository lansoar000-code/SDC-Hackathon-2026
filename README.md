# PrepWise｜餐厅需求预测与备餐建议
SDC Hackathon 2026 · Domain 2 · Team 牛马来西亚

**2026-10-22：第一版可运行代码。** 原生 HTML/CSS/JavaScript + FastAPI + SQLite + NumPy Ridge。
支持 CSV/XLSX 导入 → 历史预测 → 备餐建议 → 保存记录 → 实际销量反馈与误差对比。真实业务效果仍需用餐厅数据验证。

## 运行
本次在 **Python 3.12** 验证；其他 Python 版本尚未验证。在项目根目录打开终端：
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe run.py
```
访问 **http://127.0.0.1:8000**；接口文档 **http://127.0.0.1:8000/docs**。
在 PyCharm 中把解释器设为项目 .venv，右键运行根目录 run.py 即可。不要直接双击 HTML。
如果系统 python 命令不可用，请选择已安装的 Python 解释器创建环境；当前电脑也已准备好本地 .venv。

## 第一次使用
已准备 [10,000 天合成数据与训练说明](docs/11-synthetic-data.md)。运行 prepare_synthetic.py 可复现；run_synthetic.py 打开独立模拟训练库（8002 端口）。模拟效果不能代表真实餐厅精度。
1. 没有真实数据时，预测方式明确选择「模拟演示」，查看输入、结果、历史和 CSV 导出。
2. 有数据时，下载页面提供的空 CSV 模板，填入每日各菜品的实际销量，然后导入。也支持第一张工作表的 XLSX。
3. 预测日期建议选最新销量记录的下一天。自动模式先用历史基线；模拟规则绝不会自动混进历史模式。
4. 累积至少 21 个有记录日期后，点击「训练并比较」。每道菜有足够样本且模型验证 MAE 优于基线，才选择 Ridge。
5. 用户设定 0–50% 备餐余量；页面分别显示预测销量和建议备餐量。
6. 营业后录入实际销量，查看预测误差。也可以通过 CSV 批量补充实际销量。

## 代码从哪里读
- [代码阅读指南](docs/09-code-reading.md)：一条请求如何经过前端、路由、服务、数据库和预测模块。
- [完整文件地图](docs/02-file-map.md)：各文件职责。
- [接口说明](docs/04-api-plan.md)、[数据规则](docs/05-data-plan.md)。
- [本次实现与验证](docs/10-implementation.md)：已实现能力、检查证据与限制。

| 目录 | 职责 |
|---|---|
| frontend/ | 页面、请求、历史记录、图表 |
| backend/routes/ | HTTP 入口；校验请求并调用业务服务 |
| backend/services/ | 导入、预测、报表流程 |
| backend/repositories/ | SQL 读写，事务由服务管理 |
| forecasting/ | 读表、历史特征、基线、训练、预测与误差指标 |
| data/ | 本地 SQLite、原始数据、处理结果与预测导出 |
| models/ | 本地模型 JSON；无需 pickle |
| tests/ | 临时合成数据的回归检查；不写入真实数据库 |
| deliverables/ | 报告、PPT 和视频的素材规划 |

## 独立数据脚本
可在 PyCharm 为编号脚本添加命令行参数。下面示例输入文件需由你提供：
```powershell
python forecasting/step0_import_excel.py --input data/raw/sales.xlsx
python forecasting/step1_check_data.py --input data/processed/sales.csv
python forecasting/step2_train.py --input data/processed/sales.csv
python forecasting/step3_predict.py --input data/processed/sales.csv --target-date 2026-10-23
python forecasting/step4_check_features.py --input data/processed/sales.csv
```
独立脚本处理的是文件，不自动写入网页数据库；要在网页使用同一数据，仍需通过导入上传。
导出路径可用 --output 指定，训练模型默认 models/forecast.json；--help 查看参数。

## 检查
若需复现本次全部依赖版本，可安装 requirements.lock.txt；其中也包含检查工具。
```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
ruff check backend forecasting tests run.py
ruff format --check backend forecasting tests run.py
```
代码固定 100 字符目标行宽，保留中文模块说明与关键业务规则注释，函数名使用明确的英文动词。

## 运行边界
- 默认只监听本机，无账号体系；这是本地单餐厅版本，尚未做公网部署。
- 历史基线不对天气、考试周、活动作人为加成；模型只能从已有条件记录中学习。
- 缺失日期不填零；数据不足会告知，不伪造真实销量。
- 训练验证采用按时间的滚动单步预测；验证集用于选模型，不是独立测试集。
- 模型历史与当前历史不一致时自动回退基线；数据更新后可重新训练。
- 同一日期与菜品重复记录整批拒绝，不静默覆盖。纠错编辑功能尚未提供。
- 模拟记录不计入误差；补做历史预测另行标注，不能冒充事前预测。
- 业务日期按 UTC+8；本地数据库、业务数据和模型不提交到 GitHub。

分支：frontend 写前端，backend 写后端和预测，develop 联调，main 保存集成版本。


