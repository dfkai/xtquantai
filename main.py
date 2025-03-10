#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
xtquantai 启动脚本
提供两种启动方式：
1. 直接启动 xtquantai 服务器
2. 通过 MCP Inspector 启动 xtquantai 服务器
"""

import os
import sys
import subprocess
import argparse
import importlib
import asyncio
import shutil

def ensure_path():
    """确保当前目录在 Python 路径中"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

def check_node_installed():
    """检查 Node.js 是否已安装"""
    try:
        # 检查 node 命令是否可用
        subprocess.run(["node", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_npx_installed():
    """检查 npx 命令是否可用"""
    try:
        # 检查 npx 命令是否可用
        subprocess.run(["npx", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def start_direct():
    """直接启动 xtquantai 服务器"""
    ensure_path()
    try:
        from xtquantai import main
        print("正在直接启动 xtquantai 服务器...")
        main()
    except ImportError as e:
        print(f"导入 xtquantai 失败: {e}")
        print("尝试启动备选服务器...")
        try:
            # 尝试启动 server_direct.py
            if os.path.exists("server_direct.py"):
                print("找到 server_direct.py，启动独立服务器...")
                subprocess.run([sys.executable, "server_direct.py"], check=True)
            else:
                print("未找到 server_direct.py，无法启动服务器")
                print("请确保已安装 xtquantai 包或当前目录包含 xtquantai 源代码")
                sys.exit(1)
        except Exception as e:
            print(f"启动备选服务器失败: {e}")
            sys.exit(1)

def start_with_inspector(python_path=None, venv_path=None):
    """通过 MCP Inspector 启动 xtquantai 服务器"""
    # 检查 Node.js 和 npx 是否已安装
    if not check_node_installed():
        print("未检测到 Node.js，无法使用 MCP Inspector 模式")
        print("正在切换到直接模式...")
        start_direct()
        return
    
    if not check_npx_installed():
        print("未检测到 npx 命令，无法使用 MCP Inspector 模式")
        print("正在切换到直接模式...")
        start_direct()
        return
    
    cmd = ["npx", "@modelcontextprotocol/inspector"]
    
    if venv_path:
        cmd.extend(["uv", "run", "--venv", venv_path, "xtquantai"])
    elif python_path:
        cmd.extend(["uv", "run", "--python", python_path, "xtquantai"])
    else:
        cmd.extend(["uv", "run", "xtquantai"])
    
    print(f"执行命令: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"启动 MCP Inspector 失败: {e}")
        print("尝试切换到直接模式...")
        start_direct()
    except FileNotFoundError:
        print("找不到 npx 命令，请确保已安装 Node.js 和 npm")
        print("尝试切换到直接模式...")
        start_direct()

def main():
    """主函数，解析命令行参数并启动服务器"""
    parser = argparse.ArgumentParser(description="启动 xtquantai 服务器")
    parser.add_argument("--mode", choices=["direct", "inspector", "auto"], default="auto",
                        help="启动模式: direct=直接启动, inspector=通过MCP Inspector启动, auto=自动选择")
    parser.add_argument("--python", help="Python 解释器路径")
    parser.add_argument("--venv", help="虚拟环境路径")
    parser.add_argument("--port", type=int, default=8000, help="直接模式下的服务器端口")
    
    args = parser.parse_args()
    
    if args.mode == "direct":
        start_direct()
    elif args.mode == "inspector":
        start_with_inspector(args.python, args.venv)
    else:  # auto 模式
        # 检查是否可以使用 MCP Inspector
        if check_node_installed() and check_npx_installed():
            print("检测到 Node.js 和 npx，使用 MCP Inspector 模式")
            start_with_inspector(args.python, args.venv)
        else:
            print("未检测到 Node.js 或 npx，使用直接模式")
            start_direct()

if __name__ == "__main__":
    main() 