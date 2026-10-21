# 前后端接口草案（尚未实现）
接口路径先约定，明天实现时统一调整；今天这些网址不能调用。

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | /api/health | 确认服务是否启动 |
| GET | /api/dishes | 读取菜品清单 |
| POST | /api/data/import | 上传历史 CSV，返回成功数和问题行 |
| POST | /api/predictions | 提交日期及条件，生成菜品需求预测 |
| GET | /api/predictions | 查询预测历史 |
| GET | /api/predictions/{id} | 查看某次预测详情 |
| POST | /api/sales | 录入实际销量（第二阶段） |
| GET | /api/reports/metrics | 查询预测误差（第二阶段） |

## 预测请求字段
target_date：预测日期；weather：天气类别；is_exam_week：布尔值；has_event：布尔值。
餐厅位置和天气类别含义尚未定稿；前端和后端必须共用同一套取值。

## 预测返回字段
prediction_id、target_date、source（demo/baseline/model）、model_version、items、total_predicted_sales、warnings。
items 中包含 dish_id、dish_name、predicted_sales_quantity、recommended_prep_quantity。
数量单位为份；备餐量可以根据业务规则调整，不能直接声称它就是预测销量。
无历史数据时返回明确提示，不凭空生成真实预测；演示模式必须注明模拟。

## 错误处理
日期非法、字段缺失、数据格式不符：指出具体问题。
模型未准备好、数据不足：返回清楚的原因。
前端显示错误信息并恢复按钮，不把失败显示为零需求。

