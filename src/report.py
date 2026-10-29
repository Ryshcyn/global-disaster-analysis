"""Generate the project report from the same population as every figure."""
from pathlib import Path

import pandas as pd

from .analysis import DAMAGE, tables


def markdown_table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join(['---'] * len(headers)) + ' |',
                      *['| ' + ' | '.join(map(str, row)) + ' |' for row in rows]])


def write_report(raw, df, summary, output):
    t = tables(df)
    n = len(df)
    annual = t['annual'].set_index('Year')
    types = t['types'].sort_values('records', ascending=False)
    continents = t['continents'].sort_values('records', ascending=False)
    countries = t['countries'].sort_values('records', ascending=False)
    damage_total = df[DAMAGE].sum()
    p = summary['pareto']
    # All numeric claims below use the same fixed-window source population.
    decades = df[df.Year < 2020].groupby('Decade').size()
    decade_table = markdown_table(['时期', '记录数', '年均记录数'], [
        [f'{year}—{year+9}', f'{count:,}', f'{count/10:.1f}'] for year, count in decades.items()])
    type_table = markdown_table(['灾害类型', '记录数', '占全部记录', '损失覆盖率', '已报告损失（十亿美元）'], [
        [row['Disaster Type'], f"{row['records']:,}", f"{row['records']/n*100:.2f}%",
         f"{row['damage_coverage_pct']:.2f}%",
         '未知' if pd.isna(row['reported_damage_thousand_usd']) else f"{row['reported_damage_thousand_usd']/1e6:,.2f}"]
        for _, row in types.iterrows()])
    continent_table = markdown_table(['大洲', '记录数', '记录占比', '已报告损失占比', '损失覆盖率'], [
        [row.Continent, f'{row.records:,}', f'{row.records/n*100:.2f}%',
         f'{row.reported_damage_thousand_usd/damage_total*100:.2f}%', f'{row.damage_coverage_pct:.2f}%']
        for row in continents.itertuples()])
    country_table = markdown_table(['国家或地区', '记录数', '损失覆盖率', '已报告损失（十亿美元）'], [
        [row.Country, f'{row.records:,}', f'{row.damage_coverage_pct:.2f}%',
         '未知' if pd.isna(row.reported_damage_thousand_usd) else f'{row.reported_damage_thousand_usd/1e6:,.2f}']
        for row in countries.head(10).itertuples()])
    quality_table = markdown_table(['字段', '有效记录数', '缺失记录数', '缺失比例'], [
        [row.field, f'{row.observed:,}', f'{row.missing:,}', f'{row.missing_pct:.2f}%']
        for row in t['quality'].itertuples()])
    raw_missing = raw.isna().sum().sort_values(ascending=False).head(6)
    raw_missing_table = markdown_table(['原始字段', '缺失记录数', '占原始数据'], [
        [field, f'{count:,}', f'{count/len(raw)*100:.2f}%'] for field, count in raw_missing.items()])
    monthly = t['monthly'].set_index('month')['records']
    valid_month = monthly.sum()
    month_table = markdown_table(['开始月份', '记录数', '占有效月份记录'], [
        [f'{int(month)} 月', f'{count:,}', f'{count/valid_month*100:.2f}%'] for month, count in monthly.items()])
    year_peak = int(annual['records'].idxmax())
    loss_peak = int(annual['reported_damage_thousand_usd'].idxmax())
    loss_second = int(annual['reported_damage_thousand_usd'].nlargest(2).index[1])
    low_cover = int(annual['damage_coverage_pct'].idxmin())
    coverage_low = annual.loc[low_cover, 'damage_coverage_pct']
    flood_storm = types.set_index('Disaster Type').loc[['Flood', 'Storm'], 'records'].sum()
    asia_flood = int(t['type_continent'].loc['Flood', 'Asia'])
    africa_epidemic = int(t['type_continent'].loc['Epidemic', 'Africa'])
    europe_extreme = int(t['type_continent'].loc['Extreme temperature', 'Europe'])
    raw_name_missing = int(raw['Event Name'].isna().sum())
    jan_type = df[df['Start Month'].eq(1)].groupby('Disaster Type').size().sort_values(ascending=False)
    jan_text = '、'.join(f'{name} {count:,} 条' for name, count in jan_type.head(3).items())
    country_loss = countries.sort_values('reported_damage_thousand_usd', ascending=False)
    top3_loss_share = country_loss.head(3)['reported_damage_thousand_usd'].sum()/damage_total*100
    text = f'''# 全球自然灾害记录的多维度分析

[English report](case-study.en.md) · [项目首页](../README.md)

## 摘要

本研究围绕自然灾害记录的长期分布、地域差异与经济损失集中度，使用历史 CSV 数据进行探索性分析。
原始文件包含 **{len(raw):,} 行、{raw.shape[1]} 列**，覆盖 1970—2021 年；研究选取 **1970—2020 年**的
**{n:,} 条国家级灾害影响记录**，涉及 **{summary['countries']} 个国家或地区**。
同一灾害可以影响多个国家，因此国家级影响记录数与独立事件数分别计算，避免混用。

主要发现包括：洪水与风暴合计占记录数的 **{flood_storm/n*100:.2f}%**；地域分布中亚洲的记录数量最多；
经济损失高度集中于少量已知损失记录，但该字段缺失率达到 **{summary['damage_missing_pct']:.2f}%**，
所以集中度和总额均只描述已有报告，不能代表未观测到的全部影响。
研究将数据质量作为分析的一部分，同时展示字段缺失、分组覆盖率和指标适用范围。

## 1. 研究背景与分析问题

灾害记录既描述自然事件，也包含各国收集、评估和报告灾情的过程。
仅统计发生次数，难以区分高频灾害与高损失灾害；仅比较经济损失，又可能忽略不同国家和类型的记录完整性。
因此，本研究从三个相互关联的问题展开：

1. **分布问题：** 不同年份、月份、国家和灾害类型的记录数量有哪些差异？
2. **影响问题：** 已报告经济损失主要集中在哪些类型、地区和国家级记录？
3. **可信度问题：** 哪些字段缺失较多，哪些比较容易受到报告覆盖和指标定义的影响？

本项目使用 Python、Pandas 和 NumPy 完成读取、校验与汇总，使用 Matplotlib 绘制分析图，
使用 Plotly 提供交互式国家排名。分析定位为描述性研究，关注可复现的统计事实及其解释边界。

## 2. 原始数据长什么样

### 2.1 来源、规模与记录粒度

数据来源登记为 [ALL NATURAL DISASTERS 1900-2021 / EOSDIS（Kaggle）](https://www.kaggle.com/datasets/brsdincer/all-natural-disasters-19002021-eosdis)。
实际使用的本地文件名为 `1970-2021_DISASTERS.csv`，其时间范围和字段结构以文件内容为准，
不能仅依据在线数据集标题推定本地文件覆盖了 1900 年以来的全部记录。
原始文件指纹见 [summary.json](summary.json)，来源和使用条件见 [数据说明](../docs/DATA.md)。

数据是一张宽表：每行记录一次灾害在一个国家的影响，每列描述标识、类型、位置、时间或损失信息。
`Dis No` 的格式为 `年份-事件序号-国家代码`。例如，同一事件若影响两个国家，可以对应两个不同的国家后缀。
窗口内有 **{summary['distinct_event_ids']:,} 个去除国家后缀后的不同事件编号**，与 {n:,} 条国家级记录并不相等。
本报告所有频次图均采用国家级影响记录这一统一粒度。

### 2.2 字段结构

| 字段组 | 代表字段 | 在分析中的用途 |
|---|---|---|
| 标识与分类 | `Dis No`、`Disaster Group`、`Disaster Type`、`Disaster Subtype`、`Event Name` | 唯一性验证、灾害分类与记录追踪 |
| 国家与地理 | `Country`、`ISO`、`Region`、`Continent`、`Location`、经纬度 | 国家和大洲层面的分组比较 |
| 时间 | `Year`、`Start Year`、`Start Month`、`Start Day`、结束年月日 | 研究窗口、年度及月份分布 |
| 人员影响 | `Total Deaths`、`No Injured`、`No Affected`、`No Homeless`、`Total Affected` | 评估记录完整性，汇总已报告影响 |
| 经济影响 | 总损失、保险赔付、重建成本、`CPI` | 统计已报告名义损失，识别跨期比较限制 |
| 响应及补充信息 | `Appeal`、`Declaration`、援助金额、关联灾害、行政区代码 | 理解记录背景；不作为主要比较指标 |

读入时，{sum(raw.dtypes == 'object')} 个字段表现为文本类型，其余字段为整数或浮点数。
浮点数字段不一定是连续测量值：月份、人数等整数概念在存在空值时也可能以浮点数存储。
例如 `Start Month = 7.0` 表示 7 月，而不是具有小数精度的时间测量。

### 2.3 表格结构示意

下表为**人为构造的结构示例，不是原始灾害记录**，仅用于解释字段及空值含义。

| Dis No | Year | Disaster Type | Country / ISO | Start Month | Total Deaths | Total Damages ('000 US$) |
|---|---|---|---|---|---|---|
| 2000-0001-AAA | 2000 | Flood | 示例国家 A / AAA | 7 | 12 | 25000 |
| 2000-0001-BBB | 2000 | Flood | 示例国家 B / BBB | 7 | 空值 | 8000 |
| 2000-0002-AAA | 2000 | Storm | 示例国家 A / AAA | 空值 | 0 | 空值 |

前两行属于同一事件在不同国家的影响。第三行死亡人数为 0，表示字段中记录了零值；
第二行死亡人数空白则表示未知，两者不能等同。经济损失单位为**千美元**：示例中的 25000 对应 2500 万美元。
`Event Name` 是可选名称，原始文件有 **{raw_name_missing:,} 条、{raw_name_missing/len(raw)*100:.2f}%**记录没有名称，
因此它适合辅助辨识，不能作为统计记录总数的计数字段。

### 2.4 原始字段完整性

下表列出原始 {len(raw):,} 行中缺失最多的六个字段。它们反映出数据虽宽，但信息密度差异很大。

{raw_missing_table}

重建成本、援助金额等字段只在少部分记录中出现，不适合据此对所有类型或国家直接排名。
主分析因此围绕标识、年份、地理分组、类型、主要影响字段和开始月份展开；原始字段在本地保留，
并非为了得到一张没有空值的表而统一填充或删除记录。

## 3. 数据清洗与指标构建

### 3.1 清洗流程

处理顺序为：**读取原始文件 → 检查字段 → 标准化文本 → 解析数值 → 筛选年份 → 校验编号与分组键 → 校验影响值与月份 → 构建分析字段**。

| 处理环节 | 具体规则 | 对分析的意义 |
|---|---|---|
| 必要字段检查 | 年份、记录编号、国家、大洲、灾害类型及主要影响字段必须存在 | 避免结构变化后仍按旧口径运行 |
| 文本标准化 | 去除首尾空格，空字符串作为未知 | 防止 `Extreme temperature` 与带尾空格的标签被拆成两类 |
| 数值解析 | 年份、月份、死亡、受影响人数及损失显式转为数值；非空但无法解析的值触发错误 | 避免错误值被悄悄当作有效数据 |
| 年份筛选 | 所有模块统一为 1970—2020 | 保持各图总体一致，不将未经确认完整的 2021 年与其他年份直接比较 |
| 编号验证 | 国家级编号必须非空且唯一，结构与 ISO 后缀一致 | 保证记录追踪与分组逻辑一致 |
| 影响值校验 | 人数与损失不得为负数或无穷大 | 识别不合理数值，不将其带入求和 |
| 月份校验 | 仅接受 1—12 的整数；未知保留为空，非法值计入质量摘要 | 避免人为制造月份或季节峰值 |
| 特征构建 | 从编号提取 `Event_ID`，由年份得到 `Decade`，标记非法月份 | 支持粒度核验与时间汇总 |

原始文件有 {len(raw):,} 条记录；排除窗口外的 **{summary['excluded_outside_window']:,} 条**后保留 {n:,} 条。
原始数据的整行重复数为 **{int(raw.duplicated().sum())}**；窗口内国家级编号通过唯一性检查。
实际发现的非法月份为 **{summary['invalid_month_records']} 条**，有效月份未知的记录为 **{summary['month_unknown_records']:,} 条**。
本流程不把缺失影响记录整行删除，使记录频次仍覆盖完整的分析总体。

### 3.2 缺失值策略

人员伤亡和经济损失的未知值保留为空。原因是没有报告不代表没有损失，
填零会同时影响总额、平均值和“无伤亡”记录比例。按月份作图时，仅排除该图所需月份未知的记录，
这些记录仍参与年度、类型和国家频次分析。

聚合采用两种不同的有效样本：**计数使用全部国家级记录，损失统计使用损失已知记录**。
经济损失全为空的分组，其总额显示未知；有部分有效损失的分组，报告已知金额及相应覆盖率。
这一区分确保“已知部分之和”不会被误读为“全部真实损失”。

### 3.3 指标定义

| 指标 | 计算方式 | 分母或单位 |
|---|---|---|
| 国家级记录数 | 按唯一国家级记录逐行计数 | 条记录；包括没有事件名称的行 |
| 记录占比 | 某组记录数 / 对应总体记录数 | 依分析模块标明总体 |
| 损失覆盖率 | 某组经济损失非空记录数 / 该组全部记录数 | 百分比；真实零值算已知 |
| 已报告经济损失 | 对已知损失求和 | 原字段千美元；图中十亿美元 |
| 损失集中度 | 按损失降序，累计达到 80% 损失的最小记录数 / 损失已知记录数 | 仅适用于损失已知样本 |
| 月份占比 | 某开始月份记录数 / 开始月份有效记录数 | 排除月份未知记录 |

经济损失没有进行通胀调整。原始表中虽有 CPI 字段，但在价格基期与换算口径未充分核实前，
本研究保持名义金额含义，不将其标注为不变价损失。极端高损失记录保留，
因为损失集中度本身就关注分布尾部；高值需要核验，不因数值大就自动判为异常并删除。

## 4. 分模块分析

### 4.1 时间维度：记录数量如何变化

![图 1：历年国家级灾害影响记录数](figures/01_annual_records.png)

**图表含义。** 横轴为年份，纵轴为国家级灾害影响记录数。每个点统计该年的全部记录，
而不是统计有名称、有损失或有死亡人数的子样本。

**观察结果。** 曲线在 1970 年代处于较低水平，随后总体抬升，
到 **{year_peak} 年达到 {int(annual.loc[year_peak, 'records']):,} 条**的窗口内最高值。
2000 年以后维持较高水平，但并非逐年增加：曲线存在明显回落与反弹。
以完整十年区间比较，可以更清楚地区分长期分布与单年波动：

{decade_table}

**解读。** 2000—2009 年记录规模高于其他完整十年区间，而 2010—2019 年低于其前一个十年，
所以不能将整段历史概括为“灾害频次持续单调上升”。
更准确的表述是：本数据中的记录数量在早期与后期之间存在明显差异，后期内部仍有较大波动。

**解释边界。** 该曲线同时受灾害发生、国家级影响范围、历史资料保存及报告制度影响。
缺少稳定报告覆盖的对照资料时，它不能单独识别气候变化效应，
也不能把后期记录下降解释为防灾政策的因果效果。2020 年仅为一个年度，未与完整十年总数并列比较。

### 4.2 类型维度：高频灾害与高损失灾害是否一致

![图 2：灾害类型记录数](figures/02_disaster_types.png)

**图表含义。** 各类型按记录数排序，直观比较发生在国家层面的已记录影响数量。
图表保留低频类别，防止将尾部类别隐去后误认为总体只包含常见灾害。

{type_table}

**观察结果。** 洪水和风暴分别有 {int(types.set_index('Disaster Type').loc['Flood', 'records']):,} 条与
{int(types.set_index('Disaster Type').loc['Storm', 'records']):,} 条记录，合计占全部记录的 {flood_storm/n*100:.2f}%，
是频次结构中的主要组成部分。但频次排序不等于损失排序：风暴的已报告经济损失总额高于洪水，
地震记录数量虽明显更少，已报告损失总额仍接近洪水。

**解读。** 高频类型与高损失类型需要分开观察。频次指标适合识别经常出现的记录类别，
损失指标适合描述已知经济影响的规模；两者结合比单独以“最多”或“最严重”概括更有信息。

**解释边界。** 类型之间的损失覆盖率并不相同。Epidemic 在此窗口没有有效经济损失值，
其损失总额应理解为未知，而不是零。不能用缺少记录的类型与记录较充分的类型直接作真实经济危害排名。
同样，人员影响字段覆盖不同，未经控制的单次平均死亡人数也不足以建立统一的致命性排序。

### 4.3 数据质量：哪些影响被充分记录

![图 3：主要字段缺失比例](figures/03_missingness.png)

**图表含义。** 横轴表示字段缺失占全部 {n:,} 条国家级记录的比例；不同字段分别计算。

{quality_table}

**观察结果。** 经济损失是四个主要分析字段中缺失最多的一项，仅 {p['observed_records']:,} 条记录可用于损失分析。
死亡人数和受影响人数的缺失也不可忽略，而开始月份相对完整。
因此，同一份数据支持的“记录分布”与“影响分布”拥有不同的有效样本规模。

**解读。** 缺失不是一个只在清洗阶段处理完就能忽略的问题，而会持续影响结论。
例如，某地区记录数较多但损失覆盖率较低，其损失总额未必与已记录数量成比例；
某类型没有经济金额，也不能由此断定它经济危害轻微。

**解释边界。** 本研究没有证明缺失满足随机机制。因此不能将已知损失记录视为全体记录的无偏样本，
也没有用均值填补全部未知损失。若要估算完整损失，需要额外资料、缺失机制假设与敏感性分析。

### 4.4 损失结构：少量记录是否贡献大部分已知损失

![图 4：已报告经济损失集中度](figures/04_loss_concentration.png)

**图表含义。** 将有经济损失数值的记录按金额从大到小排列。
横轴是纳入的记录比例，纵轴是其累计贡献的已报告损失比例；曲线越早接近高位，损失越集中。
图中横向虚线为 80% 损失阈值，纵向参考线对应达到这一阈值的最小记录比例。

**观察结果。** 在 {p['observed_records']:,} 条有损失数据的国家级记录中，前 **{p['top_records']:,} 条、{p['top_share_pct']:.2f}%**
就贡献了已报告损失的 80%。这说明该样本呈明显的长尾结构：大量金额较小的记录构成数量基础，
少量大额记录支配了总金额。

**解读。** 比较总体损失时，均值容易被尾部记录牵动。分析者除了给出总额或平均数，
还应查看集中度、分位数和高损失记录的分布背景。
在后续风险研究中，这一结构可以帮助确定重点核验对象与情景研究方向，但不直接给出最优预算分配。

**解释边界。** 分母是损失已知的国家级记录，不是全部 {n:,} 条记录，
也不是去重后的独立灾害事件。真实零损失若被记录则仍进入分母；未知记录不进入。
因此不能把这一结果简写为“全球 10% 的灾害造成 80% 的全部损失”。
此外，排序使用名义美元，跨年代价格差异仍可能影响集中度的具体数值。

### 4.5 经济影响：年度损失与报告覆盖共同变化

![图 5：历年已报告经济损失与损失覆盖率](figures/05_loss_and_coverage.png)

**图表含义。** 上图展示各年已报告经济损失总额，单位为十亿美元；下图展示当年全部记录中，
经济损失字段已知的比例。二者共享年份轴，便于同时观察金额与样本完整性。

**观察结果。** 最高金额出现在 **{loss_peak} 年，约 {annual.loc[loss_peak, 'reported_damage_thousand_usd']/1e6:,.2f} 十亿美元**；
另一个突出峰值为 **{loss_second} 年，约 {annual.loc[loss_second, 'reported_damage_thousand_usd']/1e6:,.2f} 十亿美元**。
曲线并不是平滑增长，而是由若干高金额年度形成尖峰，这与损失分布受少量尾部记录影响的结构相一致。
这里的“一致”仅指统计表现相容，不代表已逐条确认各峰值由哪些事件造成。

覆盖率曲线也有明显波动，**{low_cover} 年仅为 {coverage_low:.2f}%**。
这意味着当年已报告金额只来自少部分记录。即使某一年的金额较低，也不能在覆盖不足时直接认定实际损失较轻。

**解读。** 将金额和覆盖率放在同一分析模块，可避免只看一条损失曲线就作结论。
金额峰值应结合当年已知记录、类型构成及极端值进一步核验；
跨期比较则需要同时控制价格水平、资产暴露和报告覆盖变化。

**解释边界。** 本图显示名义已报告总额，不是全球真实总额，也不是不变价损失或单位资产损失率。
本研究不将金额增加归因于灾害物理强度增强，也不把某年减少解释为风险治理成效。

### 4.6 月份分布：记录是否集中在某些日历月份

![图 6：按开始月份划分的国家级记录数](figures/06_calendar_month.png)

**图表含义。** 以灾害记录的开始月份分组，有效月份样本共 {valid_month:,} 条，
其余 {summary['month_unknown_records']:,} 条月份未知记录不进入本图。

{month_table}

**观察结果。** 1 月记录数最高，为 {monthly.loc[1]:,} 条；7 月和 8 月也处于较高水平，
分别为 {monthly.loc[7]:,} 条与 {monthly.loc[8]:,} 条。
1 月的前三类记录为 {jan_text}，说明月份峰值包含不同灾害类型的共同贡献，
不能仅从总量曲线把它归结为某一种天气现象。

**解读。** 月份分布适合作为细分分析的起点：继续按国家、纬度或类型拆分，
才能判断某个地区是否存在稳定的灾害季节性。全球汇总反映的是不同气候带、半球与灾害类型的混合分布。

**解释边界。** 南北半球季节相反，不能统一把 6—8 月标为全球夏季。
对于长期缓发灾害，开始月份的记录约定也可能与突发事件不同；本项目没有据此验证气候机制。
月份计数没有按每月天数标准化，表示记录数量而非每日发生率。

### 4.7 地域与类型：不同大洲的记录结构有何差异

![图 7：灾害类型与大洲交叉分布](figures/07_type_continent.png)

**图表含义。** 行为灾害类型，列为大洲，单元格为国家级影响记录数。
色块深浅和格内数字共同呈现绝对数量，零值表示当前样本没有该组合记录。

{continent_table}

**观察结果。** 亚洲的记录总数最多，洪水记录为 {asia_flood:,} 条，是图中数量最突出的组合。
非洲的流行病记录为 {africa_epidemic:,} 条，在该类型与大洲的交叉比较中十分突出；
欧洲有 {europe_extreme:,} 条极端温度记录，显示其记录构成与其他大洲存在差异。
已报告经济损失的地域分布也不与记录占比完全一致：亚洲与美洲的金额占比明显高于非洲。

**解读。** 热力图帮助发现值得进一步拆分的区域—类型组合，
而大洲汇总表使频次、金额与数据覆盖可以放在一起比较。
非洲损失覆盖率较低，特别提示不能将较小的已报告金额解释为较低的真实经济风险。

**解释边界。** 本图比较的是绝对记录数，没有按国家数量、人口、面积或资产总量进行标准化。
所以“记录多”不同于“个体面临风险高”。历史分类与地区命名沿用数据快照，
不把零记录解读为该地区不存在相应灾害。

### 4.8 国家层面：频次排名与损失排名的差别

![图 8：国家级记录数量前十](figures/08_country_records.png)

[打开交互式国家排名](figures/08_country_explorer.html)可查看记录数量前二十的国家及其损失覆盖率、已报告金额。
HTML 文件内嵌绘图库，下载后可离线打开；下表提供无需交互即可查阅的关键数值。

{country_table}

**观察结果。** 美国、中国、印度位居国家级记录数前三，分别为
{int(countries.iloc[0]['records']):,}、{int(countries.iloc[1]['records']):,} 和 {int(countries.iloc[2]['records']):,} 条。
已报告经济损失金额前三则为美国、中国和日本，合计占全部已报告损失的 **{top3_loss_share:.2f}%**。
日本的记录数并未进入前三，但金额排序更靠前，再次说明记录频次与金额规模衡量不同方面。

**解读。** 国家层面的比较需要至少同时观察数量、金额和覆盖率。
数量适合描述在本数据中出现了多少次国家级影响，金额描述有数值记录的部分造成多大经济损失，
覆盖率则说明金额依据是否充分。三项指标结合，能减少单一榜单带来的误读。

**解释边界。** 国家榜单不是“最危险国家”排名，也不是人均损失或单位 GDP 风险排名。
不同国家的资产价格、国土面积、人口及历史报告能力都会影响可观察结果。

## 5. 综合讨论与进一步分析方向

### 5.1 高频记录和尾部损失需要同时观察

洪水与风暴主导记录数量，但少量大额记录又主导已报告金额。
因此，研究灾害结构时不能只选择“发生次数最多”或“平均损失最高”一个指标，
应将日常高频影响与尾部金额风险分开描述，再结合地区和类型细分。

### 5.2 数据覆盖是解释结果的必要条件

损失缺失超过六成，且类型、地区与年份之间覆盖差异明显。
本研究能够描述已报告影响的结构，但不能从当前表格直接恢复全部未知损失。
要扩展分析，可以引入覆盖率分层、分时期稳定样本对比，以及对缺失机制的敏感性研究。

### 5.3 从描述统计走向可比较的风险指标

若进一步回答“哪里风险更高”或“实际损失是否上升”，需要补充人口、面积、资产存量、价格指数及报告制度信息。
跨期金额应采用明确基期的价格调整；跨地区应选择符合问题的暴露分母；
对于因果问题，还需有合适研究设计，而不是依靠图表趋势推断原因。

## 6. 结论

1970—2020 年的 {n:,} 条国家级影响记录呈现出明显的时间、地域与类型差异。
洪水和风暴构成记录频次主体，亚洲的记录数最多，
而已报告损失在国家与记录层面都表现出较强集中性。
与此同时，经济损失字段的大量缺失、历史报告覆盖差异和名义价格水平，决定了这些结果应当作为历史记录的结构描述，
而不是直接解释为全球真实风险的完整排序或因果变化。

本项目通过保留记录编号、显式区分未知与零值、同时呈现金额与覆盖率，
使分布统计、集中度分析与结果解读建立在一致的总体和指标定义上。

## 参考资料

- [Kaggle：ALL NATURAL DISASTERS 1900-2021 / EOSDIS](https://www.kaggle.com/datasets/brsdincer/all-natural-disasters-19002021-eosdis)
- [EM-DAT：国家级灾害影响记录结构](https://doc.emdat.be/docs/data-structure-and-content/core-structure-of-the-database/)
- [EM-DAT：公开表字段说明](https://doc.emdat.be/docs/data-structure-and-content/emdat-public-table/)
- [EM-DAT：缺失数据说明](https://files.emdat.be/docs/20240725%20Caveat%20of%20missing%20data%20in%20EM-DAT.pdf)

复现入口为 `python -m src.run`；各图对应汇总数据位于 [tables](tables/)，
输入文件指纹、分析窗口与关键数字保存在 [summary.json](summary.json)。
'''
    (Path(output) / 'case-study.zh-CN.md').write_text(text, encoding='utf-8')
