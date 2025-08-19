# 漫畫圖片自動化下載工具

一個功能強大的漫畫圖片爬取和自動下載工具，支持多種下載模式和CSV導出功能。

## 🚀 主要功能

- **智能圖片爬取**: 使用Selenium自動化瀏覽器，支持多種圖片元素類型
- **自動下載模式**: 爬取完成後直接下載圖片，無需額外步驟
- **CSV導出**: 將圖片信息導出為CSV文件，支持後續批量下載
- **多種圖片類型支持**: img標籤、canvas、背景圖片、SVG、picture標籤等
- **智能文件名生成**: 自動提取漫畫標題，生成有意義的文件名

## 📦 安裝依賴

```bash
pip install -r requirements.txt
```

### 必需依賴
- `selenium`: 瀏覽器自動化
- `requests`: HTTP請求
- `Chrome瀏覽器` + `ChromeDriver`: 瀏覽器驅動

## 使用方式

**目前僅針對 [ganma.jp](https://ganma.jp/web)，可供下載**

### 方式1: 爬取並自動下載（推薦）

```bash
python manga_browser_scraper.py -u "漫畫網址" --auto-download --output-dir "目標資料夾"
```

**參數說明:**
- `-u, --url`: 漫畫頁面URL（必需）
- `--auto-download`: 啟用自動下載模式
- `--output-dir`: 圖片保存目錄（默認: downloaded_images）
- `--headless`: 無頭模式，不顯示瀏覽器窗口
- `--wait`: 頁面加載等待時間（秒，默認: 5）
- `--delay`: 下載延遲時間（秒，默認: 0.5）

**示例:**
```bash
# 基本自動下載
python manga_browser_scraper.py -u "https://ganma.jp/comic/123" --auto-download --output-dir "目標資料夾"

# 自定義輸出目錄和延遲
python manga_browser_scraper.py -u "https://ganma.jp/comic/123" --auto-download --output-dir "my_manga" --delay 1.0

# 無頭模式（後台運行）
python manga_browser_scraper.py -u "https://ganma.jp/comic/123" --auto-download --headless
```

### 方式2: 只爬取不下載（輸出CSV）

```bash
python manga_browser_scraper.py -u "https://ganma.jp/..."
```

這種方式會：
1. 爬取頁面中的所有圖片
2. 生成CSV文件（包含圖片URL、類型、屬性等）
3. 保存到 `output/` 目錄

### 方式3: 從CSV文件下載

```bash
python download_form_csv.py
```

然後按提示輸入：
- CSV文件路徑
- 輸出目錄
- 下載延遲時間

## �� 輸出文件說明

### 自動下載模式
```
my_manga_images/
├── 漫畫標題_img_001.webp
├── 漫畫標題_img_002.webp
├── 漫畫標題_canvas_003.png
└── ...
```

### CSV導出模式
```
output/
├── manga_detailed_ganma.jp_20241201_143022.json    # 詳細JSON數據
├── manga_simple_ganma.jp_20241201_143022.txt       # 簡化文本報告
└── manga_images_ganma.jp_20241201_143022.csv       # 圖片信息CSV
```

##  CSV文件格式

CSV文件包含以下列：
- `index`: 圖片索引
- `type`: 圖片類型（img_tag, canvas, background_image, svg, picture, js_extracted）
- `url`: 圖片URL
- `alt`: 圖片alt屬性
- `title`: 圖片title屬性
- `width`: 圖片寬度
- `height`: 圖片高度
- `class`: CSS類名
- `id`: 元素ID
- `manga_title`: 漫畫標題
- `page_title`: 頁面標題
- `extract_time`: 提取時間

##  高級配置

### 自定義請求頭
在 `manga_browser_scraper.py` 中修改：
```python
headers = {
    'User-Agent': '你的User-Agent',
    'Referer': '你的Referer',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
}
```

### 調整等待時間
```bash
# 增加頁面加載等待時間
python manga_browser_scraper.py -u "..." --wait 10

# 增加下載延遲
python manga_browser_scraper.py -u "..." --delay 2.0
```

## ⚠️ 注意事項

1. **網絡延遲**: 建議設置適當的下載延遲，避免被網站封鎖
2. **文件命名**: 文件名會自動清理非法字符，長度限制為30字符
3. **瀏覽器要求**: 需要安裝Chrome瀏覽器和對應版本的ChromeDriver
4. **圖片格式**: 支持常見圖片格式（jpg, png, webp, gif等）

## 🐛 常見問題

### Q: 圖片下載失敗怎麼辦？
A: 檢查網絡連接，嘗試增加延遲時間，或檢查圖片URL是否有效

### Q: 文件名還是顯示"unknown"？
A: 網站可能沒有標準的標題結構，程序會自動使用頁面標題或域名

### Q: 瀏覽器啟動失敗？
A: 確保已安裝Chrome瀏覽器和ChromeDriver，版本要匹配

### Q: 如何批量處理多個URL？
A: 可以寫一個簡單的腳本循環調用，或使用批處理文件

##  更新日誌

- **v2.0**: 整合自動下載功能，支持CSV導出
- **v1.0**: 基礎圖片爬取功能

##  貢獻

歡迎提交Issue和Pull Request來改進這個工具！

##  許可證

本項目僅供學習和研究使用，請遵守相關網站的使用條款。
```

這個README文檔涵蓋了：

1. **功能概述**: 清楚說明工具的主要功能
2. **安裝說明**: 依賴安裝步驟
3. **使用方式**: 三種不同的使用模式，每種都有詳細示例
4. **輸出說明**: 文件結構和CSV格式
5. **配置選項**: 高級配置和參數說明
6. **常見問題**: 幫助用戶解決可能遇到的問題

你可以根據需要調整內容，或者添加其他特定的說明！
