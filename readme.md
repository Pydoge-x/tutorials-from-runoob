# 菜鸟教程爬虫 (Runoob Crawler)

一个用于爬取菜鸟教程 (runoob.com) 内容的 Python 工具，支持将教程转换为 HTML 和 PDF 格式。

## 功能特性

- 支持爬取多个教程分类
- 自动将 HTML 转换为 PDF
- **智能跳过已爬取的内容**（避免重复爬取）
- 支持配置文件管理教程 URL
- 支持自动发现网站上所有可用教程
- 使用 URL 映射精确跟踪已爬取内容
- 完整的日志记录

## 安装依赖

```bash
pip install requests beautifulsoup4 selenium webdriver-manager tqdm pdfkit
```

### 额外要求

1. **Chrome 浏览器** - 用于渲染动态页面
2. **wkhtmltopdf** - 用于将 HTML 转换为 PDF
   - Windows: 从 https://wkhtmltopdf.org/downloads.html 下载并安装
   - Linux: `sudo apt-get install wkhtmltopdf`
   - macOS: `brew install wkhtmltopdf`

## 快速开始

### 1. 为已有内容生成 URL 映射（可选）

如果之前已经爬取过一些内容，先运行：

```bash
python generate_mapping.py
```

这会扫描现有的 HTML 文件，从文件中提取原始 URL 并生成 `url_mapping.json` 映射文件。

### 2. 初始化配置文件

```bash
python crawler.py --init-config
```

这会创建一个 `config.json` 文件。

### 3. 编辑配置文件

修改 `config.json`，添加你想爬取的教程 URL：

```json
{
  "category_urls": [
    "https://www.runoob.com/pytorch/pytorch-tutorial.html",
    "https://www.runoob.com/python3/python3-tutorial.html",
    "https://www.runoob.com/tensorflow/tensorflow-tutorial.html"
  ],
  "delay": 1.5
}
```

### 4. 开始爬取

```bash
python crawler.py
```

程序会自动跳过已爬取的内容！

## 命令行参数

| 参数                 | 说明                                   | 示例                                                                                    |
| -------------------- | -------------------------------------- | --------------------------------------------------------------------------------------- |
| `--init-config`    | 创建默认配置文件                       | `python crawler.py --init-config`                                                     |
| `--config <path>`  | 指定配置文件路径                       | `python crawler.py --config myconfig.json`                                            |
| `--limit <n>`      | 限制每个分类爬取的教程数量             | `python crawler.py --limit 10`                                                        |
| `--delay <秒>`     | 请求间隔时间（秒），默认 1.5           | `python crawler.py --delay 2`                                                         |
| `--category <url>` | 爬取指定分类                           | `python crawler.py --category "https://www.runoob.com/python3/python3-tutorial.html"` |
| `--url <url>`      | 爬取单个教程页面                       | `python crawler.py --url "https://www.runoob.com/python3/python3-basic-syntax.html"`  |
| `--urls <urls>`    | 爬取多个 URL（逗号分隔）               | `python crawler.py --urls "url1,url2,url3"`                                           |
| `--discover`       | 自动发现网站上所有可用教程分类         | `python crawler.py --discover`                                                        |
| `--check-crawled`  | 查看已爬取的文件列表                   | `python crawler.py --check-crawled`                                                   |
| `--no-skip`        | 强制重新爬取所有内容（不跳过已存在的） | `python crawler.py --no-skip`                                                         |

## 使用示例

### 查看帮助

```bash
python crawler.py --help
```

### 发现可用的教程分类

```bash
python crawler.py --discover
```

输出示例：

```
Found 50+ tutorial categories:
  1. https://www.runoob.com/python3/python3-tutorial.html
  2. https://www.runoob.com/java/java-tutorial.html
  3. https://www.runoob.com/c/c-tutorial.html
  ...
```

### 爬取单个教程分类

```bash
python crawler.py --category "https://www.runoob.com/pytorch/pytorch-tutorial.html"
```

### 爬取单个教程页面

```bash
python crawler.py --url "https://www.runoob.com/python3/python3-basic-syntax.html"
```

### 爬取多个 URL

```bash
python crawler.py --urls "https://www.runoob.com/python3/python3-tutorial.html,https://www.runoob.com/pytorch/pytorch-tutorial.html"
```

### 限制爬取数量

```bash
python crawler.py --category "https://www.runoob.com/pytorch/pytorch-tutorial.html" --limit 5
```

### 强制重新爬取（忽略已有文件）

```bash
python crawler.py --no-skip
```

### 查看已爬取的内容

```bash
python crawler.py --check-crawled
```

## 去重机制

### 工作原理

程序使用 **URL 映射文件** 来精确跟踪已爬取的内容：

1. **精确匹配** - 每次爬取成功后，将 URL 和文件名记录到 `runoob_content/url_mapping.json`
2. **下次运行时** - 自动检查 URL 是否已在映射表中
3. **自动跳过** - 已存在的 URL 会自动跳过，只爬取新的内容

### 手动生成映射

如果之前已经爬取过内容，需要生成 URL 映射：

```bash
python generate_mapping.py
```

这会扫描所有 HTML 文件，从文件内容中提取原始 URL 并生成映射。

### 查看映射文件

映射文件位置：`runoob_content/url_mapping.json`

内容格式：

```json
{
  "https://www.runoob.com/pytorch/pytorch-tensor.html": "PyTorch-张量Tensor.html",
  "https://www.runoob.com/pytorch/pytorch-intro.html": "PyTorch-简介.html"
}
```

## 输出目录

爬取的内容会保存到以下目录：

- **HTML 文件**: `runoob_content/`
- **PDF 文件**: `runoob_pdf/`
- **URL 映射**: `runoob_content/url_mapping.json`
- **爬取摘要**: `runoob_content/crawl_summary.json`

每个教程分类会创建对应的子目录。

## 配置文件说明

`config.json` 文件示例：

```json
{
  "category_urls": [
    "https://www.runoob.com/pytorch/pytorch-tutorial.html",
    "https://www.runoob.com/tensorflow/tensorflow-tutorial.html"
  ],
  "delay": 1.5,
  "auto_discover": false
}
```

### 配置项说明

| 配置项            | 类型 | 说明                             |
| ----------------- | ---- | -------------------------------- |
| `category_urls` | 数组 | 要爬取的教程分类 URL 列表        |
| `delay`         | 数字 | 请求间隔时间（秒），建议 1-3     |
| `auto_discover` | 布尔 | 是否自动发现教程分类（保留字段） |

## 常见问题

### Q: 为什么 PDF 转换失败？

A: 确保已正确安装 wkhtmltopdf。在 Windows 上，可能需要指定完整路径。默认路径：`C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe`

### Q: 如何跳过已爬取的内容？

A: 默认行为就是跳过已存在的文件。如需强制重新爬取，使用 `--no-skip` 参数。

### Q: 爬取速度太慢怎么办？

A: 可以减少 `--delay` 参数值（但可能被网站封 IP），或者使用 `--limit` 限制爬取数量。

### Q: Chrome 驱动启动失败怎么办？

A: 程序会自动降级到使用 requests 库，虽然速度较慢但可以继续工作。

### Q: 之前爬取的内容没有被跳过？

A: 运行 `python generate_mapping.py` 生成 URL 映射文件后再试。

## 目录结构

```
tutorials-from-runoob/
├── crawler.py           # 主程序
├── config.json          # 配置文件（自动生成）
├── generate_mapping.py # 生成URL映射脚本
├── README.md            # 说明文档
├── MANUAL.md            # 详细使用手册
├── runoob_content/     # HTML 输出目录
│   ├── url_mapping.json # URL 映射文件
│   ├── crawl_summary.json
│   └── PyTorch/
│       └── *.html
└── runoob_pdf/         # PDF 输出目录
    └── PyTorch/
        └── *.pdf
```

## 许可证

仅供学习交流使用，请勿用于商业目的。
