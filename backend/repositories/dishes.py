"""菜品查询。菜品在导入销量时创建，不自动生成虚构菜品。"""


def list_dishes(connection) -> list[dict]:
    return [
        dict(row)
        for row in connection.execute(
            "SELECT dish_id, dish_name FROM dishes ORDER BY dish_name, dish_id"
        )
    ]
