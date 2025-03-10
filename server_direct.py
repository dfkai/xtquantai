#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
xtquantai 直接服务器
提供直接的 API 接口，不依赖于 MCP
"""

import os
import sys
import json
import traceback
import time
from typing import Dict, List, Any, Optional
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# 尝试导入 xtquant 相关模块
xtdata = None
UIPanel = None

try:
    from xtquant import xtdata
    print(f"成功导入xtquant模块，路径: {xtdata.__file__ if hasattr(xtdata, '__file__') else '未知'}")
    
    # 尝试导入UIPanel
    try:
        from xtquant.xtdata import UIPanel
        print("成功导入UIPanel类")
    except ImportError as e:
        print(f"警告: 无法导入UIPanel类: {str(e)}")
        # 创建一个模拟的UIPanel类
        class UIPanel:
            def __init__(self, stock, period, figures=None):
                self.stock = stock
                self.period = period
                self.figures = figures or []
            
            def __str__(self):
                return f"UIPanel(stock={self.stock}, period={self.period}, figures={self.figures})"
except ImportError as e:
    print(f"警告: 无法导入xtquant模块: {str(e)}")
    print("Python搜索路径:")
    for path in sys.path:
        print(f"  - {path}")
    
    # 创建模拟的xtdata模块
    class MockXtdata:
        def __init__(self):
            self.name = "MockXtdata"
        
        def get_trading_dates(self, market="SH"):
            print(f"模拟调用get_trading_dates({market})")
            return ["2023-01-01", "2023-01-02", "2023-01-03"]
        
        def get_stock_list_in_sector(self, sector="沪深A股"):
            print(f"模拟调用get_stock_list_in_sector({sector})")
            return ["000001.SZ", "600519.SH", "300059.SZ"]
        
        def get_instrument_detail(self, code, iscomplete=False):
            print(f"模拟调用get_instrument_detail({code}, {iscomplete})")
            return {"code": code, "name": "模拟股票", "price": 100.0}
        
        def apply_ui_panel_control(self, panels):
            print(f"模拟调用apply_ui_panel_control({panels})")
            return True
        
        def get_market_data(self, fields, stock_list, period="1d", start_time="", end_time="", count=-1, dividend_type="none", fill_data=True):
            print(f"模拟调用get_market_data({fields}, {stock_list}, {period}, {start_time}, {end_time}, {count}, {dividend_type}, {fill_data})")
            # 创建模拟数据
            result = {}
            for stock in stock_list:
                stock_data = {}
                for field in fields:
                    if field == "close":
                        stock_data[field] = [100.0, 101.0, 102.0]
                    elif field == "open":
                        stock_data[field] = [99.0, 100.0, 101.0]
                    elif field == "high":
                        stock_data[field] = [102.0, 103.0, 104.0]
                    elif field == "low":
                        stock_data[field] = [98.0, 99.0, 100.0]
                    elif field == "volume":
                        stock_data[field] = [10000, 12000, 15000]
                    else:
                        stock_data[field] = [0.0, 0.0, 0.0]
                result[stock] = stock_data
            return result
    
    # 使用模拟的xtdata
    xtdata = MockXtdata()
    print("使用模拟的xtdata模块")

# 确保xtdata已初始化
def ensure_xtdc_initialized():
    """确保XTQuant数据中心已初始化"""
    global xtdata
    if xtdata is None:
        print("xtdata模块未初始化，尝试重新导入")
        try:
            from xtquant import xtdata
            print(f"成功导入xtquant模块，路径: {xtdata.__file__ if hasattr(xtdata, '__file__') else '未知'}")
        except ImportError as e:
            print(f"警告: 无法导入xtquant模块: {str(e)}")
            xtdata = MockXtdata()
            print("使用模拟的xtdata模块")

# API 函数
def get_trading_dates(market="SH"):
    """获取交易日期"""
    ensure_xtdc_initialized()
    try:
        dates = xtdata.get_trading_dates(market)
        return {"success": True, "data": dates}
    except Exception as e:
        print(f"获取交易日期出错: {str(e)}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def get_stock_list(sector="沪深A股"):
    """获取板块股票列表"""
    ensure_xtdc_initialized()
    try:
        stocks = xtdata.get_stock_list_in_sector(sector)
        return {"success": True, "data": stocks}
    except Exception as e:
        print(f"获取板块股票列表出错: {str(e)}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def get_instrument_detail(code, iscomplete=False):
    """获取股票详情"""
    ensure_xtdc_initialized()
    try:
        detail = xtdata.get_instrument_detail(code, iscomplete)
        return {"success": True, "data": detail}
    except Exception as e:
        print(f"获取股票详情出错: {str(e)}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def get_history_market_data(fields, stock_list, period="1d", start_time="", end_time="", count=-1, dividend_type="none", fill_data=True):
    """获取历史行情数据"""
    ensure_xtdc_initialized()
    try:
        # 处理输入参数
        if isinstance(fields, str):
            fields = fields.split(",")
        if isinstance(stock_list, str):
            stock_list = stock_list.split(",")
        
        data = xtdata.get_market_data(fields, stock_list, period, start_time, end_time, count, dividend_type, fill_data)
        
        # 转换数据为可序列化格式
        result = {}
        for stock, stock_data in data.items():
            result[stock] = {}
            for field, values in stock_data.items():
                if hasattr(values, 'tolist'):  # 如果是numpy数组
                    result[stock][field] = values.tolist()
                else:
                    result[stock][field] = values
        
        return {"success": True, "data": result}
    except Exception as e:
        print(f"获取历史行情数据出错: {str(e)}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def create_chart_panel(codes, period="1d", indicator_name="MA", param_names="", param_values=""):
    """创建图表面板"""
    ensure_xtdc_initialized()
    try:
        # 收集环境信息
        env_info = {
            "python_version": sys.version,
            "platform": sys.platform,
            "cwd": os.getcwd(),
            "pid": os.getpid(),
            "user": os.environ.get("USERNAME", "unknown"),
            "xtdata_type": str(type(xtdata)),
            "has_apply_ui_panel_control": hasattr(xtdata, 'apply_ui_panel_control'),
        }
        
        if xtdata is None:
            return {"success": False, "error": "xtdata模块未正确加载", "debug_info": env_info}
        
        # 解析股票代码列表
        stock_list = [code.strip() for code in codes.split(",") if code.strip()]
        if not stock_list:
            return {"success": False, "error": "未提供有效的股票代码", "debug_info": env_info}
        
        # 解析参数名称和值
        param_names_list = [name.strip() for name in param_names.split(",") if name.strip()]
        param_values_list = []
        for value in param_values.split(","):
            if value.strip():
                try:
                    if '.' in value:
                        param_values_list.append(float(value.strip()))
                    else:
                        param_values_list.append(int(value.strip()))
                except ValueError:
                    param_values_list.append(value.strip())
        
        # 构建指标配置
        indicator_params = {}
        for i, name in enumerate(param_names_list):
            if i < len(param_values_list):
                indicator_params[name] = param_values_list[i]
        
        # 创建指标配置字典
        indicator_config = {indicator_name: indicator_params}
        
        # 创建面板列表
        print(f"创建图表面板: 股票={stock_list}, 周期={period}, 指标={indicator_config}")
        
        panel_info = []
        try:
            # 尝试创建UIPanel对象
            panels = []
            for stock in stock_list:
                try:
                    panel = UIPanel(stock, period, figures=[indicator_config])
                    panels.append(panel)
                    panel_info.append({
                        "stock": stock,
                        "period": period,
                        "figures": str(indicator_config),
                        "panel_type": str(type(panel)),
                        "panel_str": str(panel)
                    })
                except Exception as e:
                    error_msg = f"创建UIPanel对象失败: {str(e)}"
                    print(error_msg)
                    traceback.print_exc()
                    panel_info.append({
                        "stock": stock,
                        "period": period,
                        "figures": str(indicator_config),
                        "error": error_msg
                    })
            
            # 应用面板控制
            if hasattr(xtdata, 'apply_ui_panel_control'):
                start_time = time.time()
                result = xtdata.apply_ui_panel_control(panels)
                end_time = time.time()
                
                # 强制刷新UI
                if hasattr(xtdata, 'refresh_ui'):
                    xtdata.refresh_ui()
                
                # 添加延迟，确保UI有时间更新
                time.sleep(0.5)
                
                return {
                    "success": True, 
                    "data": {
                        "result": result,
                        "execution_time": end_time - start_time,
                        "panel_info": panel_info
                    },
                    "debug_info": env_info
                }
            else:
                return {
                    "success": False, 
                    "error": "xtdata模块没有apply_ui_panel_control方法",
                    "debug_info": {
                        "env_info": env_info,
                        "panel_info": panel_info
                    }
                }
        except Exception as e:
            print(f"创建或应用面板时出错: {str(e)}")
            traceback.print_exc()
            return {
                "success": False,
                "error": f"创建或应用面板时出错: {str(e)}",
                "debug_info": {
                    "env_info": env_info,
                    "panel_info": panel_info,
                    "traceback": traceback.format_exc()
                }
            }
    except Exception as e:
        print(f"创建图表面板出错: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "debug_info": {
                "traceback": traceback.format_exc()
            }
        }

def create_custom_layout(codes, period="1d", indicator_name="MA", param_names="", param_values=""):
    """创建自定义布局"""
    # 这里简单地调用 create_chart_panel 函数，实际应用中可以根据需要扩展
    return create_chart_panel(codes, period, indicator_name, param_names, param_values)

# HTTP 请求处理器
class XTQuantAIHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_GET(self):
        # 解析URL路径和查询参数
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)
        
        # 将查询参数转换为单值字典
        params = {k: v[0] if len(v) == 1 else v for k, v in query.items()}
        
        # 根据路径调用相应的函数
        result = {"success": False, "error": "未知路径"}
        
        if path == "/api/get_trading_dates":
            market = params.get("market", "SH")
            result = get_trading_dates(market)
        
        elif path == "/api/get_stock_list":
            sector = params.get("sector", "沪深A股")
            result = get_stock_list(sector)
        
        elif path == "/api/get_instrument_detail":
            code = params.get("code", "")
            iscomplete = params.get("iscomplete", "false").lower() == "true"
            if not code:
                result = {"success": False, "error": "未提供股票代码"}
            else:
                result = get_instrument_detail(code, iscomplete)
        
        elif path == "/api/get_history_market_data":
            fields = params.get("fields", "")
            stock_list = params.get("stock_list", "")
            period = params.get("period", "1d")
            start_time = params.get("start_time", "")
            end_time = params.get("end_time", "")
            count = int(params.get("count", "-1"))
            dividend_type = params.get("dividend_type", "none")
            fill_data = params.get("fill_data", "true").lower() == "true"
            
            if not fields or not stock_list:
                result = {"success": False, "error": "未提供字段或股票列表"}
            else:
                result = get_history_market_data(fields, stock_list, period, start_time, end_time, count, dividend_type, fill_data)
        
        elif path == "/api/create_chart_panel":
            codes = params.get("codes", "")
            period = params.get("period", "1d")
            indicator_name = params.get("indicator_name", "MA")
            param_names = params.get("param_names", "")
            param_values = params.get("param_values", "")
            
            if not codes:
                result = {"success": False, "error": "未提供股票代码"}
            else:
                result = create_chart_panel(codes, period, indicator_name, param_names, param_values)
        
        elif path == "/api/create_custom_layout":
            codes = params.get("codes", "")
            period = params.get("period", "1d")
            indicator_name = params.get("indicator_name", "MA")
            param_names = params.get("param_names", "")
            param_values = params.get("param_values", "")
            
            if not codes:
                result = {"success": False, "error": "未提供股票代码"}
            else:
                result = create_custom_layout(codes, period, indicator_name, param_names, param_values)
        
        elif path == "/api/list_tools":
            # 列出所有可用的工具
            result = {
                "success": True,
                "data": [
                    {"name": "get_trading_dates", "description": "获取交易日期"},
                    {"name": "get_stock_list", "description": "获取板块股票列表"},
                    {"name": "get_instrument_detail", "description": "获取股票详情"},
                    {"name": "get_history_market_data", "description": "获取历史行情数据"},
                    {"name": "create_chart_panel", "description": "创建图表面板"},
                    {"name": "create_custom_layout", "description": "创建自定义布局"}
                ]
            }
        
        # 返回JSON响应
        self._set_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
    
    def do_POST(self):
        # 获取请求内容长度
        content_length = int(self.headers.get("Content-Length", 0))
        
        # 读取请求体
        post_data = self.rfile.read(content_length).decode("utf-8")
        
        # 解析JSON数据
        try:
            params = json.loads(post_data)
        except json.JSONDecodeError:
            self._set_headers()
            self.wfile.write(json.dumps({"success": False, "error": "无效的JSON数据"}).encode("utf-8"))
            return
        
        # 解析URL路径
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # 根据路径调用相应的函数
        result = {"success": False, "error": "未知路径"}
        
        if path == "/api/get_trading_dates":
            market = params.get("market", "SH")
            result = get_trading_dates(market)
        
        elif path == "/api/get_stock_list":
            sector = params.get("sector", "沪深A股")
            result = get_stock_list(sector)
        
        elif path == "/api/get_instrument_detail":
            code = params.get("code", "")
            iscomplete = params.get("iscomplete", False)
            if not code:
                result = {"success": False, "error": "未提供股票代码"}
            else:
                result = get_instrument_detail(code, iscomplete)
        
        elif path == "/api/get_history_market_data":
            fields = params.get("fields", "")
            stock_list = params.get("stock_list", "")
            period = params.get("period", "1d")
            start_time = params.get("start_time", "")
            end_time = params.get("end_time", "")
            count = params.get("count", -1)
            dividend_type = params.get("dividend_type", "none")
            fill_data = params.get("fill_data", True)
            
            if not fields or not stock_list:
                result = {"success": False, "error": "未提供字段或股票列表"}
            else:
                result = get_history_market_data(fields, stock_list, period, start_time, end_time, count, dividend_type, fill_data)
        
        elif path == "/api/create_chart_panel":
            codes = params.get("codes", "")
            period = params.get("period", "1d")
            indicator_name = params.get("indicator_name", "MA")
            param_names = params.get("param_names", "")
            param_values = params.get("param_values", "")
            
            if not codes:
                result = {"success": False, "error": "未提供股票代码"}
            else:
                result = create_chart_panel(codes, period, indicator_name, param_names, param_values)
        
        elif path == "/api/create_custom_layout":
            codes = params.get("codes", "")
            period = params.get("period", "1d")
            indicator_name = params.get("indicator_name", "MA")
            param_names = params.get("param_names", "")
            param_values = params.get("param_values", "")
            
            if not codes:
                result = {"success": False, "error": "未提供股票代码"}
            else:
                result = create_custom_layout(codes, period, indicator_name, param_names, param_values)
        
        # 返回JSON响应
        self._set_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))

def run_server(port=8000):
    """运行HTTP服务器"""
    server_address = ("", port)
    httpd = HTTPServer(server_address, XTQuantAIHandler)
    print(f"启动服务器在 http://localhost:{port}")
    print("提供以下API接口:")
    print("1. GET/POST /api/get_trading_dates - 获取交易日期")
    print("2. GET/POST /api/get_stock_list - 获取板块股票列表")
    print("3. GET/POST /api/get_instrument_detail - 获取股票详情")
    print("4. GET/POST /api/get_history_market_data - 获取历史行情数据")
    print("5. GET/POST /api/create_chart_panel - 创建图表面板")
    print("6. GET/POST /api/create_custom_layout - 创建自定义布局")
    print("7. GET /api/list_tools - 列出所有可用的工具")
    print("按Ctrl+C停止服务器")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("服务器已停止")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="启动xtquantai直接服务器")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口号")
    
    args = parser.parse_args()
    
    run_server(args.port) 