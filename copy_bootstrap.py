#!/usr/bin/env python3
"""查找Flask-Bootstrap的静态文件位置"""

import os
import sys
import flask_bootstrap

print("=" * 60)
print("查找Flask-Bootstrap静态文件")
print("=" * 60)

# 获取Flask-Bootstrap的安装位置
bootstrap_path = os.path.dirname(flask_bootstrap.__file__)
print(f"\nFlask-Bootstrap位置: {bootstrap_path}")

# 查找static文件夹
static_path = os.path.join(bootstrap_path, "static")
if os.path.exists(static_path):
    print(f"\n找到static文件夹!")
    for root, dirs, files in os.walk(static_path):
        level = root.replace(static_path, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files[:5]:  # 只显示前5个文件
            print(f'{subindent}{file}')
        if len(files) > 5:
            print(f'{subindent}... 还有 {len(files)-5} 个文件')
else:
    print(f"\n未找到static文件夹")

# 复制Bootstrap文件
print("\n" + "=" * 60)
print("复制Bootstrap文件到vendor目录")
print("=" * 60)

import shutil

vendor_js = "d:\\code\\stocks\\static\\vendor\\js"
os.makedirs(vendor_js, exist_ok=True)

# 查找bootstrap.js文件
bootstrap_js_paths = [
    os.path.join(static_path, "js", "bootstrap.min.js"),
    os.path.join(static_path, "js", "bootstrap.bundle.min.js"),
    os.path.join(static_path, "bootstrap", "js", "bootstrap.min.js"),
    os.path.join(static_path, "bootstrap", "js", "bootstrap.bundle.min.js"),
]

for src in bootstrap_js_paths:
    if os.path.exists(src):
        print(f"\n找到: {src}")
        dst = os.path.join(vendor_js, os.path.basename(src))
        shutil.copy2(src, dst)
        print(f"  复制到: {dst}")
        print(f"  大小: {os.path.getsize(dst)} bytes")

# 验证
print("\n" + "=" * 60)
print("验证vendor/js目录:")
print("=" * 60)
for f in os.listdir(vendor_js):
    fpath = os.path.join(vendor_js, f)
    print(f"  {f}: {os.path.getsize(fpath)} bytes")

print("\n" + "=" * 60)
