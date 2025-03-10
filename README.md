# XTQuantAI

XTQuantAI 是一个基于 Model Context Protocol (MCP) 的服务器，它将讯投 (XTQuant) 量化交易平台的功能与人工智能助手集成，使 AI 能够直接访问和操作量化交易数据和功能。

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 功能特点

XTQuantAI 提供以下核心功能：

### 基础数据查询
- **获取交易日期** (`get_trading_dates`) - 获取指定市场的交易日期
- **获取板块股票列表** (`get_stock_list`) - 获取特定板块的股票列表
- **获取股票详情** (`get_instrument_detail`) - 获取股票的详细信息

### 行情数据
- **获取历史行情数据** (`get_history_market_data`) - 获取股票的历史行情数据
- **获取最新行情数据** (`get_latest_market_data`) - 获取股票的最新行情数据
- **获取完整行情数据** (`get_full_market_data`) - 获取股票的完整行情数据

### 图表和可视化
- **创建图表面板** (`create_chart_panel`) - 创建股票图表面板，支持各种技术指标
- **创建自定义布局** (`create_custom_layout`) - 创建自定义的图表布局，可以指定指标名称、参数名和参数值

## 安装

### 前提条件
- Python 3.11 或更高版本
- 讯投 (XTQuant) 量化交易平台
- [uv](https://github.com/astral-sh/uv) 包管理工具 (推荐)

### 使用 pip 安装
```bash
pip install xtquantai
```

### 使用 uv 安装
```bash
uv pip install xtquantai
```

### 从源码安装
```bash
git clone https://github.com/dfkai/xtquantai.git
cd xtquantai
uv pip install -e .
```

## 使用方法

### 直接启动服务器
```bash
# 使用 Python 直接运行
python -m xtquantai

# 或使用安装的命令行工具
xtquantai
```

### 使用 MCP Inspector 进行调试
```bash
npx @modelcontextprotocol/inspector uv run xtquantai
```

### 与 Claude Desktop 集成

在 Claude Desktop 中配置 MCP 服务器：

#### Windows
编辑 `%APPDATA%/Claude/claude_desktop_config.json` 文件：

```json
{
  "mcpServers": {
    "xtquantai": {
      "command": "uv",
      "args": [
        "run",
        "xtquantai"
      ]
    }
  }
}
```

#### macOS
编辑 `~/Library/Application Support/Claude/claude_desktop_config.json` 文件：

```json
{
  "mcpServers": {
    "xtquantai": {
      "command": "uv",
      "args": [
        "run",
        "xtquantai"
      ]
    }
  }
}
```

## 工具使用示例

### 获取交易日期
```python
# 获取上海市场的交易日期
dates = get_trading_dates(market="SH")
```

### 获取股票列表
```python
# 获取沪深A股板块的股票列表
stocks = get_stock_list(sector="沪深A股")
```

### 创建图表面板
```python
# 创建包含MA指标的图表面板
result = create_chart_panel(
    codes="000001.SZ,600519.SH",
    period="1d",
    indicator_name="MA",
    param_names="period",
    param_values="5"
)
```

## 开发

### 构建和发布

准备发布包：

1. 同步依赖并更新锁文件：
```bash
uv sync
```

2. 构建包分发：
```bash
uv build
```

3. 发布到 PyPI：
```bash
uv publish
```

### 调试

由于 MCP 服务器通过标准输入/输出运行，调试可能具有挑战性。我们强烈建议使用 [MCP Inspector](https://github.com/modelcontextprotocol/inspector) 进行调试。

## 项目结构

```
xtquantai/
├── src/
│   └── xtquantai/
│       ├── __init__.py    # 包初始化文件
│       └── server.py      # MCP 服务器实现
├── main.py                # 启动脚本
├── server_direct.py       # 直接 HTTP 服务器实现
├── pyproject.toml         # 项目配置
└── README.md              # 项目文档
```

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎贡献！请随时提交问题或拉取请求。

## 致谢

- [讯投科技](https://www.thinktrader.net/) 提供的量化交易平台
- [Model Context Protocol](https://modelcontextprotocol.io/) 提供的 AI 集成框架