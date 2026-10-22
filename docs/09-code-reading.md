# 代码阅读指南
你可以先理解一条流程，再打开具体函数。无需从第一个文件逐行背代码。

## 1. 启动
run.py 调用 uvicorn 启动 backend/main.py 中的 app。
create_app() 只组装路由、错误处理和静态页面；启动时 initialize() 创建 SQLite 表。
Settings 把数据库、模型、页面路径集中管理；不会在函数中散落绝对路径。
配置环境变量：PREPWISE_DATABASE 和 PREPWISE_MODEL。默认路径相对项目根目录确定。

## 2. 用户点击预测
frontend/script.js 读取日期、天气、考试周、活动、模式和备餐余量。
frontend/js/api.js 把它们作为 JSON 发给 POST /api/predictions。
backend/schemas.py 中 PredictionRequest 检查类型和范围。
backend/routes/predictions.py 把合法请求交给 create_prediction()。
backend/services/prediction_service.py 在事务中：
1. 只查目标日期之前的销量。
2. 调用 forecasting/predictor.py 的 predict()。
3. 汇总数量，保存输入、版本、历史截止日和结果快照。
4. 返回结果，前端用 DOM 文本节点展示；菜名不会被当成 HTML。

## 3. 三种预测来源
demo：后端 DEMO_RULES 固定规则，明显标为模拟。
baseline：同星期最近四次均值；不足两次时用最近七条营业记录均值。
model：Ridge 或 XGBoost 从历史特征学习，逐菜品验证后择优；某些菜用模型、另一些用基线时标 mixed。明细 algorithm 字段显示具体算法。

features.py 是训练和预测共用入口，按菜品隔离，严格只取目标日之前数据。
目标日期的天气和活动是用户可提前提供的条件；目标日实际销量不允许进入特征。

## 4. CSV/Excel 导入
routes/imports.py 限制文件大小，读取上传内容。
forecasting/data.py 解析表头、日期、数量与布尔值，逐行调用 SaleRecord 校验。
services/import_service.py 开启数据库事务。
repositories/sales.py 再检查库内重复和同编号名称冲突，全部通过后写入。
其中任何一步失败都返回错误；没有“前半张表已写进去”的状态。

## 5. 训练
routes/reports.py 读取数据快照 → training.py。
日期末段 20% 留作滚动单步验证；训练端与验证端用相同 feature_vector()。
验证过程中可使用较早验证日已观察到的实际值，符合每日滚动预测；不是一次性多日预测。
estimators.py 集中实现 Ridge 和 XGBoost 的训练、批量预测与模型读取。
三个候选使用同一组字段、训练日期和验证日期；验证 MAE 最低者胜出，同分优先基线、其次 Ridge。
模型 JSON 保存字段顺序、模型类型、参数、训练截止日、数据指纹和验证报告；XGBoost 内部使用官方 JSON 模型格式。
模型文件通过临时文件原子替换；历史指纹改变时 predict() 回退基线。

## 6. 读数据库
database.connect() 负责连接生命周期与事务。repositories 仅负责 SQL。
dishes 存菜品；sales 存日期-菜品唯一销量；predictions 存完整 JSON 快照。
SQL 参数使用占位符，不把用户字符串拼进 SQL。
后端处理完请求会关闭连接；重启仍从磁盘恢复记录。

## 7. 反馈与图表
录入实际销量 → POST /api/sales。
GET /api/reports/metrics 按同日期同菜品对齐，只选最近一次非模拟预测。
创建日期在目标日或之后的预测标 retrospective；主指标只算事前保存的预测。
charts.js 展示图和表；所有值来自后端。WAPE 是误差率，不是准确率。

## 8. 如何继续修改
- 改外观：frontend/style.css 和 app.css。
- 改界面事件：script.js；改网络请求规则：js/api.js。
- 加接口：routes 新函数 → schemas 定义 → services 业务 → repositories 读写。
- 改预测：优先读 baseline.py、features.py、estimators.py、training.py、predictor.py。
- 改数据规则：schemas.py 和 forecasting/data.py，同时补 tests/test_workflow.py。

可读性约定：一个模块承担一种职责；入口短小；关键业务取舍写原因注释；异常统一转换为可读错误。
