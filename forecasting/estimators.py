"""模型细节集中在这里：Ridge 与 XGBoost 使用同一组输入特征。"""

from functools import lru_cache

import numpy as np
import xgboost as xgb

from forecasting.features import FEATURE_NAMES

# 固定配置不查看测试集，也不为追逐测试成绩反复调参。
XGBOOST_PARAMETERS = {
    "objective": "reg:squarederror",
    "eval_metric": "mae",
    "tree_method": "hist",
    "device": "cpu",
    "max_depth": 4,
    "eta": 0.05,
    "min_child_weight": 10,
    "subsample": 0.85,
    "colsample_bytree": 1.0,
    "lambda": 10.0,
    "alpha": 0.1,
    "seed": 20261022,
    "nthread": 2,
}
XGBOOST_ROUNDS = 200


def fit_ridge(vectors, quantities):
    matrix = np.asarray(vectors, dtype=float)
    center, scale = matrix.mean(axis=0), matrix.std(axis=0)
    scale[scale == 0] = 1
    design = np.column_stack([np.ones(len(matrix)), (matrix - center) / scale])
    penalty = np.eye(design.shape[1]) * 10.0
    penalty[0, 0] = 0  # 不惩罚截距，避免把整体销量强行推向零。
    coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ np.asarray(quantities))
    return {
        "kind": "ridge",
        "center": center.tolist(),
        "scale": scale.tolist(),
        "coefficients": coefficients.tolist(),
    }


def fit_xgboost(vectors, quantities):
    training = xgb.DMatrix(
        np.asarray(vectors, dtype=np.float32),
        label=np.asarray(quantities, dtype=np.float32),
        feature_names=FEATURE_NAMES,
        nthread=2,
    )
    booster = xgb.train(XGBOOST_PARAMETERS, training, num_boost_round=XGBOOST_ROUNDS)
    # 只保存 XGBoost 官方模型格式；不使用依赖 Python 对象快照的 pickle。
    return {
        "kind": "xgboost",
        "model_json": booster.save_raw(raw_format="json").decode("utf-8"),
        "library_version": xgb.__version__,
    }


def predict_estimator(model, vectors):
    """批量预测，训练验证与测试回放都使用此函数。旧 Ridge 字典仍可读取。"""
    matrix = np.asarray(vectors, dtype=float)
    if matrix.ndim != 2 or matrix.shape[1] != len(FEATURE_NAMES):
        raise ValueError("模型输入字段数量不匹配")
    kind = model.get("kind", "ridge")
    if kind == "ridge":
        standardized = (matrix - np.asarray(model["center"])) / np.asarray(model["scale"])
        values = np.column_stack([np.ones(len(matrix)), standardized]) @ np.asarray(
            model["coefficients"]
        )
    elif kind == "xgboost":
        # inplace_predict 避免每次单日请求都重复创建 DMatrix。
        values = _restore_booster(model["model_json"]).inplace_predict(matrix.astype(np.float32))
    else:
        raise ValueError(f"不支持的模型类型：{kind}")
    if not np.isfinite(values).all():
        raise ValueError("模型返回非有限预测值")
    return np.maximum(0.0, values).tolist()


def predict_one(model, vector):
    return float(predict_estimator(model, [vector])[0])


@lru_cache(maxsize=32)
def _restore_booster(model_json: str):
    """缓存键是模型内容；新模型内容改变时自然重新加载，不使用过期实例。"""
    booster = xgb.Booster(params={"nthread": 2, "device": "cpu"})
    booster.load_model(bytearray(model_json, "utf-8"))
    return booster
