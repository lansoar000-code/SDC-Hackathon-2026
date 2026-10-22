# 加入 XGBoost

## 当前行为
每道菜使用同一组历史特征、同一训练/验证日期，比较历史基线、Ridge 和 XGBoost。选择验证 MAE 最低者；同分按基线、Ridge、XGBoost 的顺序选择。
不是强制让 XGBoost 替换所有菜品。当前这批合成数据的八道菜在验证阶段均选中了 XGBoost。

## 模块与文件
- forecasting/estimators.py：统一训练与预测入口；Ridge 标准化，XGBoost 使用树模型。
- forecasting/training.py：只根据验证段选择方法；参数和三个候选分数写入模型。
- forecasting/predictor.py：按 kind 调用实际算法，明细返回 algorithm。
- frontend/js/charts.js：分别显示 XGBoost、Ridge、基线的验证 MAE。
- retrain_synthetic.py：复用现有 80,000 条数据，不重新生成销量。

## 固定配置
XGBoost 3.4.1，CPU hist，200 轮，深度 4，学习率 0.05，min_child_weight=10，subsample=0.85，lambda=10，alpha=0.1，种子 20261022，线程 2。
这套参数在查看本次 XGBoost 测试结果前固定；没有根据测试成绩选择轮数或反复调参。
XGBoost 使用 [官方 JSON 模型保存方式](https://xgboost.readthedocs.io/en/stable/tutorials/saving_model.html)，不使用 pickle。输入、训练和预测依据 [官方 Python 原生接口](https://xgboost.readthedocs.io/en/stable/python/python_intro.html)。

## 相同时间段的模拟比较
前 7,000 天训练、接着 1,500 天验证；模型选择后用前 8,500 天重训。
最后 1,500 天、共 12,000 条菜品日记录，滚动单日预测。三种方法的日期、特征和观察到的过去销量一致。

| 方法 | MAE（份/菜品日） | WAPE（误差率） | Bias（份） |
|---|---:|---:|---:|
| XGBoost | 9.0113 | 12.9424% | -2.9942 |
| Ridge | 12.1469 | 17.4458% | -0.6801 |
| 历史基线 | 14.5899 | 20.9545% | 0.1001 |

XGBoost 在这段模拟比较中总体误差更低，但平均偏少约 3 份；它没有解决假期、关闭日和供给冲击等所有问题。
这段测试在旧版 Ridge 项目中已经查看过。本次属于同段比较，不应称为一份全新未见的测试集；结果也不能证明真实食堂精度。
测试只评估冻结的 holdout_model，不用来改选方法。最终部署模型另用全部 10,000 天重训，不能把上述指标称为该全量模型的独立测试效果。

## 本地路径与运行
原数据、原 Ridge 模型和报告保留。新增输出：
- data/synthetic/v1/xgboost_comparison/comparison_report.json：同段比较报告。
- data/synthetic/v1/xgboost_comparison/holdout_predictions.csv：逐条结果。
- models/synthetic/xgboost-v2/holdout_model.json：只用前 8,500 天训练的模型。
- models/synthetic/xgboost-v2/final_model.json：使用全部 10,000 天的当前模型。

首次复现：安装 backend/requirements.txt，然后运行 python retrain_synthetic.py。
输出文件已存在时会停止，避免覆盖；再次比较使用 --output、--models 另选新目录。
运行 python run_synthetic.py，8002 端口优先使用新的 xgboost-v2 模型文件；没有新模型时仍可用原 Ridge 文件。
新建数据的 prepare_synthetic.py、网页训练按钮和编号训练脚本也都会比较三个候选。

## 验证
25 项回归通过，覆盖原生 JSON 模型往返、可复现训练、非线性场景选择 XGBoost、旧 Ridge 文件兼容、历史隔离、数据库事务与 API 工作流。
模型、数据与打包文件只保存在本地；GitHub 保存实现与说明。
