# xtquantai

xtquantai 是一个基于 Model Context Protocol (MCP) 的服务器，它将迅投 (xtquant) 量化交易平台的功能与人工智能助手集成，使 AI 能够直接访问和操作量化交易数据和功能。

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 功能特点

XTQuantAI 提供以下核心功能(陆续更新中，欢迎大家提交新创意)：

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

⚠️ 注意
1. QMT 生态系统目前仅支持 Windows，因此以下均在 Windows 环境实现
2. Windows 环境目前在实现 MCP 过程中有不少细节，需要注意

### 前提条件
- Python 3.11 或更高版本
- 迅投 QMT 或投研终端
- [uv](https://github.com/astral-sh/uv) 包管理工具 (推荐)

### uv 的安装及注意事项

uv 是后续用来启动包的工具，因此我们需要在开始安装一下，注意你需要在你要运行 xtquantai 的环境里面安装这个包，这是第一个可能出问题的地方，不确定就都安装一下。

```python
pip install uv
```
第二个注意点，uv 是有缓存的，因此我才会有 `clear_cache_and_run.py` 的文件，你一旦中间有错误的运行，不删缓存就会一直不更新，记得运行一下删除。


### 下载即可
```bash
git clone https://github.com/dfkai/xtquantai.git
```

或者直接下载 压缩包。你可以下载到任意文件夹，只要最后能够找到 xtquantai 的具体地址即可，最好去文件夹里直接去复制地址。

## 使用方法

### 与 Cursor 的集成

#### Windows（QMT/投研端目前仅支持 Windows，需在 Windows 环境）

在 Cursor 中配置 MCP 服务器：

方法一：

在当前项目建立 `.cursor` 文件夹，在该文件夹下建立 `mcp.json` 文件，则 Cursor 编辑器会自动添加该 mcp 工具

```json
{
  "mcpServers": {
    "xtquantai": {
      "command": "cmd /c uvx",
      "args": [
        "path:\\to\\xtquantai"
      ]
    }
  }
}
```

> ⚠️ 注意：在 windows 中，命令务必加上 cmd /c，否则会导致命令窗口执行完立即关闭。

方法二：

直接在 `设置-MCP-添加新的 MCP Server`，名字叫 `xtquantai`，命令(command)是：`cmd /c uvx path:\to\xtquantai`，调整为`Enabled`。

这里注意 `path to` 意思是你自己本地的地址，同时注意你手动填写进去是单斜杠，仅仅在json文件中需要两个斜杠防止转义。

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

### 直接启动服务器
```bash
# 使用 Python 直接运行
python -m xtquantai

# 或使用安装的命令行工具
xtquantai
```

### 使用 MCP Inspector 进行调试（仅在开发的的时候使用）

需要安装 node 环境。
```bash
npx @modelcontextprotocol/inspector uv run xtquantai
```

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

- [迅投科技](https://www.thinktrader.net/) 提供的量化交易平台
- [Model Context Protocol](https://modelcontextprotocol.io/) 提供的 AI 集成框架