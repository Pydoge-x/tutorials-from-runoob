# 菜鸟教程爬虫 - 详细使用手册

## 目录

1. [简介](#1-简介)
2. [安装配置](#2-安装配置)
3. [快速开始](#3-快速开始)
4. [命令行详解](#4-命令行详解)
5. [配置文件](#5-配置文件)
6. [去重机制](#6-去重机制)
7. [高级用法](#7-高级用法)
8. [故障排除](#8-故障排除)

---

## 1. 简介

本工具用于自动化爬取菜鸟教程 (runoob.com) 的教程内容，并支持转换为 PDF 格式离线阅读。

### 主要功能

| 功能 | 说明 |
|------|------|
| 多分类爬取 | 支持同时爬取多个教程分类 |
| 自动转PDF | 将爬取的HTML自动转换为PDF |
| **增量爬取** | 使用URL映射精确跳过已爬取的内容 |
| 智能限速 | 可配置请求间隔，避免被封 |
| 自动发现 | 自动扫描网站上的所有教程分类 |

---

## 2. 安装配置

### 2.1 Python 环境

```bash
# Python 3.7+
python --version
```

### 2.2 安装依赖

```bash
pip install requests beautifulsoup4 selenium webdriver-manager tqdm pdfkit
```

### 2.3 安装 wkhtmltopdf

**Windows:**
1. 下载: https://wkhtmltopdf.org/downloads.html
2. 安装到默认路径: `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe`

**Linux:**
```bash
sudo apt-get install wkhtmltopdf
```

**macOS:**
```bash
brew install wkhtmltopdf
```

---

## 3. 快速开始

### 3.1 首次使用

```bash
# 1. 初始化配置文件
python crawler.py --init-config

# 2. 编辑 config.json，添加你想爬取的教程 URL

# 3. 开始爬取
python crawler.py
```

### 3.2 后续使用（增量爬取）

```bash
# 直接运行，会自动跳过已爬取的内容
python crawler.py
```

### 3.3 处理之前爬取的内容

如果之前已经爬取过一些内容，需要生成 URL 映射：

```bash
python generate_mapping.py
```

这会扫描所有 HTML 文件，从文件内容中提取原始 URL 并生成映射。

---

## 4. 命令行详解

### 4.1 基础命令

```bash
# 查看帮助
python crawler.py --help
```

### 4.2 参数一览

#### 初始化与配置

```bash
# 创建默认配置文件
python crawler.py --init-config

# 指定配置文件路径
python crawler.py --config my-config.json
```

#### 爬取模式

```bash
# 使用配置文件中的URL爬取（默认）
python crawler.py

# 爬取单个教程分类
python crawler.py --category "URL"

# 爬取单个教程页面
python crawler.py --url "URL"

# 爬取多个URL（逗号分隔）
python crawler.py --urls "URL1,URL2,URL3"
```

#### 控制选项

```bash
# 限制每个分类爬取的教程数量
python crawler.py --limit 10

# 设置请求延迟（秒）
python crawler.py --delay 2

# 强制重新爬取所有内容（不跳过已存在的文件）
python crawler.py --no-skip
```

#### 信息查看

```bash
# 自动发现可用的教程分类
python crawler.py --discover

# 查看已爬取的文件列表
python crawler.py --check-crawled
```

### 4.3 组合示例

```bash
# 爬取前5个教程，跳过已存在的
python crawler.py --category "URL" --limit 5

# 强制重新爬取前10个
python crawler.py --category "URL" --limit 10 --no-skip

# 使用自定义配置文件爬取
python crawler.py --config my-config.json --limit 20
```

---

## 5. 配置文件

### 5.1 文件位置

默认配置文件为 `config.json`，位于程序同级目录。

### 5.2 配置项

```json
{
  "category_urls": [
    "https://www.runoob.com/pytorch/pytorch-tutorial.html",
    "https://www.runoob.com/tensorflow/tensorflow-tutorial.html",
    "https://www.runoob.com/python3/python3-tutorial.html"
  ],
  "delay": 1.5,
  "auto_discover": false
}
```

| 配置项 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `category_urls` | 数组 | 是 | 要爬取的教程分类 URL 列表 |
| `delay` | 数字 | 否 | 请求间隔时间（秒），默认 1.5 |
| `auto_discover` | 布尔 | 否 | 保留字段，暂时无效 |

### 5.3 获取教程URL

运行以下命令查看可用的教程分类：

```bash
python crawler.py --discover
```

常见的教程URL格式：
- Python: `https://www.runoob.com/python3/python3-tutorial.html`
- PyTorch: `https://www.runoob.com/pytorch/pytorch-tutorial.html`
- TensorFlow: `https://www.runoob.com/tensorflow/tensorflow-tutorial.html`
- Java: `https://www.runoob.com/java/java-tutorial.html`
- C: `https://www.runoob.com/c/c-tutorial.html`
- Go: `https://www.runoob.com/go/go-tutorial.html`

---

## 6. 去重机制

### 6.1 工作原理

程序使用 **URL 映射文件** 来精确跟踪已爬取的内容：

1. **精确匹配** - 每次爬取成功后，将 URL 和文件名记录到 `runoob_content/url_mapping.json`
2. **下次运行时** - 自动检查 URL 是否已在映射表中
3. **自动跳过** - 已存在的 URL 会自动跳过，只爬取新的内容

### 6.2 生成映射文件

对于之前已经爬取的内容，需要手动生成 URL 映射：

```bash
python generate_mapping.py
```

这会：
- 扫描 `runoob_content/` 目录下的所有 HTML 文件
- 从每个文件内容中提取"原文链接"
- 生成 `url_mapping.json` 映射文件

### 6.3 查看已爬取

```bash
python crawler.py --check-crawled
```

### 6.4 强制重新爬取

```bash
python crawler.py --no-skip
```

这会忽略已有的映射文件，重新爬取所有内容。

### 6.5 映射文件格式

位置：`runoob_content/url_mapping.json`

```json
{
  "https://www.runoob.com/pytorch/pytorch-tensor.html": "PyTorch-张量Tensor.html",
  "https://www.runoob.com/pytorch/pytorch-intro.html": "PyTorch-简介.html",
  "https://www.runoob.com/pytorch/pytorch-install.html": "PyTorch-安装.html"
}
```

---

## 7. 高级用法

### 7.1 使用不同的配置文件

```bash
# 生产环境配置
python crawler.py --config production.json

# 测试环境配置
python crawler.py --config test.json
```

### 7.2 批量测试新分类

```bash
# 先限制数量测试
python crawler.py --category "NEW_URL" --limit 3

# 测试没问题后完整爬取
python crawler.py --category "NEW_URL"
```

### 7.3 增量更新多个分类

配置文件中有多个分类时，直接运行即可自动跳过已存在的：

```bash
python crawler.py
```

### 7.4 完整工作流示例

```bash
# 1. 发现可用的教程分类
python crawler.py --discover

# 2. 初始化配置文件
python crawler.py --init-config

# 3. 编辑 config.json 添加想要的分类

# 4. 首次爬取（可能有很多内容）
python crawler.py --limit 10  # 先测试10个

# 5. 完整爬取
python crawler.py

# 6. 之后每次运行会自动跳过已存在的
python crawler.py

# 7. 查看已爬取的内容
python crawler.py --check-crawled
```

---

## 8. 故障排除

### 8.1 PDF 转换失败

**问题:** 提示 wkhtmltopdf 找不到

**解决方案:**

1. 确认已安装 wkhtmltopdf
2. Windows 上检查路径: `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe`
3. 将路径添加到系统 PATH 环境变量

### 8.2 Chrome 驱动失败

**问题:** Chrome 驱动启动失败

**解决方案:**

程序会自动降级到使用 requests 库，虽然可能无法获取动态渲染的内容，但可以继续工作。

### 8.3 爬取被拦截

**问题:** 请求被网站拒绝

**解决方案:**

1. 增加 `--delay` 参数值
2. 使用 `--no-skip` 前确保没有重复爬取
3. 更换网络环境

### 8.4 之前爬取的内容没有被跳过

**问题:** 运行爬虫时，没有跳过之前已经爬取的内容

**解决方案:**

```bash
# 运行 generate_mapping.py 生成 URL 映射
python generate_mapping.py

# 然后再运行爬虫
python crawler.py
```

### 8.5 中文乱码

**问题:** 保存的文件名或内容乱码

**解决方案:**

程序已使用 UTF-8 编码，如仍有问题，检查系统默认编码设置。

---

## 命令速查表

| 需求 | 命令 |
|------|------|
| 首次使用 | `python crawler.py --init-config` |
| 编辑配置 | 修改 `config.json` 文件 |
| 开始爬取 | `python crawler.py` |
| 查看帮助 | `python crawler.py --help` |
| 发现教程 | `python crawler.py --discover` |
| 查看已爬取 | `python crawler.py --check-crawled` |
| 强制重爬 | `python crawler.py --no-skip` |
| 限制数量 | `python crawler.py --limit 10` |
| 单个分类 | `python crawler.py --category "URL"` |
| 单个页面 | `python crawler.py --url "URL"` |
| 多个URL | `python crawler.py --urls "URL1,URL2"` |
| 生成映射 | `python generate_mapping.py` |

---

## 输出文件说明

| 文件/目录 | 说明 |
|-----------|------|
| `runoob_content/` | HTML 文件输出目录 |
| `runoob_pdf/` | PDF 文件输出目录 |
| `runoob_content/url_mapping.json` | URL 映射文件（去重用） |
| `runoob_content/crawl_summary.json` | 爬取摘要记录 |
| `config.json` | 用户配置文件 |
