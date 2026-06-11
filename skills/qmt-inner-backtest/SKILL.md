---
name: qmt-inner-backtest
description: >-
  根据策略描述、研报 PDF 或截图，解读因子/选股逻辑，基于 scripts/daily-factors-backtest.py
  框架生成 QMT 内置日频因子回测脚本。用户提到 QMT 内置回测、因子选股回测、截面因子、
  研报复现、handlebar 回测、after_init 预计算信号时使用。
---

# QMT 内置因子回测

## 概述

基于 `scripts/daily-factors-backtest.py` 生成 **QMT 策略编辑器内置回测** 脚本。

核心模式：**`after_init` 预计算全区间因子与买卖信号 → `handlebar` 按调仓日执行交易**。

母版路径：本 skill 目录下的 `scripts/daily-factors-backtest.py`（相对 SKILL.md 所在目录）

## 适用场景

| 适合 | 不适合 |
|------|--------|
| 日频截面因子选股（Barra 风格处理） | Tick/分钟高频 |
| 固定持仓数 Top-N 等权调仓 | 期货开平仓（`qmt-future-trade`，规划中） |
| 研报因子复现、上下影线/价值/动量等 | 目标持仓型期货实盘（`qmt-live-strategy-template`，规划中） |
| 申万行业 + 市值中性化 | 仅要信号推送（`qmt-live-signal-feishu`，规划中） |

## 母版架构（必须理解再改）

```
daily-factors-backtest.py
├── 文件头 # coding:gbk + 策略说明 docstring
├── 因子函数库          ← 【主要替换区】factor_xxx + 中性化/去极值
├── init(C)             ← 【配置区】回测区间、股票池、资金、因子参数
├── after_init(C)       ← 【信号区】拉数据 → 算因子 → 过滤 → 生成 g.buy/sell_signals
├── handlebar(C)        ← 【执行区】调仓日卖出/买入（通常保留）
├── 交易执行函数         ← 通常原样保留
└── 辅助工具函数         ← 通常原样保留（IPO/ST/涨跌停/财务宽表）
```

### 各段职责

| 段 | 函数/变量 | 做什么 |
|----|-----------|--------|
| 全局状态 | `g = G()` | 跨函数共享参数、信号矩阵、持仓 |
| 因子库 | `factor_ubl(...)` | 输入 OHLCV/市值等宽表，输出因子 DataFrame（index=日期, columns=股票） |
| 因子后处理 | `filter_extreme_mad_df` / `neutralize_by_market_cap` / `neutralize_by_industry_zscore` / `cross_section_zscore` | Barra 风格流水线，按研报需求保留或删减 |
| 初始化 | `init(C)` | 设 `g.start_date`/`g.end_date`、`g.stock_pool`、`g.max_positions`、`g.rebalance_days` 等；**预定义** `g.buy_signals`/`g.sell_signals` 防空矩阵 |
| 预计算 | `after_init(C)` | 一次性拉全区间行情+财务 → 算因子 → IPO/ST/停牌过滤 → 截面排名 → `shift(1)` 生成 T+1 信号 |
| 执行 | `handlebar(C)` | 每 `g.rebalance_days` 个交易日调仓：先卖后买，开盘价成交 |
| 交易 | `execute_sell/buy_signals` | 涨停不买、跌停不卖；科创板 200 股、其余 100 股整数倍 |
| 辅助 | `get_ipo_mask` / `get_st_mask` / `get_financial_wide_table` | 上市满 120 天、ST 区间、财务字段宽表 |

### 信号时序（防未来函数）

```python
df_rank = df_factor_filtered.rank(axis=1, ascending=g.rank_ascending)
df_is_top_n = df_rank <= g.max_positions
g.buy_signals = df_is_top_n.shift(1).fillna(False)   # T 日因子 → T+1 日买入
g.sell_signals = ~g.buy_signals
```

**禁止**去掉 `.shift(1)`，除非用户明确要求当日收盘调仓且接受前视偏差。

## Agent 工作流

### 1. 解读策略输入

用户可能提供：文字描述、研报 PDF、截图、已有因子公式。提取并输出 **策略规格表**（生成前给用户确认）：

```markdown
## 策略规格（待确认）

| 项 | 内容 |
|----|------|
| 策略名称 | |
| 因子公式 | 逐行写明计算步骤 |
| 所需行情字段 | open/high/low/close/volume/... |
| 所需财务字段 | 如 CAPITALSTRUCTURE.free_float_capital |
| 因子窗口 | std_period / factor_period 等 |
| 排序方向 | ascending=True（值越小越好）或 False |
| 中性化 | 市值 OLS / 申万行业 Z-score / 无 |
| 股票池 | 如 中证1000、沪深300、全 A |
| 持仓数 | max_positions |
| 调仓频率 | rebalance_days（交易日） |
| 回测区间 | start_date ~ end_date |
| 初始资金 | initial_capital |
```

**研报/PDF 解读要点：**
- 区分「因子定义」与「组合构建」（Top 10、5 日调仓等）
- 注意「蜡烛上影线」「威廉下影线」等术语对应的 OHLC 公式
- 记录去极值方法（MAD 几倍）、中性化顺序
- 参数缺省时标注假设，不要静默编造

**截图解读要点：**
- 对照图中公式、参数表、回测设置截图
- 股票池名称必须与 QMT 板块名一致（见下方板块表）

### 2. 复制母版并替换

1. 读取 `scripts/daily-factors-backtest.py` 全文作模板
2. 输出到用户指定路径，默认 `strategies/<策略名>-backtest/backtest.py`
3. **只改必要部分**，交易执行与辅助函数原样保留

**必改清单：**

| 位置 | 改什么 |
|------|--------|
| 文件头 docstring | 策略名、研报来源、因子逻辑、参数说明 |
| `logger` 名称 | 与策略一致，便于日志过滤 |
| `factor_xxx()` | 新因子计算；函数名与 `g.factor_name` 对应 |
| `init()` | 回测区间、股票池、资金、因子参数、`rank_ascending` |
| `after_init()` | 数据字段获取、调用新因子函数；中性化步骤按研报增删 |
| `init` 日志文案 | 策略名称与参数摘要 |

**通常不改：** `handlebar`、`execute_*`、`get_ipo_mask`、`get_st_mask`、涨跌停判断、`get_df_ex`。

### 3. 因子替换模式

**模式 A — 单因子 Top-N（母版默认）**

```python
def factor_xxx(daily_open, daily_high, daily_low, daily_close, daily_market_cap,
               stock_industry_map=None, **kwargs):
    # 1. 原始特征
    # 2. 滚动统计
    # 3. 去极值 → 市值中性 → 行业中性（可选）
    # 4. 截面 Z-score（单因子可跳过第 4 步）
    return factor_df
```

**模式 B — 多子因子合成**

每个子因子独立走 MAD + 中性化，最后 `zscore(A) + zscore(B)` 或加权求和。

**模式 C — 无需中性化**

跳过 `neutralize_by_*`，仅 `filter_extreme_mad_df` + `cross_section_zscore`。

**模式 D — 需额外财务因子**

在 `after_init` 用 `get_financial_wide_table(C, g.stock_pool, 'TABLE.field', ...)` 拉宽表，传入 `factor_xxx`。

常用财务字段示例：
- `CAPITALSTRUCTURE.free_float_capital` — 自由流通股本（母版用于市值）
- `PERSHAREINDEX.eps` — 每股收益
- `ASHAREINCOME.net_profit_incl_min_int_inc` — 净利润

### 4. 生成后自检

- [ ] 首行 `# coding:gbk`
- [ ] `init` 中预定义 `g.buy_signals` / `g.sell_signals` 空 DataFrame
- [ ] `after_init` 行情为空时 `return`，不抛未捕获异常
- [ ] 信号含 `.shift(1)`
- [ ] `g.start_date` 与 `g.backtest_start_time` 区间一致
- [ ] 股票池 `C.get_stock_list_in_sector(...)` 名称在 QMT 中存在
- [ ] 因子函数返回值 shape 与 `daily_close` 对齐（index=日期, columns=股票代码）
- [ ] `rank_ascending` 与研报「因子越大越好/越小越好」一致

## 用户必须配置的回测项

生成脚本后，**必须提醒用户**在 QMT 中核对以下配置（Agent 不代替用户在 QMT GUI 操作）：

### A. 脚本内 `init()` 参数

| 参数 | 格式 | 说明 |
|------|------|------|
| `g.start_date` / `g.end_date` | `'YYYYMMDD'` | `after_init` 拉行情/财务的起止 |
| `g.backtest_start_time` / `g.backtest_end_time` | `'YYYY-MM-DD HH:MM:SS'` | 与上面区间一致 |
| `g.stock_pool` | 板块名或代码列表 | `C.get_stock_list_in_sector("中证1000")` |
| `g.initial_capital` | 整数 | 初始资金 |
| `g.max_positions` | 整数 | 持仓只数 = Top N |
| `g.cash_usage_ratio` | 0~1 | 调仓日可用资金比例，默认 0.95 |
| `g.rebalance_days` | 整数 | 每 N 个交易日调仓一次 |
| `g.accid` | `'test'` | 回测账号，保持 test |

### B. QMT 策略编辑器回测面板

用户需在 QMT **模型交易 / 策略研究** 中手动设置：

1. **回测起止日期** — 与脚本 `g.backtest_*` 一致
2. **初始资金** — 与 `g.initial_capital` 一致
3. **基准** — 如沪深300、中证1000（便于对比）
4. **手续费 / 印花税 / 滑点** — 研报有写明则告知用户按研报设
5. **复权方式** — 脚本内 `dividend_type='front_ratio'`（前复权），面板需一致
6. **品种类型** — 股票

### C. 常用 QMT 板块名称

| 用户说法 | QMT sector 名 |
|----------|---------------|
| 中证1000 | `"中证1000"` |
| 沪深300 | `"沪深300"` |
| 中证500 | `"中证500"` |
| 全 A | `"沪深A股"` |
| 创业板 | `"创业板"` |
| 科创板 | `"科创板"` |
| 申万一级行业 | `get_sector_list('申万一级行业板块')` 下各行业 |

板块名因 QMT 版本可能略有差异；若 `get_stock_list_in_sector` 失败，提示用户在本机 QMT 板块列表中确认准确名称。

### D. 数据前置

1. QMT 客户端已登录
2. 在「数据管理」中下载回测区间 **日线行情** 及所需 **财务数据**
3. 股票池成分股越多，`after_init` 越慢（中证1000 约 1000 只，属正常）

## 运行方式

QMT 内置回测 **不在 conda 命令行运行**，流程如下：

1. 将生成的 `.py` 复制到 QMT 策略目录，或在策略编辑器新建策略粘贴代码
2. 保存后点击 **编译**，确认无语法错误
3. 打开 **回测** 面板，设置日期/资金/费率
4. 运行回测，查看收益曲线、持仓、日志输出
5. 日志中关注：`[数据检查]`、`[因子]` 步骤统计、`【最新调仓建议】`

若用户需要在项目内留存：

```text
strategies/<name>-backtest/
└── backtest.py    # 生成的策略文件
```

## 向用户确认的话术模板

策略生成前：

> 请确认策略规格表中的：股票池、回测区间、持仓数、调仓频率、因子方向。  
> 若有研报未写明的参数（如 MAD 倍数、中性化顺序），我将按母版默认处理并标注。

交付脚本后：

> 脚本已生成。请在 QMT 中：
> 1. 核对回测起止日期与脚本 `init()` 一致  
> 2. 确认股票池板块名在本机 QMT 可用  
> 3. 下载对应区间的日线与财务数据  
> 4. 设置手续费/滑点（研报有要求请按研报）  
> 5. 编译运行回测  
>
> 默认 T 日收盘算因子、T+1 日开盘调仓。如需改调仓逻辑请说明。

## 与母版示例的对应关系

母版 `factor_ubl` 实现的是东吴证券上下影线因子：

```
蜡烛上影线 = High - max(Open, Close)
威廉下影线 = Close - Low
→ 标准化 → 20日 std/mean → MAD去极值 → 市值OLS中性 → 申万行业Z-score → 截面Z-score → 相加
→ 值越小越好 → Top 10 → 每5日调仓
```

替换其他因子时，保持相同「宽表进、宽表出」接口，其余流水线按研报裁剪。

## 禁止事项

- 不要去掉 `# coding:gbk`
- 不要去掉 `init` 中对信号变量的预定义
- 不要默认帮用户在 QMT 里点运行；只生成脚本并给配置清单
- 不要把期货下单逻辑混入本框架
- 不要在因子矩阵中引入未来数据（用 `shift(1)` 或等价滞后）
- 未经用户确认不要提交含资金账号的改动

## 快速示例

**用户需求：** 复现 20 日动量因子，沪深300成分，Top 20，每月调仓。

**Agent 动作：**
1. 输出策略规格表供确认
2. 新建 `factor_momentum(daily_close, lookback=20)`：`daily_close / daily_close.shift(20) - 1`
3. MAD 去极值 + 市值中性（研报若要求）
4. `g.rank_ascending = False`（动量越大越好）
5. `g.stock_pool = C.get_stock_list_in_sector("沪深300")`
6. `g.max_positions = 20`，`g.rebalance_days = 20`（约月度）
7. 提醒用户下载沪深300成分日线及设置回测费率
