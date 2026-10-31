# TaketoriKassen（发布产物）

本仓库**只放构建产物**，源码不公开。

## 下载

在 [Releases](../../releases) 里取 `TaketoriKassen-<版本>.jar`，放进服务端 `plugins/`
覆盖同名旧文件即可，不需要改配置、不需要迁移存档。

## 运行要求

- 服务端：Paper 26.1.2（Java 25）
- 数据目录：`plugins/TaketoriKassen`
- 首次启动会把 `config.yml` 从 `config-version 11` 自动迁到 `12`
- 角色 / 武器 id 与旧版一致，玩家已选角色、房间配置、战绩都能直接沿用

## 版本

| 版本 | 说明 |
| --- | --- |
| 2.2.4 | 退房回大厅的落点兜底：落点不可用时回落主世界出生点并告警（不再静默不传送）、`lobby.yml` 的世界没加载时提示查 `bukkit.yml`、传送异常不再打断收尾、`endCleanup` 逐人 try/catch 不让一个人拖累整队、`unloadAndDelete` 卸载前先驱逐玩家、`entryPointOf` 按世界名回查防传进已卸载世界、`entryPoints` 三处补清理 |
| 2.2.3 | 修房间世界「空图」：整份存档根目录当模板时自动下钻到真正装 `region/` 的那一层再复制；模板没有地形时建房前就拦下并说明原因；房间世界加载后日志打出 folder 与 region 数量；启动时不再直接删 `k_tpl_*` 编辑副本，改为转存 `moonmap-recover/` |
| 2.2.2 | 开局发染色队帽（红「进攻方」/ 蓝「防守方」）、未选角色进房弹菜单提示、加时投票超时改判平局、moonmap 导入失败列出查找路径与可导入世界、启动时清空上局角色绑定 |
| 2.2.1 | 房间 / 月面模板世界兼容 Paper 26.1 的 `dimensions/minecraft` 布局：世界判定不再只认 `level.dat`、缺 `level.dat` 自动补齐、复制跳过 `paper/metadata.dat`、加载失败重试一次 |
| 2.2.0 | 队伍商店（拆弹钳 / 地雷 / 商人 NPC）、包点读条拆弹、加时赛；构建基线 Paper 26.1.2 + Java 25 |