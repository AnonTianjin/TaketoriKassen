覆盖 `plugins/TaketoriKassen-*.jar` 即可，不需要改配置、不需要迁移存档。

## 新增

- 队伍商店：`/taketori shop` 开界面（11 号槽拆弹钳 / 15 号槽地雷 / 22 号关闭），
  `/taketori shop clipper|mine` 直接买，`/taketori shop setnpc <red|blue>` 记录商人位置
- 拆弹钳（红队，30 分，每人 2 把，携带时拆除 10 秒 → 6 秒，阵亡失效）
- 地雷（蓝队，40 分，每队 2 枚，杀伤 5 格 / 触发 3 格）
- 加时赛：时间到双方均未达标则投票，全员同意后 60 秒纯 PVP 比人头
- 包点相位机：开局延迟 40 秒变 TNT，红队 4.5 格内左键读条拆除，超时转基地战

## 兼容性

- 角色 / 武器 id 与旧版一致，玩家已选角色、房间配置、战绩无需迁移
- `config-version` 11 → 12 由插件首次启动自动完成
- 命令 `/taketori`、权限 `taketori.play` / `taketori.admin`、数据目录 `plugins/TaketoriKassen` 均不变

## 运行要求

Paper 26.1.2（Java 25）