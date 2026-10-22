"""接口和导入共用的数据定义；用字段约束阻止不合理输入。"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator

from backend.config import business_today

Weather = Literal["sunny", "cloudy", "rainy"]


class SaleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    date: date
    dish_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    dish_name: str = Field(min_length=1, max_length=100)
    sales_quantity: int = Field(ge=0, le=1000000, strict=True)
    prepared_quantity: int | None = Field(default=None, ge=0, le=1000000, strict=True)
    waste_quantity: int | None = Field(default=None, ge=0, le=1000000, strict=True)
    weather: Weather | None = None
    is_exam_week: StrictBool | None = None
    has_event: StrictBool | None = None

    @field_validator("date")
    @classmethod
    def reject_future_actuals(cls, value):
        if value > business_today():
            raise ValueError("实际销量不能填写未来日期")
        return value

    @model_validator(mode="after")
    def check_quantities(self):
        if self.prepared_quantity is not None:
            if self.sales_quantity > self.prepared_quantity:
                raise ValueError("销量不能超过备餐量")
            if (
                self.waste_quantity is not None
                and self.sales_quantity + self.waste_quantity > self.prepared_quantity
            ):
                raise ValueError("销量加浪费量不能超过备餐量")
        return self


class SaleBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    records: list[SaleRecord] = Field(min_length=1, max_length=20000)


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_date: date
    weather: Weather = "sunny"
    is_exam_week: StrictBool = False
    has_event: StrictBool = False
    mode: Literal["auto", "baseline", "demo"] = "auto"
    prep_buffer_percent: float = Field(default=0, ge=0, le=50, allow_inf_nan=False)


class TrainingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cutoff_date: date | None = None
