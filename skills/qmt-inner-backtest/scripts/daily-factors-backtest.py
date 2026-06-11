# coding:gbk
"""
QMT 单因子策略
策略描述：中证1000成分股 UBL上下影线综合因子策略

研报来源：东吴证券《技术分析拥抱选股因子（二）：上下影线，蜡烛好还是威廉好？》
因子逻辑：
- 蜡烛上影线小 → 抛压小 → 后续上涨概率大
- 威廉下影线小 → 买气弱 → 结合蜡烛上影线效果更好
- UBL = zscore(蜡烛上_std) + zscore(威廉下_mean)

因子处理流程（Barra风格）：
1. 去极值 (MAD 3倍标准差) - 截断极端值，MAD=0时保留原值
2. 市值中性化 (OLS回归取残差) - 使用自由流通市值，样本<10或分母=0时保留原值
3. 行业中性化 (申万一级行业内Z-score) - 行业样本<3或未匹配行业时保留原值
4. 截面标准化 (Z-score) - std=0时返回0

容错设计：
1. init 中预定义所有信号变量，防止 after_init 失败导致 handlebar 崩溃
2. 数据获取失败时静默跳过，不中断策略运行
3. get_ipo_mask/get_st_mask 处理 None/无效日期
4. 数据缺失时输出汇总日志，便于排查
5. 每个处理步骤输出详细统计日志（数据点数、处理比例、跳过原因）
"""
import sys
import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta

# 配置 logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('ubl_shadow')

class G():
    pass

g = G()

# ============================================================================
#                              因子函数库
# ============================================================================

def factor_ubl(daily_open, daily_high, daily_low, daily_close, daily_market_cap,
               stock_industry_map=None, std_period=5, factor_period=20):
    """UBL 上下影线综合因子

    结合蜡烛图上影线标准差和威廉下影线均值，市值中性化 + 行业中性化后综合。

    Args:
        daily_open: 开盘价 DataFrame
        daily_high: 最高价 DataFrame
        daily_low: 最低价 DataFrame
        daily_close: 收盘价 DataFrame
        daily_market_cap: 市值 DataFrame（用于市值中性化）
        stock_industry_map: 股票-行业映射表（用于行业中性化，None则跳过）
        std_period: 标准化窗口期（默认5日）
        factor_period: 因子计算窗口期（默认20日）

    Returns:
        UBL 因子值 DataFrame（值越小越好）
    """
    # ==================== 1. 计算原始影线 ====================
    # 蜡烛上影线 = High - max(Open, Close)
    candle_upper = daily_high - np.maximum(daily_open, daily_close)

    # 威廉下影线 = Close - Low
    william_lower = daily_close - daily_low

    # ==================== 2. 标准化（除以过去N日均值） ====================
    # 避免除零
    candle_upper_ma = candle_upper.rolling(std_period).mean()
    william_lower_ma = william_lower.rolling(std_period).mean()

    # 标准化
    candle_upper_std_raw = candle_upper / candle_upper_ma.replace(0, np.nan)
    william_lower_std_raw = william_lower / william_lower_ma.replace(0, np.nan)

    # ==================== 3. 计算子因子 ====================
    # 蜡烛上_std：过去20日标准化蜡烛上影线的标准差
    candle_upper_std = candle_upper_std_raw.rolling(factor_period).std()

    # 威廉下_mean：过去20日标准化威廉下影线的均值
    william_lower_mean = william_lower_std_raw.rolling(factor_period).mean()

    # ==================== 4. 去极值 (MAD) ====================
    logger.info("[步骤4] 去极值 (MAD 3倍标准差)...")
    logger.info("  处理子因子: candle_upper_std")
    candle_upper_std = filter_extreme_mad_df(candle_upper_std)
    logger.info("  处理子因子: william_lower_mean")
    william_lower_mean = filter_extreme_mad_df(william_lower_mean)

    # ==================== 5. 市值中性化 ====================
    logger.info("[步骤5] 市值中性化 (OLS回归)...")
    ln_cap = np.log(daily_market_cap.replace(0, np.nan))

    logger.info("  处理子因子: candle_upper_std")
    candle_upper_std_neutral = neutralize_by_market_cap(candle_upper_std, ln_cap)
    logger.info("  处理子因子: william_lower_mean")
    william_lower_mean_neutral = neutralize_by_market_cap(william_lower_mean, ln_cap)

    # ==================== 6. 行业中性化（可选） ====================
    if stock_industry_map:
        logger.info("[步骤6] 行业中性化 (申万一级行业内Z-score)...")
        logger.info("  处理子因子: candle_upper_std")
        candle_upper_std_neutral = neutralize_by_industry_zscore(candle_upper_std_neutral, stock_industry_map)
        logger.info("  处理子因子: william_lower_mean")
        william_lower_mean_neutral = neutralize_by_industry_zscore(william_lower_mean_neutral, stock_industry_map)
    else:
        logger.info("[步骤6] 行业中性化: 跳过（无行业映射表）")

    # ==================== 7. 截面标准化 + 综合 ====================
    logger.info("[步骤7] 截面标准化 + 综合...")
    candle_zscore = cross_section_zscore(candle_upper_std_neutral)
    william_zscore = cross_section_zscore(william_lower_mean_neutral)

    ubl = candle_zscore + william_zscore

    # 输出综合因子统计
    valid_count = ubl.notna().sum().sum()
    total_count = ubl.size
    valid_ratio = valid_count / total_count * 100 if total_count > 0 else 0
    logger.info(f"  [综合因子] 有效值 {valid_count}/{total_count} ({valid_ratio:.1f}%)")

    return ubl


def filter_extreme_mad(series, n=3):
    """MAD 去极值（容错版）

    Args:
        series: pd.Series 因子值
        n: MAD 倍数阈值，默认 3

    Returns:
        去极值后的 Series

    容错：
        - MAD = 0（所有值相同）→ 返回原值不处理
        - 空 Series → 返回原值
    """
    if series.empty or series.isna().all():
        return series

    median = series.median()
    mad = (series - median).abs().median()

    # 【容错】MAD = 0 说明值都相同，无需去极值
    if mad == 0 or pd.isna(mad):
        return series

    threshold = n * 1.4826 * mad
    upper = median + threshold
    lower = median - threshold
    return series.clip(lower, upper)


def filter_extreme_mad_df(factor_df, n=3):
    """对 DataFrame 每个截面做 MAD 去极值

    Args:
        factor_df: 因子值 DataFrame (index=日期, columns=股票)
        n: MAD 倍数阈值

    Returns:
        去极值后的 DataFrame
    """
    result = factor_df.copy()
    total_clipped = 0
    total_valid = 0

    for date in factor_df.index:
        row = factor_df.loc[date].dropna()
        if len(row) > 0:
            clipped_row = filter_extreme_mad(row, n)
            # 统计被截断的数量
            total_clipped += (clipped_row != row).sum()
            total_valid += len(row)
            result.loc[date, row.index] = clipped_row

    if total_valid > 0:
        clip_ratio = total_clipped / total_valid * 100
        logger.info(f"  [去极值] 处理 {total_valid} 个数据点，截断 {total_clipped} 个 ({clip_ratio:.2f}%)")

    return result


def neutralize_by_market_cap(factor_df, ln_cap_df):
    """市值中性化：OLS 回归取残差（容错版）

    Args:
        factor_df: 因子值 DataFrame
        ln_cap_df: ln(市值) DataFrame

    Returns:
        市值中性化后的因子 DataFrame

    容错：
        - 样本 < 10 → 保留原值
        - 市值全相同（分母=0）→ 保留原值
        - 回归失败 → 保留原值
    """
    result = factor_df.copy()

    total_dates = len(factor_df.index)
    processed_dates = 0
    skipped_sample = 0
    skipped_denominator = 0
    skipped_error = 0

    for date in factor_df.index:
        y = factor_df.loc[date].dropna()
        x = ln_cap_df.loc[date].reindex(y.index).dropna()

        common_stocks = y.index.intersection(x.index)
        if len(common_stocks) < 10:
            skipped_sample += 1
            continue

        y_common = y[common_stocks]
        x_common = x[common_stocks]

        try:
            x_mean = x_common.mean()
            y_mean = y_common.mean()

            # 【容错】分母为 0（市值全相同）→ 跳过，保留原值
            denominator = ((x_common - x_mean) ** 2).sum()
            if denominator == 0 or pd.isna(denominator):
                skipped_denominator += 1
                continue

            b = ((x_common - x_mean) * (y_common - y_mean)).sum() / denominator
            a = y_mean - b * x_mean

            # 计算残差
            residual = y_common - (a + b * x_common)
            result.loc[date, common_stocks] = residual
            processed_dates += 1

        except Exception:
            skipped_error += 1
            continue

    # 输出统计
    process_ratio = processed_dates / total_dates * 100 if total_dates > 0 else 0
    logger.info(f"  [市值中性化] 处理 {processed_dates}/{total_dates} 个截面 ({process_ratio:.1f}%)")
    if skipped_sample > 0:
        logger.warning(f"  [市值中性化] 跳过 {skipped_sample} 个截面 (样本<10)")
    if skipped_denominator > 0:
        logger.warning(f"  [市值中性化] 跳过 {skipped_denominator} 个截面 (市值无差异)")
    if skipped_error > 0:
        logger.warning(f"  [市值中性化] 跳过 {skipped_error} 个截面 (计算异常)")

    return result


def cross_section_zscore(df):
    """截面 Z-score 标准化

    Args:
        df: 因子值 DataFrame

    Returns:
        标准化后的 DataFrame
    """
    mean = df.mean(axis=1)
    std = df.std(axis=1)
    return df.sub(mean, axis=0).div(std.replace(0, np.nan), axis=0)


def build_stock_industry_map(C):
    """构建股票 -> 申万一级行业的映射表（容错版）

    Returns:
        dict: {stock_code: industry_name}，获取失败返回空字典
    """
    stock_industry_map = {}

    try:
        sector_list = get_sector_list('申万一级行业板块')
        # 容错：返回格式可能是 [['SW1交通运输', ...], []] 或 None
        if not sector_list or not sector_list[0]:
            logger.warning("获取申万行业板块失败，行业中性化将跳过")
            return {}

        industries = sector_list[0]  # ['SW1交通运输', 'SW1传媒', ...]
        logger.info(f"获取到 {len(industries)} 个申万一级行业")

        for industry in industries:
            try:
                stocks = C.get_stock_list_in_sector(industry)
                if not stocks:
                    continue
                for stock in stocks:
                    stock_industry_map[stock] = industry
            except Exception:
                continue

        logger.info(f"行业映射表构建完成，覆盖 {len(stock_industry_map)} 只股票")

    except Exception as e:
        logger.warning(f"构建行业映射表失败: {e}，行业中性化将跳过")

    return stock_industry_map


def neutralize_by_industry_zscore(factor_df, stock_industry_map):
    """行业中性化：每个行业内部独立做 Z-score（容错版）

    优点：简单直观，每个行业选出的股票数量均衡

    Args:
        factor_df: 因子值 DataFrame
        stock_industry_map: {stock_code: industry_name} 映射表

    Returns:
        行业中性化后的因子 DataFrame

    容错处理：
        - 没有匹配到行业的股票 → 保留原值（不做行业中性化）
        - 行业内股票 < 3 只 → 保留原值
    """
    if not stock_industry_map:
        logger.warning("  [行业中性化] 映射表为空，跳过")
        return factor_df

    # 【关键】先复制原值，未匹配的股票保留原值
    result = factor_df.copy()

    # 统计
    total_stocks_processed = 0
    total_stocks_unmatched = 0
    total_stocks_skipped_small_ind = 0
    industries_processed = set()

    for date in factor_df.index:
        values = factor_df.loc[date].dropna()
        if values.empty:
            continue

        # 获取行业标签
        industries = pd.Series({s: stock_industry_map.get(s) for s in values.index})

        # 统计未匹配的股票
        unmatched_count = industries.isna().sum()
        total_stocks_unmatched += unmatched_count

        industries = industries.dropna()
        if industries.empty:
            continue

        # 按行业分组做 z-score
        for ind in industries.unique():
            ind_stocks = industries[industries == ind].index.tolist()

            # 行业内有效股票（有因子值的）
            valid_ind_stocks = [s for s in ind_stocks if s in values.index]
            if len(valid_ind_stocks) < 3:  # 行业内股票太少，保留原值
                total_stocks_skipped_small_ind += len(valid_ind_stocks)
                continue

            ind_values = values[valid_ind_stocks]
            mean = ind_values.mean()
            std = ind_values.std()

            if std > 0:
                result.loc[date, valid_ind_stocks] = (ind_values - mean) / std
            else:
                result.loc[date, valid_ind_stocks] = 0

            total_stocks_processed += len(valid_ind_stocks)
            industries_processed.add(ind)

    # 输出统计（汇总）
    total_all = total_stocks_processed + total_stocks_unmatched + total_stocks_skipped_small_ind
    if total_all > 0:
        process_ratio = total_stocks_processed / total_all * 100
        unmatched_ratio = total_stocks_unmatched / total_all * 100
        logger.info(f"  [行业中性化] 覆盖 {len(industries_processed)} 个行业")
        logger.info(f"  [行业中性化] 处理 {total_stocks_processed} 个数据点 ({process_ratio:.1f}%)")
        if total_stocks_unmatched > 0:
            logger.warning(f"  [行业中性化] 未匹配行业 {total_stocks_unmatched} 个数据点 ({unmatched_ratio:.1f}%)，保留原值")
        if total_stocks_skipped_small_ind > 0:
            logger.info(f"  [行业中性化] 行业样本<3 跳过 {total_stocks_skipped_small_ind} 个数据点，保留原值")

    return result


# ============================================================================
#                              策略主体
# ============================================================================

def init(C):
    """参数设定"""
    logger.info("=" * 50)
    logger.info("单因子策略初始化：UBL 上下影线综合因子")
    logger.info("=" * 50)

    # ------------------------回测参数设定-----------------------------
    g.start_date = '20240101'
    g.end_date = '20260123'
    g.backtest_start_time = '2024-01-01 00:00:00'
    g.backtest_end_time = '2026-01-23 00:00:00'
    g.period = '1d'

    # ------------------------股票池设定-----------------------------
    try:
        logger.info("正在获取股票池...")
        g.stock_pool = C.get_stock_list_in_sector("中证1000")[:]
        logger.info(f"成功获取股票池，包含 {len(g.stock_pool)} 只股票")
    except Exception as e:
        logger.warning(f"获取股票池时出错: {e}，使用默认备选池")
        g.stock_pool = ['000001.SZ', '000002.SZ', '000063.SZ']

    # ------------------------资金管理参数-----------------------------
    g.initial_capital = 1000000
    g.max_positions = 10
    g.cash_usage_ratio = 0.95
    g.rebalance_days = 5
    g.accid = 'test'

    # ------------------------预定义信号变量（容错设计）-----------------------------
    # 防止 after_init 报错导致 handlebar 崩溃
    g.buy_signals = pd.DataFrame()
    g.sell_signals = pd.DataFrame()
    g.daily_open = pd.DataFrame()
    g.daily_close = pd.DataFrame()

    # ------------------------因子参数-----------------------------
    g.factor_name = 'UBL'
    g.std_period = 5        # 影线标准化窗口
    g.factor_period = 20    # 因子计算窗口
    g.rank_ascending = True  # True=选最小的（UBL值小的优先）

    # ------------------------变量初始化-----------------------------
    g.money = g.initial_capital
    g.holdings = {}
    g.trade_records = []
    g.trade_day_count = 0

    logger.info(f"参数设置：回测区间 {g.start_date}~{g.end_date}")
    logger.info(f"资金管理：初始资金 {g.initial_capital:,}, 持仓 {g.max_positions} 只, 利用率 {g.cash_usage_ratio*100:.0f}%")
    logger.info(f"因子设置：{g.factor_name}, 标准化窗口 {g.std_period}, 因子窗口 {g.factor_period}")
    logger.info("=" * 50)

def after_init(C):
    """数据获取与因子计算"""
    logger.info("=" * 50)
    logger.info("数据获取与信号计算")
    logger.info("=" * 50)

    # ==================== 1. 获取行情数据 ====================
    logger.info("正在获取日频数据...")
    daily_data = C.get_market_data_ex([], g.stock_pool, period='1d',
                                     start_time=g.start_date, end_time=g.end_date,
                                     dividend_type='front_ratio', fill_data=False)

    daily_close_raw = get_df_ex(daily_data, "close")
    daily_open_raw = get_df_ex(daily_data, "open")
    daily_high_raw = get_df_ex(daily_data, "high")
    daily_low_raw = get_df_ex(daily_data, "low")
    daily_volume_raw = get_df_ex(daily_data, "volume")

    # 【容错】数据为空时提前返回
    if daily_close_raw.empty:
        logger.error("行情数据获取失败！策略将无法生成信号")
        return

    logger.info(f"获取到 {len(daily_close_raw)} 个交易日, {len(daily_close_raw.columns)} 只股票")

    # ==================== 数据质量体检 ====================
    total_cells = daily_close_raw.size # 总数据点数 (天数 * 股票数)
   
    # 1. 统计 NaN (真正意义上的缺失，通常是未上市或接口失败)
    real_missing = daily_close_raw.isna().sum().sum()
    missing_ratio = (real_missing / total_cells) * 100

    # 2. 统计成交量为 0 (剔除 NaN 后的 0，通常代表停牌)
    # daily_volume_raw == 0 会把 NaN 也判定为 False，所以这里统计的是纯 0
    zero_vol_count = (daily_volume_raw == 0).sum().sum()
    zero_vol_ratio = (zero_vol_count / total_cells) * 100

    if missing_ratio > 5: # 缺失超过 5% 设为 Error
        logger.error(f"[数据检查] 严重缺失! 空值比例: {missing_ratio:.2f}% ({real_missing}点)")
    elif missing_ratio > 0:
        logger.warning(f"[数据检查] 存在空值。空值比例: {missing_ratio:.2f}% ({real_missing}点)")

    if zero_vol_ratio > 0:
        # 停牌比例一般反映市场活跃度
        logger.info(f"[数据检查] 停牌统计。比例: {zero_vol_ratio:.2f}% ({zero_vol_count}点)")
    # ======================================================
   
    # 转换索引
    for df in [daily_close_raw, daily_open_raw, daily_high_raw, daily_low_raw, daily_volume_raw]:
        df.index = pd.to_datetime(df.index.astype(str))

    # 停牌掩码
    suspend_mask = daily_close_raw.isna()
    logger.debug(f"停牌数据点: {suspend_mask.sum().sum()}")

    # 填充数据用于因子计算
    daily_close = daily_close_raw.ffill()
    daily_open = daily_open_raw.ffill()
    daily_high = daily_high_raw.ffill()
    daily_low = daily_low_raw.ffill()
    daily_volume = daily_volume_raw.fillna(0)

    # ==================== 2. 获取市值数据（用于中性化） ====================
    logger.info("正在获取市值数据...")
    df_total_cap = get_financial_wide_table(
        C, g.stock_pool,
        # 'CAPITALSTRUCTURE.total_capital',  # 总股本
        'CAPITALSTRUCTURE.free_float_capital',  # 自由流通股本

        g.start_date, g.end_date
    )
    df_total_cap.index = pd.to_datetime(df_total_cap.index)

    # 对齐到日频索引，计算总市值
    df_total_cap_aligned = df_total_cap.reindex(daily_close.index).ffill()
    daily_market_cap = daily_close * df_total_cap_aligned  # 总市值 = 收盘价 * 总股本
    logger.info(f"市值数据获取完成，有效列数: {daily_market_cap.notna().any().sum()}")

    # ==================== 2.5 获取行业映射表（用于行业中性化） ====================
    logger.info("正在构建行业映射表...")
    stock_industry_map = build_stock_industry_map(C)

    # ==================== 3. 计算因子 ====================
    logger.info(f"计算因子: {g.factor_name}...")
    logger.info(f"  - 标准化窗口: {g.std_period} 日")
    logger.info(f"  - 因子窗口: {g.factor_period} 日")

    df_factor = factor_ubl(
        daily_open, daily_high, daily_low, daily_close, daily_market_cap,
        stock_industry_map=stock_industry_map,
        std_period=g.std_period, factor_period=g.factor_period
    )

    # ==================== 4. 过滤无效股票 ====================
    logger.info("过滤新股、ST、停牌...")
    target_index = df_factor.index
    ipo_mask = get_ipo_mask(C, g.stock_pool, target_index)
    st_mask = get_st_mask(C, g.stock_pool, target_index)
    suspend_mask_aligned = suspend_mask.reindex(target_index).fillna(False)

    # 【关键】因子计算后清除停牌日的因子值（停牌日不应参与排名）
    df_factor = df_factor.where(~suspend_mask_aligned)

    valid_mask = ipo_mask & (~st_mask) & (~suspend_mask_aligned)

    # ==================== 5. 排序生成信号 ====================
    df_factor_filtered = df_factor.where(valid_mask)
    df_rank = df_factor_filtered.rank(axis=1, ascending=g.rank_ascending)

    df_is_top_n = df_rank <= g.max_positions
    g.buy_signals = df_is_top_n.shift(1).fillna(False)
    g.sell_signals = ~g.buy_signals

    g.daily_open = daily_open
    g.daily_close = daily_close

    buy_signal_count = g.buy_signals.sum().sum()
    logger.info(f"信号生成完成: 回测天数 {len(g.buy_signals)}, 买入信号总数 {buy_signal_count}")
    logger.info("=" * 50)

    # ==================== 打印最新调仓建议 ====================
    # 获取信号矩阵中最后一个交易日
    last_date = g.buy_signals.index[-1]
    # 提取该日信号为 True 的股票
    last_day_targets = g.buy_signals.loc[last_date]
    target_list = last_day_targets[last_day_targets].index.tolist()

    logger.info("*" * 30)
    logger.info(f"【最新调仓建议】 目标日期: {last_date.strftime('%Y-%m-%d')}")
    if target_list:
        logger.info(f"建议持仓品种 (共{len(target_list)}只):")
        for i, stock in enumerate(target_list):
            name = C.get_instrument_detail(stock).get('InstrumentName', '未知')
            logger.info(f"  [{i+1}] {stock} ({name})")
    else:
        logger.warning("最新日期无买入信号！")
    logger.info("*" * 30)

def sync_from_qmt(accid):
    """从 QMT 同步持仓和资金"""
    try:
        positions = get_trade_detail_data(accid, 'stock', 'POSITION')
        g.holdings = {}
        for pos in positions:
            code = pos.m_strInstrumentID + "." + pos.m_strExchangeID
            g.holdings[code] = {"持仓数量": pos.m_nVolume}
        account = get_trade_detail_data(accid, 'stock', 'account')
        if account:
            g.money = account[0].m_dAvailable
        logger.info(f"[同步] 持仓 {len(g.holdings)} 只, 现金 {g.money:,.0f}")
    except Exception as e:
        logger.debug(f"QMT 同步跳过: {e}")

def handlebar(C):
    """每日交易执行"""
    g.trade_day_count += 1

    if g.rebalance_days > 1 and g.trade_day_count % g.rebalance_days != 1:
        return

    current_time_int = C.get_bar_timetag(C.barpos)
    current_date_ts = pd.to_datetime(timetag_to_datetime(current_time_int, "%Y%m%d"))
    current_date_str = current_date_ts.strftime('%Y-%m-%d')

    # 【容错】信号为空时跳过
    if g.buy_signals.empty or current_date_ts not in g.buy_signals.index:
        return

    sync_from_qmt(g.accid)

    logger.info(f">>> 调仓日 {current_date_str} (第{g.trade_day_count}个交易日)")

    # 卖出并获取回收金额（用于买入计算）
    sell_proceeds = execute_sell_signals(C, current_date_ts)
    execute_buy_signals(C, current_date_ts)
    print_holdings_summary(current_date_ts)

# ============================================================================
#                              交易执行函数
# ============================================================================

def execute_sell_signals(C, current_date_ts):
    """卖出不在名单内的股票，返回卖出回收金额"""
    if g.sell_signals.empty or current_date_ts not in g.sell_signals.index:
        return 0

    positions = get_holdings(g.accid, 'stock')
    if not positions:
        logger.debug("当前无持仓，跳过卖出")
        return 0

    today_sell_mask = g.sell_signals.loc[current_date_ts]
    current_date_str = current_date_ts.strftime('%Y%m%d')

    sell_count = 0
    sell_amount = 0
    sell_stocks = []
    limit_down_stocks = []

    for stock in list(positions.keys()):
        if today_sell_mask.get(stock, False):
            if is_limit_down_at_open(stock, current_date_ts):
                limit_down_stocks.append(stock.split('.')[0])
                continue

            amount = positions[stock]['持仓数量']
            price = get_price_at_time(stock, current_date_ts)

            if price and price > 0:
                sell_value = price * amount
                logger.debug(f"[卖出] {stock}, 价格: {price:.2f}, 数量: {amount}, 金额: {sell_value:,.0f}")
                g.trade_records.append({
                    '日期': current_date_str, '股票代码': stock,
                    '交易类型': '卖出', '价格': price, '数量': amount, '金额': sell_value
                })

                if 'passorder' in globals():
                    passorder(24, 1101, g.accid, stock, 11, float(price), float(amount), "backtest", 1, "卖出", C)
                    g.money += sell_value
                    if stock in g.holdings: del g.holdings[stock]
                else:
                    g.money += sell_value
                    if stock in g.holdings: del g.holdings[stock]

                sell_count += 1
                sell_amount += sell_value
                sell_stocks.append(stock.split('.')[0])

    if limit_down_stocks:
        logger.warning(f"[跌停] {len(limit_down_stocks)}只无法卖出")

    if sell_count > 0:
        stocks_str = ','.join(sell_stocks[:5]) + ('...' if len(sell_stocks) > 5 else '')
        logger.info(f"[卖出] {sell_count}只 ({stocks_str}), 回收: {sell_amount:,.0f}")

    return sell_amount

def execute_buy_signals(C, current_date_ts):
    """执行买入"""
    if g.buy_signals.empty or current_date_ts not in g.buy_signals.index: return

    today_buy = g.buy_signals.loc[current_date_ts]
    target_stocks = today_buy[today_buy].index.tolist()[:g.max_positions]
    current_date_str = current_date_ts.strftime('%Y%m%d')

    positions = get_holdings(g.accid, 'stock')
    new_buy_candidates = [s for s in target_stocks if s not in positions]
    if not new_buy_candidates: return

    total_available = g.money

    valid_list = []
    limit_up_stocks = []
    for stock in new_buy_candidates:
        price = get_price_at_time(stock, current_date_ts)
        if not price or price <= 0:
            continue
        if is_limit_up_at_open(stock, current_date_ts):
            limit_up_stocks.append(stock.split('.')[0])
            continue
        valid_list.append((stock, price))

    if limit_up_stocks:
        logger.warning(f"[涨停] {len(limit_up_stocks)}只无法买入")

    if not valid_list:
        logger.warning("无有效买入标的")
        return

    avg_budget = (total_available * g.cash_usage_ratio) / len(valid_list)

    logger.info(f"--- 调仓启动 ---")
    logger.info(f"可用资金: {total_available:,.0f}, 计划买入: {len(valid_list)}只, 单只预算: {avg_budget:,.0f}")

    actual_total_spent = 0
    buy_stocks = []

    for stock, price in valid_list:
        lot_size = 200 if stock.startswith('688') else 100
        if g.money < (price * lot_size):
            logger.warning(f"资金耗尽，停止买入: {stock}")
            break

        buy_volume = int((avg_budget / price) // lot_size) * lot_size

        if buy_volume >= lot_size:
            cost = price * buy_volume

            if 'passorder' in globals():
                passorder(23, 1101, g.accid, stock, 11, price, buy_volume, "backtest", 1, "买入", C)

            g.money -= cost
            g.holdings[stock] = {
                "持仓数量": buy_volume,
                "成本价": price,
                "买入日期": current_date_str
            }
            actual_total_spent += cost
            buy_stocks.append(stock.split('.')[0])

            g.trade_records.append({
                '日期': current_date_str, '股票代码': stock,
                '交易类型': '买入', '价格': price, '数量': buy_volume, '金额': cost
            })
            logger.debug(f"[下单] {stock}, 价格: {price:.2f}, 股数: {buy_volume}, 花费: {cost:,.0f}")

    if buy_stocks:
        stocks_str = ','.join(buy_stocks[:5]) + ('...' if len(buy_stocks) > 5 else '')
        logger.info(f"[买入] {len(buy_stocks)}只 ({stocks_str}), 花费: {actual_total_spent:,.0f}, 剩余: {g.money:,.0f}")

def print_holdings_summary(current_date_ts):
    """打印持仓汇总"""
    positions = get_holdings(g.accid, 'stock')
    if not positions:
        return

    total_mv = sum((get_price_at_time(s, current_date_ts) or 0) * info['持仓数量']
                   for s, info in positions.items())

    try:
        available_cash = get_trade_detail_data(g.accid, 'stock', 'account')[0].m_dAvailable
    except Exception as e:
        logger.debug(f"获取 QMT 资金跳过: {e}")
        available_cash = g.money

    total_asset = total_mv + available_cash
    position_ratio = total_mv / total_asset * 100 if total_asset > 0 else 0
    logger.info(f"[持仓汇总] 持仓: {len(positions)}只, 市值: {total_mv:,.0f}, 现金: {available_cash:,.0f}, 总资产: {total_asset:,.0f}, 仓位: {position_ratio:.1f}%")

# ============================================================================
#                              辅助工具函数
# ============================================================================

def get_ipo_mask(C, stock_list, target_index):
    """生成新股过滤掩码，True 表示上市满 120 天（容错版）"""
    df_ipo = pd.DataFrame(True, index=target_index, columns=stock_list)
    for s in stock_list:
        try:
            detail = C.get_instrument_detail(s)
            if not detail:
                continue
            open_date_raw = detail.get('OpenDate')
            # 【容错】处理无效日期：0, None, '', '0.0' 等
            if not open_date_raw or str(open_date_raw) in ['0', 'None', '', '0.0']:
                continue
            open_str = str(int(float(open_date_raw)))
            open_date = pd.to_datetime(open_str, format='%Y%m%d')
            df_ipo[s] = (df_ipo.index - open_date).days >= 120
        except Exception:
            continue
    return df_ipo.astype(bool)

def get_st_mask(C, stock_list, target_index):
    """生成 ST 股票掩码，True 表示是 ST（容错版）"""
    df_st = pd.DataFrame(False, index=target_index, columns=stock_list)
    for s in stock_list:
        try:
            st_info = C.get_his_st_data(s)
            if not st_info:
                continue
            all_st_periods = st_info.get('ST', []) + st_info.get('*ST', [])
            for start_date, end_date in all_st_periods:
                df_st.loc[pd.to_datetime(start_date):pd.to_datetime(end_date), s] = True
        except Exception:
            continue
    return df_st

def get_financial_wide_table(C, stock_list, field, startDate, endDate):
    """获取财务数据宽表（容错版）"""
    try:
        start_dt = datetime.strptime(startDate, '%Y%m%d')
        seed_date = (start_dt - timedelta(days=365)).strftime('%Y%m%d')
        raw_data = C.get_raw_financial_data([field], stock_list, seed_date, endDate, report_type='report_time')
        if not raw_data:
            logger.warning(f"财务数据获取为空: {field}")
            return pd.DataFrame()
        extracted = {s: raw_data[s][field] for s in stock_list if s in raw_data and field in raw_data[s]}
        if not extracted:
            return pd.DataFrame()
        df = pd.DataFrame.from_dict(extracted)
        df.index = pd.to_datetime(df.index.map(lambda x: timetag_to_datetime(x, '%Y%m%d')))
        return df.sort_index().ffill()
    except Exception as e:
        logger.warning(f"获取财务数据失败: {field}, 错误: {e}")
        return pd.DataFrame()

def get_price_at_time(stock, current_date_ts):
    """获取指定时间的开盘价"""
    if hasattr(g, 'daily_open') and stock in g.daily_open.columns:
        if current_date_ts in g.daily_open.index:
            price = g.daily_open.loc[current_date_ts, stock]
            if pd.notna(price) and price > 0: return price
    return None

def get_limit_ratio(stock):
    """获取股票的涨跌停比例"""
    if stock.startswith(('688', '30')): return 0.20  # 科创板、创业板
    elif stock.startswith('8'): return 0.30          # 北交所
    else: return 0.10                                 # 主板

def get_prev_close(stock, current_date_ts):
    """获取前一交易日收盘价"""
    if not hasattr(g, 'daily_close') or stock not in g.daily_close.columns:
        return None
    if current_date_ts not in g.daily_close.index:
        return None
    try:
        idx = g.daily_close.index.get_loc(current_date_ts)
        if idx <= 0:
            return None
        prev_close = g.daily_close.iloc[idx - 1][stock]
        if pd.notna(prev_close) and prev_close > 0:
            return prev_close
    except Exception:
        pass
    return None

def is_limit_up_at_open(stock, current_date_ts):
    """判断开盘是否涨停"""
    open_price = get_price_at_time(stock, current_date_ts)
    prev_close = get_prev_close(stock, current_date_ts)
    if not open_price or not prev_close:
        return False
    limit_up_price = round(prev_close * (1 + get_limit_ratio(stock)), 2)
    return open_price >= limit_up_price

def is_limit_down_at_open(stock, current_date_ts):
    """判断开盘是否跌停"""
    open_price = get_price_at_time(stock, current_date_ts)
    prev_close = get_prev_close(stock, current_date_ts)
    if not open_price or not prev_close:
        return False
    limit_down_price = round(prev_close * (1 - get_limit_ratio(stock)), 2)
    return open_price <= limit_down_price

def get_df_ex(data: dict, field: str) -> pd.DataFrame:
    """从行情数据提取字段的宽表"""
    if not data: return pd.DataFrame()
    _columns = list(data.keys())
    _index = data[_columns[0]].index
    df = pd.DataFrame(index=_index, columns=_columns)
    for s in _columns:
        if field in data[s].columns: df[s] = data[s][field]
    return df

def get_holdings(accid, datatype):
    """获取持仓信息"""
    PositionInfo_dict = {}
    try:
        resultlist = get_trade_detail_data(accid, datatype, 'POSITION')
        for obj in resultlist:
            stock_code = obj.m_strInstrumentID + "." + obj.m_strExchangeID
            PositionInfo_dict[stock_code] = {"持仓数量": obj.m_nVolume}
    except Exception as e:
        logger.debug(f"获取 QMT 持仓跳过: {e}，使用本地记录")
        for stock, info in g.holdings.items():
            if isinstance(info, dict):
                volume = info.get('持仓数量', 0)
            else:
                volume = info
            if volume > 0:
                PositionInfo_dict[stock] = {"持仓数量": volume}
    return PositionInfo_dict

def timetag_to_datetime(timetag, format_str="%Y%m%d%H%M%S"):
    """时间戳转日期字符串"""
    if timetag > 1000000000000: timetag = timetag // 1000
    return datetime.fromtimestamp(timetag).strftime(format_str)