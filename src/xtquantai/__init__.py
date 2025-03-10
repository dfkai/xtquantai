import importlib
from . import server
import asyncio

# 强制重新加载server模块，避免缓存问题
importlib.reload(server)

def main():
    """Main entry point for the package."""
    print("xtquant文档地址：http://dict.thinktrader.net/nativeApi/start_now.html")
    print("正在启动xtquantai MCP服务器...")
    print("提供功能：")
    print("1. 获取交易日期 - get_trading_dates")
    print("2. 获取板块列表 - get_stock_list")
    print("3. 获取股票详情 - get_instrument_detail")
    print("4. 获取历史行情数据 - get_history_market_data")
    print("5. 获取最新行情数据 - get_latest_market_data")
    print("6. 获取完整行情数据 - get_full_market_data")
    print("7. 创建图表面板 - create_chart_panel")
    print("8. 创建自定义布局 - create_custom_layout")
    
    # 运行MCP服务器
    asyncio.run(server.main())

# Optionally expose other important items at package level
__all__ = ['main', 'server']