#!/usr/bin/env python
"""
清除缓存并运行xtquantai
"""
import os
import shutil
import subprocess
import sys

def clear_cache():
    """清除uv缓存"""
    cache_dir = os.path.expanduser("~/.local/share/uv")
    if os.path.exists(cache_dir):
        print(f"清除缓存目录: {cache_dir}")
        shutil.rmtree(cache_dir, ignore_errors=True)
    
    cache_dir = os.path.expanduser("~/.cache/uv")
    if os.path.exists(cache_dir):
        print(f"清除缓存目录: {cache_dir}")
        shutil.rmtree(cache_dir, ignore_errors=True)
    
    cache_dir = os.path.expanduser("~/AppData/Local/uv/cache")
    if os.path.exists(cache_dir):
        print(f"清除缓存目录: {cache_dir}")
        shutil.rmtree(cache_dir, ignore_errors=True)

def install_dependencies():
    """安装依赖"""
    print("安装anyio模块...")
    try:
        # 尝试使用uv安装
        subprocess.run(["uv", "pip", "install", "anyio"], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            # 如果uv不可用，尝试使用pip
            subprocess.run([sys.executable, "-m", "pip", "install", "anyio"], check=True)
        except subprocess.CalledProcessError:
            print("警告: 无法安装anyio模块，某些功能可能无法正常工作")
    
    print("安装xtquantai包...")
    try:
        # 尝试使用uv安装
        subprocess.run(["uv", "pip", "install", "-e", "."], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            # 如果uv不可用，尝试使用pip
            subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        except subprocess.CalledProcessError:
            print("警告: 无法安装xtquantai包，某些功能可能无法正常工作")

def run_xtquantai():
    """运行xtquantai"""
    print("运行xtquantai...")
    # 添加当前目录到Python路径
    sys.path.insert(0, os.path.abspath('.'))
    
    # 清除可能的缓存
    import importlib
    try:
        import xtquantai
        importlib.reload(xtquantai)
        
        # 运行xtquantai
        xtquantai.main()
    except ImportError:
        print("错误: 无法导入xtquantai模块")
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    clear_cache()
    install_dependencies()
    run_xtquantai() 