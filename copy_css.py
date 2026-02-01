#!/usr/bin/env python3
"""复制Bootstrap CSS文件"""

import os
import shutil
import flask_bootstrap

print("=" * 60)
print("复制Bootstrap CSS文件")
print("=" * 60)

# 获取Flask-Bootstrap的static文件夹
bootstrap_path = os.path.dirname(flask_bootstrap.__file__)
static_path = os.path.join(bootstrap_path, "static")

# 目标目录
vendor_css = "d:\\code\\stocks\\static\\vendor\\css"
os.makedirs(vendor_css, exist_ok=True)

# 查找bootstrap.css文件
css_files = [
    ("bootstrap.min.css", os.path.join(static_path, "css", "bootstrap.min.css")),
    ("bootstrap.css", os.path.join(static_path, "css", "bootstrap.css")),
]

print(f"\nFlask-Bootstrap CSS目录: {os.path.join(static_path, 'css')}")
if os.path.exists(os.path.join(static_path, 'css')):
    print("  可用文件:")
    for f in os.listdir(os.path.join(static_path, 'css')):
        print(f"    - {f}")

print("\n复制文件:")
for filename, src in css_files:
    if os.path.exists(src):
        dst = os.path.join(vendor_css, filename)
        shutil.copy2(src, dst)
        print(f"  ✅ {filename}: {os.path.getsize(dst)} bytes")
    else:
        print(f"  ❌ {filename}: 不存在")

# 验证
print("\n" + "=" * 60)
print("验证vendor/css目录:")
print("=" * 60)
for f in os.listdir(vendor_css):
    fpath = os.path.join(vendor_css, f)
    print(f"  {f}: {os.path.getsize(fpath)} bytes")
