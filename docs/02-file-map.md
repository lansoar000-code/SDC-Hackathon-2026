# 完整文件地图

今天只做架构说明与注释占位；标为第二阶段的内容暂不影响第一版演示。文件名是建议实现位置，不代表对应功能已经完成。

## 保留的已有文件
| 文件 | 作用 | 当前状态 |
|---|---|---|
| frontend/index.html | 页面结构、输入与结果区 | 已有演示 |
| frontend/style.css | 页面样式 | 已有演示 |
| frontend/script.js | 按天气、考试周、活动生成模拟结果 | 已有模拟逻辑 |
| backend/requirements.txt | 以后记录 Python 依赖 | 暂空，等确定框架 |
| .gitignore | 排除无需提交的本地文件 | 保留原文件 |
| .replit | 已有 Replit 配置 | 保留原文件 |
| LICENSE | 授权说明 | 保留原文件 |

## 后端与预测文件
| 文件 | 负责什么 |
|---|---|
| backend/main.py | 后端启动入口：创建 API 服务、注册路由和前端访问配置。 |
| backend/database.py | 数据库连接与初始化：统一打开、关闭数据库和创建表。 |
| backend/config.py | 读取运行配置：数据库路径、模型路径、允许的前端地址。 |
| backend/schemas.py | 请求和响应格式：约定日期、天气、菜品、数量等字段与校验规则。 |
| backend/routes/health.py | 健康检查接口：让前端知道后端是否正常运行。 |
| backend/routes/dishes.py | 菜品接口：获取菜品编号和名称。 |
| backend/routes/imports.py | 历史数据导入接口：接收上传文件，调用校验与保存服务。 |
| backend/routes/predictions.py | 预测接口：接收条件、触发预测、查询预测历史。 |
| backend/routes/sales.py | 第二阶段：实际销量录入接口，为预测效果比较提供真实值。 |
| backend/routes/reports.py | 第二阶段：误差报表接口，返回可解释的评估指标。 |
| backend/services/import_service.py | 导入流程：解析文件、调用校验、保存合法记录、返回问题行。 |
| backend/services/prediction_service.py | 预测流程：读取历史数据、调用预测模块、形成备餐建议并保存记录。 |
| backend/services/report_service.py | 第二阶段：把实际销量与预测结果对齐并计算报表。 |
| backend/repositories/dishes.py | 菜品数据读写：把数据库操作与 API 路由分开。 |
| backend/repositories/sales.py | 历史销量数据读写。 |
| backend/repositories/predictions.py | 预测记录与结果明细数据读写。 |
| forecasting/step0_import_excel.py | 可独立运行的导入步骤：将确认支持的 Excel/CSV 整理成统一数据格式。 |
| forecasting/step1_check_data.py | 可独立运行的数据检查步骤：列名、日期、缺失、重复、数量和菜品规则。 |
| forecasting/step2_train.py | 可独立运行的训练步骤：按时间分割数据，对比简单基线与候选模型。 |
| forecasting/step3_predict.py | 可独立运行的预测步骤：加载指定版本模型，生成下一天各菜品需求。 |
| forecasting/step4_check_features.py | 开发检查步骤：确认特征只来自过去，训练和预测使用相同字段规则。 |
| forecasting/features.py | 历史特征：按菜品计算过去销量、移动均值及日历条件。 |
| forecasting/baseline.py | 简单基线预测：为复杂模型提供可对比的起点。 |
| forecasting/predictor.py | 统一预测入口：提供给后端服务调用，处理模型和基线的来源标识。 |
| forecasting/evaluate.py | 评估指标：MAE、WAPE、Bias，记录时间范围和数据来源。 |

## 前端预留文件
| 文件 | 负责什么 |
|---|---|
| frontend/js/api.js | 前后端请求与网络错误处理 |
| frontend/js/history.js | 第二阶段历史预测记录 |
| frontend/js/charts.js | 第二阶段趋势与误差图 |

## 各目录职责
- **backend/**：Python 后端：负责校验输入、调用预测、读写数据库。main.py 是入口，routes/ 接请求，services/ 管业务流程，repositories/ 管数据库。schemas.py 约定数据格式，config.py 管运行配置。所有 Python 文件目前只有职责注释，requirements.txt 暂空，框架确定后再填写依赖。

- **backend/routes/**：请求接待处：按健康检查、菜品、导入、预测、实际销量和报表拆分。它们负责 HTTP 参数与响应，具体运算交给 services。sales 和 reports 是第二阶段。

- **backend/services/**：业务处理处：协调导入、预测和报表。例如预测服务要读取历史、调用 forecasting、保存记录，再返回统一结果。

- **backend/repositories/**：数据库操作处：统一保存和读取菜品、销量及预测记录。路由不直接拼接数据库操作。

- **frontend/**：用户界面：index.html 是页面结构，style.css 管外观，script.js 是现有模拟演示交互。js/api.js 预留后端请求；js/history.js 和 js/charts.js 预留历史记录与图表。新 JS 文件尚未接入 HTML。现有脚本明天再按职责逐步拆分，避免今天改变演示行为。

- **frontend/js/**：预留前端模块：api.js 负责请求，history.js 负责历史记录，charts.js 负责图表。今天只有注释；它们还未被页面加载。

- **forecasting/**：预测与数据处理：step0 导入 → step1 检查 → step2 训练 → step3 预测；step4 检查特征是否泄露未来数据。features、baseline、predictor、evaluate 是供这些步骤和后端复用的公共模块。今天全部只是注释占位。

- **data/**：数据区域：raw 保留原始文件，processed 保存清理结果，predictions 保存预测输出。当前没有真实数据或虚构样本。业务敏感数据不要直接提交到 GitHub；以后按需要配置忽略规则。

- **data/raw/**：原始 CSV/Excel 的本地存放位置。原始文件只读保留；数据来源、字段与授权明确后再导入。当前只有说明。

- **data/processed/**：清理后数据的本地位置。以后记录清理步骤、问题行和字段定义，不能无记录地覆盖原始数据。当前没有生成结果。

- **data/predictions/**：预测输出的本地位置。未来输出包含目标日期、菜品、预测销量、备餐建议、模型版本和数据来源。当前没有预测文件。

- **models/**：训练模型的本地位置。未来保存模型、输入字段、训练日期范围、模型版本和评估说明。当前没有已训练模型，不提交大模型或敏感数据。

- **docs/**：理解项目的入口：按 01 到 08 顺序阅读。02 是逐文件地图；接口与扩展方案是草案，不代表功能已实现。

- **deliverables/**：比赛展示材料：report 写报告，slides 写 PPT 提纲，video 写视频脚本。分工按已确认角色描述，具体成员待定。材料必须与实际功能一致。

- **deliverables/report/**：报告提纲：餐厅痛点 → 目标用户 → 使用流程 → 系统架构 → 数据来源 → 方法与评估 → 局限 → 团队贡献。尚未制作正式提交文档。

- **deliverables/slides/**：PPT 提纲：问题与场景 → 方案 → 产品流程 → 前后端架构 → 实际演示 → 有证据的效果 → 分工。页数、模板与官方要求尚未确认。

- **deliverables/video/**：视频提纲：介绍问题 → 打开界面 → 填条件 → 运行预测 → 展示结果 → 解释模拟或真实数据来源。代码实现后再录屏；时长和格式待官方要求确认。

- **tests/**：未来检查计划：接口参数校验；导入重复与缺失记录；缺日期和冷启动；特征只用过去数据；请求失败界面；预测合计和明细一致。今天没有测试代码，也没有声称这些检查已通过。

## 阅读方式
先读项目根 README，再看产品效果与系统流转。进入每个文件夹点 README，就能看到它的中文职责说明。Python 和新增 JS 文件的开头也有中文注释。
