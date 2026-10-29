# 数据来源与复现

## 当前快照

本项目使用课程保留的 `1970-2021_DISASTERS.csv`，共 14,644 行、47 列。
分析窗口统一为 1970—2020；2021 年的完整性未经确认，因此统一排除。
原始文件的 SHA-256 记录在 `reports/summary.json`，用于验证是否使用了相同文件。

原课程报告将来源记为 Kaggle 的
[ALL NATURAL DISASTERS 1900-2021 / EOSDIS](https://www.kaggle.com/datasets/brsdincer/all-natural-disasters-19002021-eosdis)。
尚未用线上下载文件与课程快照逐字节比对，不能保证当前下载版本与本地快照完全相同。
数据字段与 EM-DAT 的历史公开表结构相符；课程标题中的 EOSDIS 不应直接解释为 NASA 实测数据来源。

## 如何运行

1. 按来源平台要求自行获取有权使用的数据。
2. 将兼容的历史 CSV 放入 `data/raw/1970-2021_DISASTERS.csv`。
3. 在仓库根目录运行 `python -m src.run`。
4. 如文件位置不同，使用 `python -m src.run --input /path/to/file.csv`。

若使用其他年份或新版 EM-DAT，需要先显式映射新版字段名称、核查年度覆盖，再修改固定分析窗口。
脚本拒绝缺失必要字段、重复编号、无法解析的数值及负影响值，不会静默替换来源。
新的下载版本可能产生不同结果，应重新生成所有图表和报告。

## 记录粒度

`Dis No` 示例格式为 `1970-0013-ARG`，包含年份、事件序号与国家后缀。
一行是一次灾害在一个国家的影响记录；同一跨国事件可能对应多行。
主要计数使用行数，并明确标记为 country-impact records；去除国家后缀的编号仅作独立事件数参考。
保留 ID，避免用名称字段计数或丢失核验依据。

## 最小数据字典

| 字段 | 定义与处理 |
|---|---|
| `Dis No` | 国家级影响记录编号，窗口内必须非空且唯一 |
| `Year` | 历史快照的年份字段，所有分析统一按此筛选 |
| `Country` / `ISO` | 国家或地区及三位国家代码，不代表现代政治边界重建 |
| `Continent` | 历史快照大洲分类，沿用来源，不重分类 |
| `Disaster Type` | 灾害类型，去除首尾空格，保留历史分类 |
| `Start Month` | 1—12，未知保持空值，非法月份转为未知并计入摘要 |
| `Total Deaths` | 已报告死亡人数，未知不填零 |
| `Total Affected` | 已报告受影响人数，未知不填零 |
| `Total Damages ('000 US$)` | 已报告名义经济损失，单位千美元，未知不填零 |

## 使用与发布

原始与逐行处理数据不纳入公开包或 Git 跟踪；本地文件仅用于复现。
公开包包含汇总表、分析图和代码，不包含逐条损失值、逐行排名或课程原报告。
未对第三方数据授予新的许可。

EM-DAT 对 Public Data 与 Archive 有不同分发条件；即使从第三方下载，也不能据此推定可自由转发原始数据。
实际使用及发布应遵守所获取版本的条款。

- [EM-DAT 数据结构](https://doc.emdat.be/docs/data-structure-and-content/core-structure-of-the-database/)
- [公开表字段说明](https://doc.emdat.be/docs/data-structure-and-content/emdat-public-table/)
- [缺失数据说明](https://files.emdat.be/docs/20240725%20Caveat%20of%20missing%20data%20in%20EM-DAT.pdf)
- [使用和再分发说明](https://doc.emdat.be/docs/additional-resources-and-tutorials/faq/)
