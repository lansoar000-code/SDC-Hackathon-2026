# 文件地图（代码版）
本次已将原先注释占位实现为可运行模块。展示材料目录继续保留给队友填写。
逐步讲解见 [代码阅读指南](09-code-reading.md)。

| 文件/目录 | 具体职责 |
|---|---|
| run.py | PyCharm 和终端的启动入口 |
| backend/main.py | 组装路由、错误处理、页面服务 |
| backend/config.py | 路径、上传限制和 UTC+8 日期 |
| backend/database.py | 建表、事务、连接关闭 |
| backend/schemas.py | 输入字段、类型与业务约束 |
| backend/errors.py | 统一业务错误 |
| backend/dependencies.py | 向每个请求提供应用配置 |
| backend/routes/health.py | 健康与数据概况 |
| backend/routes/dishes.py | 菜品查询 |
| backend/routes/imports.py | 文件上传 |
| backend/routes/predictions.py | 预测、历史、详情、CSV 导出 |
| backend/routes/sales.py | 实际销量录入与查询 |
| backend/routes/reports.py | 训练、模型状态与误差报表 |
| backend/services/import_service.py | 整批导入事务 |
| backend/services/prediction_service.py | 预测协调与保存快照 |
| backend/services/report_service.py | 实际销量对齐和误差口径 |
| backend/repositories/ | dishes/sales/predictions 的 SQL 读写 |
| forecasting/data.py | CSV/XLSX 解析与行号错误 |
| forecasting/features.py | 训练/在线共用历史特征 |
| forecasting/baseline.py | 同星期或近七次均值 |
| forecasting/training.py | 标准化 Ridge、时间验证、择优、JSON 保存 |
| forecasting/predictor.py | demo/baseline/model 选择与备餐建议 |
| forecasting/evaluate.py | MAE、RMSE、WAPE、Bias |
| forecasting/cli.py | 五个编号脚本共用命令行逻辑 |
| forecasting/step0_import_excel.py | 表格转统一 CSV |
| forecasting/step1_check_data.py | 独立数据校验 |
| forecasting/step2_train.py | 独立训练 |
| forecasting/step3_predict.py | 独立预测和导出 |
| forecasting/step4_check_features.py | 修改未来销量后检查特征稳定性 |
| frontend/index.html | 预测、导入、训练、实际反馈、历史和误差页面 |
| frontend/style.css | 原有暗色视觉样式 |
| frontend/app.css | 扩展表单、表格、状态和移动布局 |
| frontend/script.js | 页面事件协调和预测展示 |
| frontend/js/api.js | 请求、超时、错误信息 |
| frontend/js/history.js | 历史分页、详情展示 |
| frontend/js/charts.js | 训练比较与预测/实际图表 |
| frontend/js/ui.js | 安全文本节点与统一状态 |
| frontend/templates/sales_template.csv | 仅表头的空模板 |
| tests/test_workflow.py | 临时数据库和合成数据回归 |
| tests/make_browser_fixture.py | 生成明确标识的浏览器测试数据 |
| data/ | 本地 SQLite 与数据；真实数据不提交 |
| models/ | 本地训练参数，不提交 |
| deliverables/ | 队友的报告、PPT、视频提纲 |

