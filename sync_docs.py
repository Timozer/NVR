#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NVR App - 官方“隐私政策”与“用户协议” Markdown 全自动同步至 HTML 网页脚本
该脚本无需任何第三方包依赖，纯原生 Python 3 实现。

用法：
  python3 sync_docs.py        <- 仅执行本地同步 (Markdown -> HTML)
  python3 sync_docs.py --push <- 执行本地同步，并自动 Git 提交推送至 GitHub 远程仓库
"""

import os
import re
import sys
import subprocess

# 相对路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 隐私政策文件路径
MD_PRIVACY_ZH = os.path.join(BASE_DIR, "PRIVACY_ZH.md")
MD_PRIVACY_EN = os.path.join(BASE_DIR, "PRIVACY_EN.md")
HTML_PRIVACY = os.path.join(BASE_DIR, "docs", "privacy.html")

# 用户协议文件路径
MD_TERMS_ZH = os.path.join(BASE_DIR, "TERMS_ZH.md")
MD_TERMS_EN = os.path.join(BASE_DIR, "TERMS_EN.md")
HTML_TERMS = os.path.join(BASE_DIR, "docs", "terms.html")

def md_to_html(md_path):
    """
    轻量级原生 Markdown 到符合 HTML 标准的 HTML 转换器
    支持三级标题、列表、粗体以及常规换行段落。
    """
    if not os.path.exists(md_path):
        print(f"❌ 错误：找不到 Markdown 文件：{md_path}")
        return ""

    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    html_parts = []
    in_list = False

    for line in lines:
        line = line.strip()
        
        # 1. 忽略或跳过最顶部大标题 (例如 # NVR 隐私政策)
        if line.startswith("# ") or not line:
            if not line and in_list:
                html_parts.append("</ul>")
                in_list = False
            continue

        # 2. 解析标题 (### 转换为 <h2>)
        if line.startswith("### "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            title_text = line.replace("### ", "", 1).strip()
            html_parts.append(f"<h2>{title_text}</h2>")
            continue

        # 3. 解析列表项 (以 - 或数字 1. 2. 开头)
        list_match = re.match(r'^(?:-|\d+\.)\s*(.*)$', line)
        if list_match:
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            
            item_text = list_match.group(1)
            # 格式化粗体 **text**
            item_text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', item_text)
            # 格式化中文字符中可能出现的【】
            item_text = re.sub(r'【([^】]+)】', r'<strong>【\1】</strong>', item_text)
            
            html_parts.append(f"<li>{item_text}</li>")
            continue

        # 4. 普通段落解析
        if in_list:
            html_parts.append("</ul>")
            in_list = False
            
        # 格式化粗体 **text**
        paragraph_text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', line)
        # 格式化中文字符中可能出现的【】
        paragraph_text = re.sub(r'【([^】]+)】', r'<strong>【\1】</strong>', paragraph_text)
        
        html_parts.append(f"<p>{paragraph_text}</p>")

    if in_list:
        html_parts.append("</ul>")

    return "".join(html_parts)

def sync_file(md_zh_path, md_en_path, html_tmpl_path, content_key):
    """
    通用单网页文件同步函数
    """
    print(f"📖 正在解析 {os.path.basename(md_zh_path)} & {os.path.basename(md_en_path)}...")
    html_zh = md_to_html(md_zh_path)
    html_en = md_to_html(md_en_path)
    
    if not html_zh or not html_en:
        return False
        
    print(f"📄 正在读取 {os.path.basename(html_tmpl_path)}...")
    with open(html_tmpl_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # 精准替换英文内容
    en_pattern = rf'(// \[START_EN_CONTENT\]\s*{content_key}:\s*`)[^`]*(`\s*// \[END_EN_CONTENT\])'
    if not re.search(en_pattern, html_content):
        print(f"❌ 错误：在 {html_tmpl_path} 中找不到英文占位符 {content_key}")
        return False
    html_content = re.sub(en_pattern, rf'\1{html_en}\2', html_content)

    # 精准替换中文内容
    zh_pattern = rf'(// \[START_ZH_CONTENT\]\s*{content_key}:\s*`)[^`]*(`\s*// \[END_ZH_CONTENT\])'
    if not re.search(zh_pattern, html_content):
        print(f"❌ 错误：在 {html_tmpl_path} 中找不到中文占位符 {content_key}")
        return False
    html_content = re.sub(zh_pattern, rf'\1{html_zh}\2', html_content)

    print(f"💾 正在保存更新至 {os.path.basename(html_tmpl_path)}...")
    with open(html_tmpl_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return True

def main():
    print("🔄 开始执行 NVR 全自动多语言文档网页同步...")
    
    # 1. 同步隐私政策网页
    privacy_success = sync_file(MD_PRIVACY_ZH, MD_PRIVACY_EN, HTML_PRIVACY, "privacy_content")
    
    # 2. 同步服务协议网页
    terms_success = sync_file(MD_TERMS_ZH, MD_TERMS_EN, HTML_TERMS, "terms_content")
    
    if not privacy_success or not terms_success:
        print("❌ 部分网页同步失败，同步中止。")
        return False
        
    print("✨ 恭喜！本地“隐私政策网页”和“用户协议网页”均已与最新 Markdown 文档实现完美对齐！")
    return True

def run_git_push():
    print("🚀 正在自动执行一键 Git 提交与全球同步推送...")
    try:
        # 1. git add 所有必要的文件与更新网页
        subprocess.run([
            "git", "add", 
            "PRIVACY_ZH.md", "PRIVACY_EN.md", 
            "TERMS_ZH.md", "TERMS_EN.md", 
            "docs/index.html", "docs/privacy.html", "docs/terms.html",
            "sync_docs.py"
        ], cwd=BASE_DIR, check=True)
        
        # 2. git commit
        subprocess.run(["git", "commit", "-m", "docs: auto-sync privacy policy and terms of service to bilingual html pages"], cwd=BASE_DIR, check=True)
        
        # 3. git push
        result = subprocess.run(["git", "push"], cwd=BASE_DIR, capture_output=True, text=True, check=True)
        print("✅ Git 提交推送成功！所有双语网页和 Markdown 文档在全球端均已更新！")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ Git 自动同步失败。错误详情：")
        print(e.stderr if hasattr(e, 'stderr') else e)

if __name__ == "__main__":
    success = main()
    
    # 检查是否传入了 --push 参数
    if success and len(sys.argv) > 1 and sys.argv[1] == "--push":
        run_git_push()
