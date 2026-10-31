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
| 2.2.1 | 房间 / 月面模板世界兼容 Paper 26.1 的 `dimensions/minecraft` 布局：世界判定不再只认 `level.dat`、缺 `level.dat` 自动补齐、复制跳过 `paper/metadata.dat`、加载失败重试一次 |
| 2.2.0 | 队伍商店（拆弹钳 / 地雷 / 商人 NPC）、包点读条拆弹、加时赛；构建基线 Paper 26.1.2 + Java 25 |