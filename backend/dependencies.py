"""从当前应用取配置，测试时可使用临时数据库，不依赖全局可变状态。"""

from fastapi import Request


def get_settings(request: Request):
    return request.app.state.settings
