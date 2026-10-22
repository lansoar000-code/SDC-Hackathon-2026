# 已实现接口
运行后以 /docs 自动生成的 OpenAPI 页面为完整字段定义。

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | /api/health | 服务状态和销量日期范围 |
| GET | /api/dishes | 已导入菜品清单 |
| POST | /api/data/import | multipart 表单 file，CSV/XLSX；成功 201 |
| POST | /api/sales | JSON records 数组，新增实际销量；成功 201 |
| GET | /api/sales | 分页查看销量，limit 1–1000、offset ≥ 0 |
| POST | /api/predictions | 创建并保存预测；成功 201 |
| GET | /api/predictions | 分页历史，limit 1–100、offset ≥ 0 |
| GET | /api/predictions/{id} | 保存的完整预测快照 |
| GET | /api/predictions/{id}/export | CSV 导出；菜名防公式解释 |
| POST | /api/models/train | JSON {} 或 cutoff_date；训练及验证比较 |
| GET | /api/models/status | 模型状态和验证报告 |
| GET | /api/reports/metrics | 实际/预测对齐，事前指标与历史补做分开 |

预测请求：
```json
{"target_date":"2026-10-23","weather":"sunny","is_exam_week":false,"has_event":false,"mode":"auto","prep_buffer_percent":0}
```
mode：auto/baseline/demo。weather：sunny/cloudy/rainy。备餐余量 0–50；布尔字段必须为 JSON true/false。
结果包含 prediction_id、created_at、target_date、source、model_version、data_through、conditions、items、总销量、总备餐量和 warnings。
每个 item 记录 dish_id、dish_name、predicted_sales_quantity、recommended_prep_quantity、method。

错误统一返回 error.message、可选 error.details。格式错误 400、缺历史或字段非法 422、重复记录/名称冲突 409、文件过大 413、找不到记录 404。
基线不受天气/考试周/活动影响；混合结果 source=mixed，并逐菜品说明 method。
同源页面与 API 一起由服务提供，无需配置跨域。


