# backend/repositories：板块说明

SQL 访问层：dishes 查询菜品，sales 检查重复并保存销量，predictions 保存和读取 JSON 快照。事务由服务通过 database.connect() 管理。

