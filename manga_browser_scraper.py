import time
import json
import os
import requests
from datetime import datetime
from urllib.parse import urlparse, urljoin
import argparse
import csv

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("❌ 需要安裝selenium: pip install selenium")
    exit(1)

class MangaBrowserScraper:
    def __init__(self, headless=False, wait_time=5, auto_download=False, output_dir="downloaded_images", delay=0.5):
        """初始化瀏覽器爬蟲"""
        self.wait_time = wait_time
        self.driver = None
        self.auto_download = auto_download
        self.output_dir = output_dir
        self.delay = delay
        self.setup_driver(headless)
        
        # 設置下載相關
        if self.auto_download:
            self.setup_downloader()
    
    def setup_downloader(self):
        """設置下載器"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://ganma.jp/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
        })
        
        # 創建輸出目錄
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"📁 自動下載模式已啟用，圖片將保存到: {os.path.abspath(self.output_dir)}")
    
    def setup_driver(self, headless):
        """設置Chrome瀏覽器驅動"""
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument("--headless")
            
            # 基本設置
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome瀏覽器啟動成功")
            
        except Exception as e:
            print(f"❌ 瀏覽器啟動失敗: {e}")
            print("請確保已安裝Chrome瀏覽器和ChromeDriver")
            exit(1)
    
    def scrape_manga_page(self, url):
        """爬取漫畫頁面"""
        try:
            print(f"🌐 正在訪問: {url}")
            self.driver.get(url)
            
            # 等待頁面加載
            print("⏳ 等待頁面加載...")
            time.sleep(self.wait_time)
            
            # 等待JavaScript執行完成
            self.wait_for_page_load()
            
            # 獲取頁面信息
            page_info = self.extract_page_info(url)
            
            # 獲取所有圖片
            images = self.extract_all_images()
            
            # 保存結果
            self.save_results(url, page_info, images)
            
            # 如果啟用自動下載，直接下載圖片
            if self.auto_download and images:
                self.download_images_auto(images, page_info)
            
            return {
                'page_info': page_info,
                'images': images
            }
            
        except Exception as e:
            print(f"❌ 爬取失敗: {e}")
            return None
    
    def wait_for_page_load(self):
        """等待頁面完全加載"""
        try:
            # 等待body元素出現
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 等待頁面加載完成
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 額外等待JavaScript執行
            time.sleep(2)
            
        except TimeoutException:
            print("⚠️ 頁面加載超時，繼續執行...")
    
    def extract_page_info(self, url):
        """提取頁面基本信息"""
        try:
            page_info = {
                'url': url,
                'title': self.driver.title,
                'timestamp': datetime.now().isoformat(),
                'user_agent': self.driver.execute_script("return navigator.userAgent"),
                'viewport': self.driver.execute_script("return window.innerWidth + 'x' + window.innerHeight")
            }
            
            # 嘗試獲取漫畫標題 - 改進標題提取邏輯
            manga_title = self.extract_manga_title()
            if manga_title:
                page_info['manga_title'] = manga_title
            else:
                # 如果沒有找到漫畫標題，使用頁面標題作為備選
                page_title = self.driver.title.strip()
                if page_title and page_title != "N/A":
                    # 清理頁面標題，移除網站名稱等
                    clean_title = self.clean_page_title(page_title)
                    page_info['manga_title'] = clean_title
                else:
                    # 使用域名作為最後備選
                    domain = urlparse(url).netloc.replace('.', '_')
                    page_info['manga_title'] = domain
            
            return page_info
            
        except Exception as e:
            print(f"⚠️ 提取頁面信息失敗: {e}")
            # 即使出錯也要提供一個有意義的標題
            domain = urlparse(url).netloc.replace('.', '_')
            return {
                'url': url, 
                'timestamp': datetime.now().isoformat(),
                'manga_title': domain
            }
    
    def extract_manga_title(self):
        """改進的漫畫標題提取方法"""
        try:
            # 嘗試多種選擇器來找到漫畫標題
            selectors = [
                "h1", 
                ".title", 
                ".manga-title", 
                ".comic-title",
                ".story-title",
                "[class*='title']",
                "[class*='manga']",
                "[class*='comic']",
                "[class*='story']",
                "title"  # 頁面標題
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 2 and len(text) < 100:  # 合理的標題長度
                            # 過濾掉明顯不是標題的內容
                            if not any(skip in text.lower() for skip in ['login', 'sign', 'menu', 'nav', 'footer']):
                                print(f"✅ 找到漫畫標題: {text}")
                                return text
                except:
                    continue
            
            # 如果CSS選擇器都沒找到，嘗試從頁面標題提取
            page_title = self.driver.title.strip()
            if page_title and page_title != "N/A":
                clean_title = self.clean_page_title(page_title)
                if clean_title:
                    print(f"✅ 從頁面標題提取: {clean_title}")
                    return clean_title
            
            return None
            
        except Exception as e:
            print(f"⚠️ 提取漫畫標題時出錯: {e}")
            return None
    
    def clean_page_title(self, title):
        """清理頁面標題，提取有用的部分"""
        try:
            # 移除常見的網站後綴
            suffixes = [
                ' - ganma.jp',
                ' | ganma.jp',
                ' - Ganma!',
                ' | Ganma!',
                ' - ガンマ',
                ' | ガンマ',
                ' - 漫画',
                ' | 漫画',
                ' - マンガ',
                ' | マンガ'
            ]
            
            clean_title = title
            for suffix in suffixes:
                if clean_title.endswith(suffix):
                    clean_title = clean_title[:-len(suffix)].strip()
                    break
            
            # 如果標題太長，截取前50個字符
            if len(clean_title) > 50:
                clean_title = clean_title[:50].strip()
            
            return clean_title if clean_title else None
            
        except Exception as e:
            print(f"⚠️ 清理標題時出錯: {e}")
            return None
    
    def extract_all_images(self):
        """提取頁面中的所有圖片"""
        images = []
        
        try:
            # 1. 提取img標籤圖片
            img_images = self.extract_img_tags()
            images.extend(img_images)
            
            # 2. 提取canvas元素
            canvas_images = self.extract_canvas_elements()
            images.extend(canvas_images)
            
            # 3. 提取背景圖片
            background_images = self.extract_background_images()
            images.extend(background_images)
            
            # 4. 提取SVG元素
            svg_images = self.extract_svg_elements()
            images.extend(svg_images)
            
            # 5. 提取picture標籤
            picture_images = self.extract_picture_elements()
            images.extend(picture_images)
            
            # 6. 從JavaScript變量中提取圖片URL
            js_images = self.extract_js_image_urls()
            images.extend(js_images)
            
            print(f"✅ 總共找到 {len(images)} 個圖片元素")
            
        except Exception as e:
            print(f"⚠️ 提取圖片時發生錯誤: {e}")
        
        return images
    
    def extract_img_tags(self):
        """提取img標籤圖片"""
        images = []
        try:
            img_elements = self.driver.find_elements(By.TAG_NAME, "img")
            print(f"找到 {len(img_elements)} 個img標籤")
            
            for i, img in enumerate(img_elements, 1):
                try:
                    img_info = {
                        'type': 'img_tag',
                        'index': i,
                        'src': img.get_attribute('src'),
                        'alt': img.get_attribute('alt'),
                        'title': img.get_attribute('title'),
                        'width': img.get_attribute('width'),
                        'height': img.get_attribute('height'),
                        'class': img.get_attribute('class'),
                        'id': img.get_attribute('id'),
                        'data_src': img.get_attribute('data-src'),
                        'loading': img.get_attribute('loading')
                    }
                    
                    # 清理空值
                    img_info = {k: v for k, v in img_info.items() if v}
                    images.append(img_info)
                    
                except Exception as e:
                    print(f"⚠️ 處理img標籤 {i} 時出錯: {e}")
            
        except Exception as e:
            print(f"⚠️ 提取img標籤失敗: {e}")
        
        return images
    
    def extract_canvas_elements(self):
        """提取canvas元素"""
        images = []
        try:
            canvas_elements = self.driver.find_elements(By.TAG_NAME, "canvas")
            print(f"找到 {len(canvas_elements)} 個canvas元素")
            
            for i, canvas in enumerate(canvas_elements, 1):
                try:
                    canvas_info = {
                        'type': 'canvas',
                        'index': i,
                        'width': canvas.get_attribute('width'),
                        'height': canvas.get_attribute('height'),
                        'class': canvas.get_attribute('class'),
                        'id': canvas.get_attribute('id'),
                        'data_url': canvas.get_attribute('data-url')
                    }
                    
                    # 嘗試獲取canvas的data URL
                    try:
                        data_url = self.driver.execute_script(
                            "return arguments[0].toDataURL('image/png');", canvas
                        )
                        if data_url and data_url.startswith('data:image'):
                            canvas_info['data_url'] = data_url[:100] + '...' if len(data_url) > 100 else data_url
                    except:
                        pass
                    
                    # 清理空值
                    canvas_info = {k: v for k, v in canvas_info.items() if v}
                    images.append(canvas_info)
                    
                except Exception as e:
                    print(f"⚠️ 處理canvas {i} 時出錯: {e}")
            
        except Exception as e:
            print(f"⚠️ 提取canvas失敗: {e}")
        
        return images
    
    def extract_background_images(self):
        """提取背景圖片"""
        images = []
        try:
            # 查找所有可能有背景圖片的元素
            elements_with_bg = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "[style*='background'], [style*='background-image']"
            )
            print(f"找到 {len(elements_with_bg)} 個帶背景樣式的元素")
            
            for i, element in enumerate(elements_with_bg, 1):
                try:
                    style = element.get_attribute('style')
                    if style and ('background' in style.lower() or 'background-image' in style.lower()):
                        bg_info = {
                            'type': 'background_image',
                            'index': i,
                            'style': style,
                            'tag': element.tag_name,
                            'class': element.get_attribute('class'),
                            'id': element.get_attribute('id')
                        }
                        images.append(bg_info)
                        
                except Exception as e:
                    print(f"⚠️ 處理背景樣式 {i} 時出錯: {e}")
            
        except Exception as e:
            print(f"⚠️ 提取背景圖片失敗: {e}")
        
        return images
    
    def extract_svg_elements(self):
        """提取SVG元素"""
        images = []
        try:
            svg_elements = self.driver.find_elements(By.TAG_NAME, "svg")
            print(f"找到 {len(svg_elements)} 個SVG元素")
            
            for i, svg in enumerate(svg_elements, 1):
                try:
                    svg_info = {
                        'type': 'svg',
                        'index': i,
                        'width': svg.get_attribute('width'),
                        'height': svg.get_attribute('height'),
                        'class': svg.get_attribute('class'),
                        'id': svg.get_attribute('id'),
                        'content': svg.get_attribute('outerHTML')[:200] + '...' if len(svg.get_attribute('outerHTML')) > 200 else svg.get_attribute('outerHTML')
                    }
                    images.append(svg_info)
                    
                except Exception as e:
                    print(f"⚠️ 處理SVG {i} 時出錯: {e}")
            
        except Exception as e:
            print(f"⚠️ 提取SVG失敗: {e}")
        
        return images
    
    def extract_picture_elements(self):
        """提取picture標籤"""
        images = []
        try:
            picture_elements = self.driver.find_elements(By.TAG_NAME, "picture")
            print(f"找到 {len(picture_elements)} 個picture標籤")
            
            for i, picture in enumerate(picture_elements, 1):
                try:
                    # 查找picture內的img
                    img = picture.find_element(By.TAG_NAME, "img")
                    if img:
                        picture_info = {
                            'type': 'picture',
                            'index': i,
                            'src': img.get_attribute('src'),
                            'srcset': img.get_attribute('srcset'),
                            'sizes': img.get_attribute('sizes'),
                            'alt': img.get_attribute('alt')
                        }
                        images.append(picture_info)
                        
                except Exception as e:
                    print(f"⚠️ 處理picture {i} 時出錯: {e}")
            
        except Exception as e:
            print(f"⚠️ 提取picture失敗: {e}")
        
        return images
    
    def extract_js_image_urls(self):
        """從JavaScript變量中提取圖片URL"""
        images = []
        try:
            # 執行JavaScript來查找可能的圖片URL
            js_code = """
            const imageUrls = [];
            
            // 查找全局變量中的圖片URL
            for (let key in window) {
                try {
                    const value = window[key];
                    if (typeof value === 'string' && value.includes('.jpg') || value.includes('.png') || value.includes('.webp')) {
                        if (value.startsWith('http')) {
                            imageUrls.push({
                                source: 'global_variable',
                                key: key,
                                url: value
                            });
                        }
                    }
                } catch (e) {}
            }
            
            // 查找data屬性中的圖片URL
            document.querySelectorAll('[data-*]').forEach(el => {
                for (let attr of el.attributes) {
                    if (attr.name.startsWith('data-') && (attr.value.includes('.jpg') || attr.value.includes('.png') || attr.value.includes('.webp'))) {
                        if (attr.value.startsWith('http')) {
                            imageUrls.push({
                                source: 'data_attribute',
                                element: el.tagName,
                                attribute: attr.name,
                                url: attr.value
                            });
                        }
                    }
                }
            });
            
            return imageUrls;
            """
            
            js_results = self.driver.execute_script(js_code)
            if js_results:
                print(f"從JavaScript中找到 {len(js_results)} 個圖片URL")
                for result in js_results:
                    result['type'] = 'js_extracted'
                    images.append(result)
            
        except Exception as e:
            print(f"⚠️ 從JavaScript提取圖片URL失敗: {e}")
        
        return images
    
    def download_images_auto(self, images, page_info):
        """自動下載圖片"""
        print(f"\n 開始自動下載 {len(images)} 個圖片...")
        
        success_count = 0
        failed_count = 0
        
        # 獲取漫畫標題用於文件名
        manga_title = page_info.get('manga_title', 'unknown')
        manga_title = self.clean_filename(manga_title)
        
        # 如果標題還是unknown，使用頁面標題或域名
        if manga_title == 'unknown' or not manga_title:
            page_title = page_info.get('title', '')
            if page_title and page_title != 'N/A':
                manga_title = self.clean_filename(self.clean_page_title(page_title))
            else:
                domain = urlparse(page_info.get('url', '')).netloc.replace('.', '_')
                manga_title = domain
        
        print(f" 使用標題: {manga_title}")
        
        for i, img in enumerate(images, 1):
            try:
                # 獲取圖片URL
                img_url = img.get('src') or img.get('url')
                if not img_url or not img_url.startswith(('http://', 'https://')):
                    print(f"[{i}/{len(images)}] ⚠️ 跳過無效URL: {img_url}")
                    continue
                
                print(f"\n[{i}/{len(images)}] 正在下載...")
                print(f"   URL: {img_url[:100]}...")
                
                # 下載圖片
                response = self.session.get(img_url, timeout=30)
                
                if response.status_code == 200:
                    # 檢查內容類型
                    content_type = response.headers.get('content-type', '')
                    print(f"  📋 內容類型: {content_type}")
                    print(f"  📏 文件大小: {len(response.content)} bytes")
                    
                    # 生成文件名
                    if 'image/' in content_type:
                        ext = content_type.split('/')[-1]
                    else:
                        ext = 'jpg'  # 默認擴展名
                    
                    # 生成更有意義的文件名
                    filename = self.generate_meaningful_filename(img, manga_title, i, ext)
                    filepath = os.path.join(self.output_dir, filename)
                    
                    # 保存圖片
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"  ✅ 已保存: {filename}")
                    success_count += 1
                    
                else:
                    print(f"  ❌ HTTP錯誤: {response.status_code}")
                    failed_count += 1
                
                # 延遲避免過於頻繁的請求
                if i < len(images):
                    time.sleep(self.delay)
                
            except Exception as e:
                print(f"  ❌ 下載失敗: {e}")
                failed_count += 1
        
        # 顯示下載結果
        print(f"\n✅ 自動下載完成！")
        print(f"成功: {success_count} 個")
        print(f"失敗: {failed_count} 個")
        print(f"圖片保存在: {os.path.abspath(self.output_dir)}")
    
    def generate_meaningful_filename(self, img, manga_title, index, ext):
        """生成更有意義的文件名"""
        try:
            # 構建文件名組件
            parts = []
            
            # 1. 漫畫標題（主要組件）
            if manga_title and manga_title != 'unknown':
                parts.append(manga_title)
            
            # 2. 圖片類型（更友好的描述）
            img_type = img.get('type', '')
            type_mapping = {
                'img_tag': 'img',
                'canvas': 'canvas',
                'background_image': 'bg',
                'svg': 'svg',
                'picture': 'pic',
                'js_extracted': 'js'
            }
            friendly_type = type_mapping.get(img_type, img_type)
            if friendly_type:
                parts.append(friendly_type)
            
            # 3. 圖片索引（保持3位數格式）
            parts.append(f"{index:03d}")
            
            # 4. 如果有alt文本，可以添加（限制長度）
            alt_text = img.get('alt', '')
            if alt_text and len(alt_text) < 20:
                clean_alt = self.clean_filename(alt_text)
                if clean_alt and clean_alt != 'unknown':
                    parts.append(clean_alt)
            
            # 組合文件名
            if parts:
                filename = "_".join(parts) + "." + ext
            else:
                filename = f"image_{index:03d}.{ext}"
            
            return filename
            
        except Exception as e:
            print(f"⚠️ 生成文件名時出錯: {e}")
            return f"image_{index:03d}.{ext}"
    
    def clean_filename(self, name):
        """清理文件名中的非法字符"""
        if not name:
            return "unknown"
        # 替換非法字符
        illegal_chars = r'<>:"/\|?*'
        for char in illegal_chars:
            name = name.replace(char, '_')
        # 限制長度
        if len(name) > 30:
            name = name[:30]
        return name.strip('_')
    
    def save_results(self, url, page_info, images):
        """保存爬取結果"""
        if not images:
            print("沒有找到圖片，跳過保存")
            return
        
        os.makedirs('output', exist_ok=True)
        domain = urlparse(url).netloc
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存詳細結果
        detailed_file = f"output/manga_detailed_{domain}_{timestamp}.json"
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump({
                'page_info': page_info,
                'images': images,
                'total_images': len(images)
            }, f, ensure_ascii=False, indent=2)
        
        # 保存簡化結果
        simple_file = f"output/manga_simple_{domain}_{timestamp}.txt"
        with open(simple_file, 'w', encoding='utf-8') as f:
            f.write(f"漫畫頁面圖片提取結果\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"網址: {url}\n")
            f.write(f"標題: {page_info.get('title', 'N/A')}\n")
            f.write(f"漫畫標題: {page_info.get('manga_title', 'N/A')}\n")
            f.write(f"提取時間: {page_info.get('timestamp', 'N/A')}\n")
            f.write(f"總圖片數量: {len(images)}\n\n")
            
            # 按類型統計
            type_counts = {}
            for img in images:
                img_type = img['type']
                type_counts[img_type] = type_counts.get(img_type, 0) + 1
            
            f.write("圖片類型統計:\n")
            for img_type, count in type_counts.items():
                f.write(f"  {img_type}: {count} 個\n")
            f.write("\n")
            
            # 圖片URL列表
            f.write("圖片URL列表:\n")
            f.write("-" * 30 + "\n")
            url_count = 0
            for img in images:
                if 'src' in img and img['src']:
                    url_count += 1
                    f.write(f"{url_count}. {img['src']}\n")
                elif 'url' in img and img['url']:
                    url_count += 1
                    f.write(f"{url_count}. {img['url']}\n")
            
            if url_count == 0:
                f.write("沒有找到可用的圖片URL\n")
        
        # 保存CSV文件
        csv_file = f"output/manga_images_{domain}_{timestamp}.csv"
        self.save_images_to_csv(csv_file, images, page_info)
        
        print(f"✅ 詳細結果已保存到: {detailed_file}")
        print(f"✅ 簡化結果已保存到: {simple_file}")
        print(f"✅ CSV文件已保存到: {csv_file}")
    
    def save_images_to_csv(self, csv_file, images, page_info):
        """將圖片信息保存到CSV文件"""
        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 寫入標題行
                writer.writerow([
                    'index', 'type', 'url', 'alt', 'title', 'width', 'height', 
                    'class', 'id', 'manga_title', 'page_title', 'extract_time'
                ])
                
                # 寫入圖片數據
                for i, img in enumerate(images, 1):
                    row = [
                        i,  # index
                        img.get('type', ''),  # type
                        img.get('src') or img.get('url', ''),  # url
                        img.get('alt', ''),  # alt
                        img.get('title', ''),  # title
                        img.get('width', ''),  # width
                        img.get('height', ''),  # height
                        img.get('class', ''),  # class
                        img.get('id', ''),  # id
                        page_info.get('manga_title', ''),  # manga_title
                        page_info.get('title', ''),  # page_title
                        page_info.get('timestamp', '')  # extract_time
                    ]
                    writer.writerow(row)
                    
        except Exception as e:
            print(f"⚠️ 保存CSV文件失敗: {e}")
    
    def print_summary(self, page_info, images):
        """打印爬取摘要"""
        print(f"\n✅ 漫畫頁面爬取完成！")
        print(f"標題: {page_info.get('title', 'N/A')}")
        print(f"漫畫標題: {page_info.get('manga_title', 'N/A')}")
        print(f"總共找到 {len(images)} 個圖片元素")
        
        # 按類型統計
        type_counts = {}
        for img in images:
            img_type = img['type']
            type_counts[img_type] = type_counts.get(img_type, 0) + 1
        
        print("\n圖片類型統計:")
        for img_type, count in type_counts.items():
            print(f"  {img_type}: {count} 個")
        
        # 顯示前幾個圖片
        print(f"\n前5個圖片預覽:")
        for i, img in enumerate(images[:5], 1):
            if 'src' in img and img['src']:
                print(f"  {i}. [{img['type']}] {img['src']}")
            elif 'url' in img and img['url']:
                print(f"  {i}. [{img['type']}] {img['url']}")
            else:
                print(f"  {i}. [{img['type']}] 無URL")
    
    def close(self):
        """關閉瀏覽器"""
        if self.driver:
            self.driver.quit()
            print(" 瀏覽器已關閉")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='漫畫瀏覽器爬蟲 - 整合版本，支持自動下載')
    parser.add_argument('-u', '--url', required=True, help='漫畫頁面URL')
    parser.add_argument('--headless', action='store_true', help='無頭模式（不顯示瀏覽器窗口）')
    parser.add_argument('--wait', type=int, default=5, help='等待頁面加載的時間（秒）')
    parser.add_argument('--auto-download', action='store_true', help='爬取完成後自動下載圖片')
    parser.add_argument('--output-dir', default='downloaded_images', help='圖片下載目錄')
    parser.add_argument('--delay', type=float, default=0.5, help='下載延遲時間（秒）')
    
    args = parser.parse_args()
    
    scraper = None
    try:
        scraper = MangaBrowserScraper(
            headless=args.headless, 
            wait_time=args.wait,
            auto_download=args.auto_download,
            output_dir=args.output_dir,
            delay=args.delay
        )
        
        result = scraper.scrape_manga_page(args.url)
        
        if result:
            scraper.print_summary(result['page_info'], result['images'])
            
            if args.auto_download:
                print(f"\n 圖片已自動下載到: {os.path.abspath(args.output_dir)}")
            else:
                print(f"\n📁 圖片信息已保存到CSV文件，可使用 download_form_csv.py 進行下載")
        else:
            print("❌ 爬取失敗")
            
    except KeyboardInterrupt:
        print("\n⚠️ 用戶中斷操作")
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()
