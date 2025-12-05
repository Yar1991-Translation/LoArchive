"""
Lofter Spider Web Application
一个现代化的 Lofter 爬虫 Web 界面
"""

import os
import sys
import json
import time
import threading
import queue
import re
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# 全局状态
task_status = {
    'running': False,
    'current_task': None,
    'progress': 0,
    'message': '',
    'logs': [],
    'error': None
}

# 配置信息
config = {
    'login_key': 'LOFTER-PHONE-LOGIN-AUTH',
    'login_auth': '',
    'file_path': './dir',
    'save_path': './dir',  # 用户自定义保存路径
    'dark_mode': False,
    'auto_dedup': True,  # 自动去重
    'notify_on_complete': True  # 完成通知
}

# 下载历史文件路径
HISTORY_FILE = './download_history.json'
# 配置文件路径
CONFIG_FILE = './loarchive_config.json'

def load_config_file():
    """从文件加载配置"""
    global config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                config.update(saved_config)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    return config

def save_config_file():
    """保存配置到文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置文件失败: {e}")

def load_download_history():
    """加载下载历史"""
    default_history = {'items': [], 'stats': {'total': 0, 'images': 0, 'articles': 0}}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 确保数据结构完整
                if 'items' not in data:
                    data['items'] = []
                if 'stats' not in data:
                    data['stats'] = {'total': 0, 'images': 0, 'articles': 0}
                return data
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            return default_history
    return default_history

def save_download_history(history):
    """保存下载历史"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存历史记录失败: {e}")

def add_to_history(item_type, url, title, author, file_path, source='lofter'):
    """添加到下载历史"""
    history = load_download_history()
    
    # 检查是否已存在（去重）
    for item in history['items']:
        if item.get('url') == url:
            return False  # 已存在
    
    # 添加新记录
    record = {
        'id': str(int(time.time() * 1000)),
        'type': item_type,  # 'image', 'article', 'ao3'
        'url': url,
        'title': title,
        'author': author,
        'file_path': file_path,
        'source': source,
        'download_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'timestamp': int(time.time())
    }
    
    history['items'].insert(0, record)  # 最新的在前面
    
    # 更新统计
    history['stats']['total'] += 1
    if item_type == 'image':
        history['stats']['images'] += 1
    else:
        history['stats']['articles'] += 1
    
    # 限制历史记录数量（保留最近1000条）
    if len(history['items']) > 1000:
        history['items'] = history['items'][:1000]
    
    save_download_history(history)
    return True

def is_url_downloaded(url):
    """检查URL是否已下载过"""
    if not config.get('auto_dedup', True):
        return False
    history = load_download_history()
    for item in history['items']:
        if item.get('url') == url:
            return True
    return False

def clear_download_history():
    """清空下载历史"""
    history = {'items': [], 'stats': {'total': 0, 'images': 0, 'articles': 0}}
    save_download_history(history)
    return True

def load_config():
    """加载配置"""
    global config
    # 首先从配置文件加载
    load_config_file()
    # 然后尝试从 login_info.py 加载（如果存在）
    try:
        from login_info import login_auth, login_key
        config['login_key'] = login_key
        config['login_auth'] = login_auth
    except:
        pass
    return config

def save_login_info(login_key, login_auth):
    """保存登录信息到 login_info.py"""
    content = f'''message = """
这个文件是专门填登录信息的，lofter某次更新之后很多页面都要登录才能看，所以每个程序都要有登录信息才能用
在这里填好可以同步到每个程序
反正就是不填这里其他的都跑不起来
"""

# 登录方式对应的key，这里默认是手机登录
login_key = "{login_key}"

# 授权码
login_auth = "{login_auth}"
'''
    with open('login_info.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    config['login_key'] = login_key
    config['login_auth'] = login_auth
    
    # 重新导入以更新模块
    import importlib
    try:
        import login_info
        importlib.reload(login_info)
    except:
        pass

def add_log(message):
    """添加日志"""
    timestamp = time.strftime('%H:%M:%S')
    log_entry = f'[{timestamp}] {message}'
    task_status['logs'].append(log_entry)
    task_status['message'] = message
    print(log_entry)  # 同时打印到控制台
    # 保留最新的200条日志
    if len(task_status['logs']) > 200:
        task_status['logs'] = task_status['logs'][-200:]

def run_spider_task(task_type, params):
    """运行爬虫任务"""
    global task_status
    task_status['running'] = True
    task_status['current_task'] = task_type
    task_status['progress'] = 0
    task_status['logs'] = []
    task_status['error'] = None
    
    try:
        load_config()  # 重新加载配置
        
        # AO3 不需要登录，其他任务需要
        if task_type == 'ao3':
            run_ao3_task(params)
        elif not config['login_auth']:
            raise Exception("请先在设置中配置登录授权码！")
        elif task_type == 'single_img':
            run_single_img_task(params)
        elif task_type == 'single_txt':
            run_single_txt_task(params)
        elif task_type == 'author_img':
            run_author_img_task(params)
        elif task_type == 'author_txt':
            run_author_txt_task(params)
        elif task_type == 'like_share_tag':
            run_like_share_tag_task(params)
        else:
            add_log(f'❌ 未知的任务类型: {task_type}')
            
    except Exception as e:
        import traceback
        error_msg = str(e)
        task_status['error'] = error_msg
        add_log(f'❌ 任务出错: {error_msg}')
        add_log(traceback.format_exc())
    finally:
        task_status['running'] = False
        task_status['progress'] = 100
        add_log('✅ 任务结束')


def run_single_img_task(params):
    """运行单篇图片爬取任务 - 真正调用 l8_blogs_img.py"""
    import useragentutil
    from lxml.html import etree
    import l4_author_img
    from l13_like_share_tag import filename_check
    
    urls = params.get('urls', [])
    if not urls:
        add_log('❌ 没有提供链接')
        return
    
    add_log(f"🚀 开始单篇图片爬取，共 {len(urls)} 个链接")
    
    login_key = config['login_key']
    login_auth = config['login_auth']
    
    # 确保目录存在
    save_root = config.get('save_path', './dir')
    dir_path = os.path.join(save_root, "img/this")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    all_imgs_info = []
    
    # 解析每个博客
    for idx, blog_url in enumerate(urls):
        blog_url = blog_url.strip()
        if not blog_url:
            continue
            
        task_status['progress'] = int((idx / len(urls)) * 50)
        add_log(f"📖 [{idx+1}/{len(urls)}] 解析博客: {blog_url}")
        
        try:
            # 获取博客页面
            content = requests.get(blog_url, headers=useragentutil.get_headers(),
                                   cookies={login_key: login_auth}).content.decode("utf-8")
            
            # 获取作者信息
            author_view_url = blog_url.split("/post")[0] + "/view"
            author_view_html = requests.get(author_view_url, headers=useragentutil.get_headers(),
                                            cookies={login_key: login_auth}).content.decode("utf-8")
            author_view_parse = etree.HTML(author_view_html)
            
            try:
                author_name = author_view_parse.xpath("//h1/a/text()")[0]
            except:
                author_name = "未知作者"
            
            author_ip = re.search(r"http(s)*://(.*).lofter.com/", blog_url).group(2)
            
            # 获取发表时间
            re_date = re.search(r"\d{4}[.\\\/-]\d{2}[.\\\/-]\d{2}", content)
            if re_date:
                public_time = re_date.group(0).replace("\\", "-").replace(".", "-").replace("/", "-")
            else:
                public_time = time.strftime("%Y-%m-%d")
            
            # 匹配图片链接
            imgs_url = re.findall(r'"(http[s]{0,1}://imglf\d{0,1}.lf\d*.[0-9]{0,3}.net.*?)"', content)
            
            # 过滤图片
            filtered_imgs = []
            for img_url in imgs_url:
                if "&amp;" in img_url:
                    continue
                re_url = re.search(r"[1649]{2}[x,y][1649]{2}", img_url)
                if re_url:
                    continue
                img_url = img_url.split("imageView")[0]
                if img_url not in filtered_imgs:
                    filtered_imgs.append(img_url)
            
            add_log(f"   找到 {len(filtered_imgs)} 张图片")
            
            # 整理图片信息
            for img_idx, img_url in enumerate(filtered_imgs):
                is_gif = "gif" in img_url
                is_png = "png" in img_url
                if is_gif:
                    img_type = "gif"
                elif is_png:
                    img_type = "png"
                else:
                    img_type = "jpg"
                
                author_name_safe = author_name.replace("/", "&").replace("|", "&").replace("\\", "&").\
                    replace("<", "《").replace(">", "》").replace(":", "：").replace('"', '"').replace("?", "？").\
                    replace("*", "·").replace("\n", "").replace("(", "（").replace(")", "）")
                
                pic_name = f"{author_name_safe}[{author_ip}] {public_time}({img_idx+1}).{img_type}"
                all_imgs_info.append({
                    "img_url": img_url,
                    "pic_name": pic_name,
                    "referer": blog_url.split("post")[0]
                })
                
        except Exception as e:
            add_log(f"   ⚠️ 解析失败: {str(e)}")
            continue
    
    add_log(f"📷 共获取到 {len(all_imgs_info)} 张图片，开始下载...")
    
    # 下载图片
    for idx, img_info in enumerate(all_imgs_info):
        task_status['progress'] = 50 + int((idx / len(all_imgs_info)) * 50)
        
        pic_url = img_info["img_url"]
        pic_name = img_info["pic_name"]
        img_path = os.path.join(dir_path, pic_name)
        
        try:
            headers = useragentutil.get_headers()
            headers["Referer"] = img_info.get("referer", "")
            
            response = requests.get(pic_url, headers=headers, timeout=30)
            with open(img_path, "wb") as f:
                f.write(response.content)
            
            add_log(f"   💾 [{idx+1}/{len(all_imgs_info)}] 已保存: {pic_name}")
            
        except Exception as e:
            add_log(f"   ⚠️ 下载失败: {pic_name} - {str(e)}")
        
        if idx % 5 == 0:
            time.sleep(0.5)  # 防止请求过快
    
    add_log(f"✅ 图片保存完成！共保存 {len(all_imgs_info)} 张图片到 {dir_path}")


def run_single_txt_task(params):
    """运行单篇文章爬取任务 - 真正调用 l10_blogs_txt.py"""
    import useragentutil
    from lxml.html import etree
    import l4_author_img
    from l13_like_share_tag import filename_check
    import html2text
    
    urls = params.get('urls', [])
    if not urls:
        add_log('❌ 没有提供链接')
        return
    
    add_log(f"🚀 开始单篇文章爬取，共 {len(urls)} 个链接")
    
    login_key = config['login_key']
    login_auth = config['login_auth']
    
    # 确保目录存在
    save_root = config.get('save_path', './dir')
    dir_path = os.path.join(save_root, "article/this")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    saved_count = 0
    
    for idx, blog_url in enumerate(urls):
        blog_url = blog_url.strip()
        if not blog_url:
            continue
            
        task_status['progress'] = int((idx / len(urls)) * 100)
        add_log(f"📖 [{idx+1}/{len(urls)}] 解析博客: {blog_url}")
        
        try:
            # 获取博客页面
            blog_html = requests.get(blog_url, headers=useragentutil.get_headers(),
                                     cookies={login_key: login_auth}).content.decode("utf-8")
            blog_parse = etree.HTML(blog_html)
            
            # 获取作者信息
            author_view_url = blog_url.split("/post")[0] + "/view"
            author_view_html = requests.get(author_view_url, headers=useragentutil.get_headers(),
                                            cookies={login_key: login_auth}).content.decode("utf-8")
            author_view_parse = etree.HTML(author_view_html)
            
            try:
                author_name = author_view_parse.xpath("//h1/a/text()")[0]
            except:
                author_name = "未知作者"
            
            author_ip = re.search(r"http(s)*://(.*).lofter.com/", blog_url).group(2)
            
            # 获取发表时间
            re_date = re.search(r"\d{4}[.\\\/-]\d{2}[.\\\/-]\d{2}", blog_html)
            if re_date:
                public_time = re_date.group(0).replace("\\", "-").replace(".", "-").replace("/", "-")
            else:
                public_time = time.strftime("%Y-%m-%d")
            
            # 获取标题
            title_path = blog_parse.xpath("//h2//text()")
            if title_path:
                title = title_path[0].strip()
            else:
                title = ""
            
            # 获取正文内容
            # 尝试多种方式获取正文
            content_text = ""
            
            # 方法1: 尝试获取文章主体
            content_elements = blog_parse.xpath("//div[contains(@class,'content')]//text()")
            if content_elements:
                content_text = "\n".join([t.strip() for t in content_elements if t.strip()])
            
            # 方法2: 如果方法1失败，尝试获取所有p标签
            if not content_text:
                p_elements = blog_parse.xpath("//article//p//text() | //div[@class='text']//p//text()")
                if p_elements:
                    content_text = "\n\n".join([t.strip() for t in p_elements if t.strip()])
            
            # 方法3: 使用html2text转换
            if not content_text:
                try:
                    h = html2text.HTML2Text()
                    h.ignore_links = True
                    h.ignore_images = True
                    content_text = h.handle(blog_html)
                    # 清理一些无用内容
                    content_text = re.sub(r'\n{3,}', '\n\n', content_text)
                except:
                    content_text = "无法解析正文内容"
            
            # 构建文章
            article_head = f"{title if title else '无标题'} by {author_name}[{author_ip}]\n发表时间：{public_time}\n原文链接：{blog_url}"
            article = article_head + "\n\n" + "="*50 + "\n\n" + content_text
            
            # 生成文件名
            if title:
                file_name = f"{title} by {author_name}.txt"
            else:
                file_name = f"{author_name} {public_time}.txt"
            
            # 清理文件名中的非法字符
            file_name = file_name.replace("/", "&").replace("|", "&").replace("\\", "&").\
                replace("<", "《").replace(">", "》").replace(":", "：").replace('"', '"').\
                replace("?", "？").replace("*", "·").replace("\n", "").replace("(", "（").replace(")", "）")
            
            # 保存文件
            file_path = os.path.join(dir_path, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(article)
            
            saved_count += 1
            add_log(f"   💾 已保存: {file_name}")
            
        except Exception as e:
            add_log(f"   ⚠️ 保存失败: {str(e)}")
            continue
        
        time.sleep(0.5)  # 防止请求过快
    
    add_log(f"✅ 文章保存完成！共保存 {saved_count} 篇文章到 {dir_path}")


def run_author_img_task(params):
    """运行作者图片爬取任务"""
    add_log(f"🚀 开始爬取作者图片")
    author_url = params.get('author_url', '')
    
    if not author_url:
        add_log('❌ 请提供作者主页链接')
        return
    
    if not author_url.endswith('/'):
        author_url += '/'
    
    add_log(f"📍 作者主页: {author_url}")
    
    try:
        import l4_author_img
        import useragentutil
        from lxml.html import etree
        
        login_key = config['login_key']
        login_auth = config['login_auth']
        
        # 获取作者信息
        author_view_url = author_url + "view"
        author_view_html = requests.get(author_view_url, headers=useragentutil.get_headers(),
                                        cookies={login_key: login_auth}).content.decode("utf-8")
        author_page_parse = etree.HTML(author_view_html)
        
        try:
            author_id = author_page_parse.xpath("//body//iframe[@id='control_frame']/@src")[0].split("blogId=")[1]
            author_name = author_page_parse.xpath("//title//text()")[0]
            author_ip = re.search(r"http[s]*://(.*).lofter.com/", author_url).group(1)
            add_log(f"👤 作者: {author_name} ({author_ip})")
        except Exception as e:
            add_log(f"❌ 无法获取作者信息: {str(e)}")
            return
        
        # 获取归档页
        archive_url = author_url + "dwr/call/plaincall/ArchiveBean.getArchivePostByTime.dwr"
        add_log(f"📚 正在获取归档页...")
        
        query_num = 50
        data = l4_author_img.make_data(author_id, query_num)
        header = l4_author_img.make_head(author_url)
        
        all_blog_info = []
        page_num = 0
        
        while True:
            page_num += 1
            add_log(f"   获取第 {page_num} 页...")
            task_status['progress'] = min(30, page_num * 5)
            
            page_data = l4_author_img.post_content(
                url=archive_url, data=data, head=header,
                cookies_dict={login_key: login_auth}
            )
            
            new_blogs_info = re.findall(r"s[\d]*.blogId.*\n.*noticeLinkTitle", page_data)
            all_blog_info += new_blogs_info
            
            if len(new_blogs_info) < query_num:
                break
            
            try:
                data['c0-param2'] = 'number:' + str(
                    re.search(r's%d\.time=(.*);s.*type' % (query_num - 1), page_data).group(1))
            except:
                break
            
            time.sleep(0.5)
        
        add_log(f"📊 共获取 {len(all_blog_info)} 条博客记录")
        
        # 解析博客信息，获取图片博客
        img_blogs = []
        for blog_info in all_blog_info:
            try:
                img_url_match = re.findall(r'[\d]*.imgurl="(.*?)"', blog_info)
                if img_url_match:
                    blog_index = re.search(r's[\d]*.permalink="(.*)"', blog_info).group(1)
                    blog_url = author_url + "post/" + blog_index
                    timestamp = re.search(r's[\d]*.time=(\d*);', blog_info).group(1)
                    dt_time = time.strftime("%Y-%m-%d", time.localtime(int(int(timestamp) / 1000)))
                    img_blogs.append({"url": blog_url, "time": dt_time})
            except:
                continue
        
        add_log(f"🖼️ 共找到 {len(img_blogs)} 篇图片博客")
        
        if not img_blogs:
            add_log("⚠️ 没有找到图片博客")
            return
        
        # 创建保存目录
        author_name_safe = author_name.replace("/", "&").replace("|", "&").replace("\\", "&").\
            replace("<", "《").replace(">", "》").replace(":", "：").replace('"', '"').\
            replace("?", "？").replace("*", "·").replace("\n", "")
        save_root = config.get('save_path', './dir')
        dir_path = os.path.join(save_root, f"img/{author_name_safe}[{author_ip}]")
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        # 下载图片
        total_saved = 0
        for idx, blog in enumerate(img_blogs):
            task_status['progress'] = 30 + int((idx / len(img_blogs)) * 70)
            
            try:
                blog_html = requests.get(blog["url"], headers=useragentutil.get_headers(),
                                         cookies={login_key: login_auth}).content.decode("utf-8")
                
                imgs_url = re.findall(r'"(http[s]{0,1}://imglf\d{0,1}.lf\d*.[0-9]{0,3}.net.*?)"', blog_html)
                
                # 过滤
                filtered_imgs = []
                for img_url in imgs_url:
                    if "&amp;" in img_url:
                        continue
                    re_url = re.search(r"[1649]{2}[x,y][1649]{2}", img_url)
                    if re_url:
                        continue
                    img_url = img_url.split("imageView")[0]
                    if img_url not in filtered_imgs:
                        filtered_imgs.append(img_url)
                
                for img_idx, img_url in enumerate(filtered_imgs):
                    is_gif = "gif" in img_url
                    is_png = "png" in img_url
                    img_type = "gif" if is_gif else ("png" if is_png else "jpg")
                    
                    pic_name = f"{author_name_safe}[{author_ip}] {blog['time']}({img_idx+1}).{img_type}"
                    img_path = os.path.join(dir_path, pic_name)
                    
                    headers = useragentutil.get_headers()
                    headers["Referer"] = author_url
                    
                    img_content = requests.get(img_url, headers=headers, timeout=30).content
                    with open(img_path, "wb") as f:
                        f.write(img_content)
                    
                    total_saved += 1
                
                if idx % 10 == 0:
                    add_log(f"   📥 进度: {idx+1}/{len(img_blogs)} 博客, 已保存 {total_saved} 张图片")
                    
            except Exception as e:
                add_log(f"   ⚠️ 处理博客失败: {blog['url']} - {str(e)}")
                continue
            
            time.sleep(0.3)
        
        add_log(f"✅ 完成！共保存 {total_saved} 张图片到 {dir_path}")
        
    except Exception as e:
        import traceback
        add_log(f"❌ 爬取失败: {str(e)}")
        add_log(traceback.format_exc())


def run_author_txt_task(params):
    """运行作者文章爬取任务"""
    add_log(f"🚀 开始爬取作者文章")
    add_log("⚠️ 此功能暂未完全实现，请使用单篇保存功能")
    # TODO: 完整实现


def run_like_share_tag_task(params):
    """运行喜欢/推荐/Tag爬取任务"""
    import useragentutil
    from lxml.html import etree
    from urllib import parse as url_parse
    import html2text
    
    url = params.get('url', '')
    mode = params.get('mode', 'like2')  # like1, like2, share, tag
    save_mode = params.get('save_mode', {"article": 1, "text": 1, "long article": 1, "img": 1})
    export_pdf = params.get('export_pdf', False)  # 是否导出PDF
    
    # Lofter文章PDF生成函数
    def generate_lofter_pdf(title, author, author_ip, public_time, url, content, pdf_path):
        """为Lofter文章生成PDF"""
        try:
            from xhtml2pdf import pisa
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            import datetime
            
            # 注册中文字体
            try:
                pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            except:
                pass
            
            # 处理内容中的换行
            content_html = content.replace('\n', '<br/>')
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title} - {author}</title>
    <style>
        @page {{ 
            size: A4; 
            margin: 2.5cm 2cm; 
            @bottom-center {{
                content: counter(page);
                font-size: 10pt;
                color: #666;
            }}
        }}
        
        body {{ font-family: STSong-Light, SimSun, serif; font-size: 12pt; line-height: 1.8; color: #333; }}
        
        /* 封面样式 */
        .cover {{
            text-align: center;
            padding-top: 20%;
            page-break-after: always;
            height: 100%;
        }}
        
        .cover-title {{
            font-size: 28pt;
            font-weight: bold;
            margin-bottom: 30px;
            color: #2c3e50;
        }}
        
        .cover-author {{
            font-size: 16pt;
            margin-bottom: 60px;
            color: #555;
        }}
        
        .cover-meta {{
            font-size: 11pt;
            color: #7f8c8d;
            margin-top: 100px;
            border-top: 1px solid #ddd;
            padding-top: 30px;
            width: 60%;
            margin-left: auto;
            margin-right: auto;
        }}
        
        /* 正文内容 */
        .content-title {{
            font-size: 18pt;
            font-weight: bold;
            text-align: center;
            margin-bottom: 10px;
            padding-top: 30px;
        }}
        
        .content-meta {{
            font-size: 10pt;
            color: #999;
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 1px solid #eee;
            padding-bottom: 20px;
        }}
        
        .content {{ text-align: justify; }}
        .content p {{ text-indent: 2em; margin-bottom: 10px; }}
        
        a {{ color: #3498db; text-decoration: none; }}
    </style>
</head>
<body>
    <!-- 封面 -->
    <div class="cover">
        <div class="cover-title">{title or "无标题"}</div>
        <div class="cover-author">By {author}</div>
        
        <div class="cover-meta">
            <div>Published: {public_time}</div>
            <div>Source: Lofter</div>
            <div style="margin-top: 20px; font-size: 10pt;">
                Generated on {current_date}
            </div>
        </div>
    </div>

    <!-- 正文 -->
    <div class="content-title">{title or "无标题"}</div>
    <div class="content-meta">
        作者: {author} [{author_ip}] &nbsp;|&nbsp; 时间: {public_time}<br/>
        原文: {url}
    </div>
    
    <div class="content">
        <p>{content_html}</p>
    </div>
</body>
</html>'''
            
            with open(pdf_path, 'wb') as pdf_file:
                pisa.CreatePDF(html_content.encode('utf-8'), dest=pdf_file, encoding='utf-8')
            return True
        except Exception as e:
            return False
    
    if not url:
        add_log('❌ 请提供链接地址')
        return
    
    add_log(f"🚀 开始 {mode} 模式爬取任务")
    add_log(f"📍 URL: {url}")
    
    login_key = config['login_key']
    login_auth = config['login_auth']
    
    try:
        # 获取登录session
        add_log("🔐 正在建立登录会话...")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Host": "www.lofter.com",
        }
        
        session = requests.session()
        session.headers = headers
        session.cookies.set(login_key, login_auth)
        
        # 根据模式确定请求URL和参数
        if mode == "like2":
            requests_url = "http://www.lofter.com/dwr/call/plaincall/PostBean.getFavTrackItem.dwr"
            headers["Referer"] = "http://www.lofter.com/like"
        elif mode == "like1":
            requests_url = "https://www.lofter.com/dwr/call/plaincall/BlogBean.queryLikePosts.dwr"
            userName = re.search(r"http[s]{0,1}://(.*?).lofter.com/", url).group(1)
            headers["Referer"] = "https://www.lofter.com/favblog/" + userName
        elif mode == "share":
            requests_url = "https://www.lofter.com/dwr/call/plaincall/BlogBean.querySharePosts.dwr"
            userName = re.search(r"http[s]{0,1}://(.*?).lofter.com/", url).group(1)
            headers["Referer"] = "https://www.lofter.com/shareblog/" + userName
        elif mode == "tag":
            requests_url = "http://www.lofter.com/dwr/call/plaincall/TagBean.search.dwr"
            headers["Referer"] = url
        else:
            add_log(f"❌ 不支持的模式: {mode}")
            return
        
        session.headers = headers
        
        # 获取用户ID (like1, share 模式需要)
        userId = ""
        if mode in ["like1", "share"]:
            add_log("📖 获取用户信息...")
            host = re.search(r"https://(.*?)/", url).group(1)
            session.headers["Host"] = host
            user_page = session.get(url).content.decode("utf-8")
            user_page_parse = etree.HTML(user_page)
            try:
                userId = user_page_parse.xpath("//body/iframe[@id='control_frame']/@src")[0].split("blogId=")[1]
                add_log(f"   用户ID: {userId}")
            except:
                add_log("❌ 无法获取用户ID，请检查链接是否正确")
                return
            session.headers["Host"] = "www.lofter.com"
        
        # 构建初始请求参数
        base_data = {
            'callCount': '1',
            'httpSessionId': '',
            'scriptSessionId': '${scriptSessionId}187',
            'c0-id': '0',
            "batchId": "472351"
        }
        
        get_num = 100
        got_num = 0
        
        if mode in ["like1", "share"]:
            data_params = {
                'c0-scriptName': 'BlogBean',
                "c0-methodName": "queryLikePosts" if mode == "like1" else "querySharePosts",
                'c0-param0': 'number:' + str(userId),
                'c0-param1': 'number:' + str(get_num),
                'c0-param2': 'number:' + str(got_num),
                'c0-param3': 'string:'
            }
        elif mode == "like2":
            data_params = {
                "c0-scriptName": "PostBean",
                "c0-methodName": "getFavTrackItem",
                "c0-param0": "number:" + str(get_num),
                "c0-param1": "number:" + str(got_num),
            }
        elif mode == "tag":
            url_search = re.search(r"http[s]{0,1}://www.lofter.com/tag/(.*?)/(.*)", url)
            if url_search:
                tag_name = url_search.group(1)
                tag_type = url_search.group(2) if url_search.group(2) else "new"
            else:
                url_search = re.search(r"http[s]{0,1}://www.lofter.com/tag/(.*)", url)
                tag_name = url_search.group(1) if url_search else ""
                tag_type = "new"
            
            data_params = {
                'c0-scriptName': 'TagBean',
                'c0-methodName': 'search',
                'c0-param0': 'string:' + tag_name,
                'c0-param1': 'number:0',
                'c0-param2': 'string:',
                'c0-param3': 'string:' + tag_type,
                'c0-param4': 'boolean:false',
                'c0-param5': 'number:0',
                'c0-param6': 'number:' + str(get_num),
                'c0-param7': 'number:' + str(got_num),
                'c0-param8': 'number:' + str(int(time.time() * 1000)),
                'batchId': '870178'
            }
        
        data = {**base_data, **data_params}
        
        # 开始获取数据
        add_log("📥 开始获取数据...")
        all_fav_info = []
        real_got_num = 0
        
        while True:
            add_log(f"   请求 {got_num}-{got_num + get_num}...")
            task_status['progress'] = min(30, int(got_num / 10))
            
            response = session.post(requests_url, data=data)
            content = response.content.decode("utf-8")
            
            # 按 activityTags 切分
            new_info = content.split("activityTags")[1:]
            all_fav_info += new_info
            got_num += get_num
            real_got_num += len(new_info)
            
            add_log(f"   实际返回 {len(new_info)} 条")
            
            if len(new_info) == 0:
                add_log("   已到达最后一页")
                break
            
            if got_num >= 500:  # 限制获取数量，避免太慢
                add_log("   已达到500条限制")
                break
            
            # 更新请求参数
            if mode in ["like1", "share"]:
                data["c0-param1"] = 'number:' + str(get_num)
                data["c0-param2"] = 'number:' + str(got_num)
            elif mode == "like2":
                data["c0-param0"] = 'number:' + str(get_num)
                data["c0-param1"] = 'number:' + str(got_num)
            elif mode == "tag":
                try:
                    last_info = new_info[-1]
                    last_timestamp = re.search(r's\d{1,5}.publishTime=(.*?);', last_info).group(1)
                    data["c0-param6"] = 'number:' + str(get_num)
                    data["c0-param7"] = 'number:' + str(got_num)
                    data["c0-param8"] = 'number:' + str(last_timestamp)
                except:
                    break
            
            time.sleep(0.5)
        
        add_log(f"📊 共获取到 {real_got_num} 条博客信息")
        
        if real_got_num == 0:
            add_log("⚠️ 没有获取到任何数据，请检查登录信息和链接")
            return
        
        # 解析博客信息
        add_log("🔄 正在解析博客信息...")
        blogs_info = []
        
        for idx, fav_info in enumerate(all_fav_info):
            try:
                # 博客链接
                blog_url = re.search(r's\d{1,5}.blogPageUrl="(.*?)"', fav_info)
                if not blog_url:
                    continue
                blog_url = blog_url.group(1)
                
                # 作者名
                author_name_search = re.search(r's\d{1,5}.blogNickName="(.*?)"', fav_info)
                if author_name_search:
                    author_name = author_name_search.group(1).encode('latin-1').decode('unicode_escape', errors="replace")
                else:
                    author_name = "未知作者"
                
                # 作者IP
                author_ip = re.search(r"http[s]{0,1}://(.*?).lofter.com", blog_url).group(1)
                
                # 发表时间
                public_timestamp = re.search(r's\d{1,5}.publishTime=(.*?);', fav_info)
                if public_timestamp:
                    time_local = time.localtime(int(int(public_timestamp.group(1)) / 1000))
                    public_time = time.strftime("%Y-%m-%d", time_local)
                else:
                    public_time = "未知时间"
                
                # 图片链接
                img_urls = []
                urls_search = re.search(r'originPhotoLinks="(\[.*?\])"', fav_info)
                if urls_search:
                    try:
                        urls_str = urls_search.group(1).replace("\\", "").replace("false", "False").replace("true", "True")
                        urls_infos = eval(urls_str)
                        for url_info in urls_infos:
                            img_url = url_info.get("raw", "") or url_info.get("orign", "").split("?imageView")[0]
                            if img_url:
                                img_urls.append(img_url)
                    except:
                        pass
                
                # 正文内容
                content_search = re.search(r's\d{1,5}.content="(.*?)";', fav_info)
                if content_search:
                    content = content_search.group(1).encode('latin-1').decode("unicode_escape", errors="ignore")
                    try:
                        h = html2text.HTML2Text()
                        h.ignore_links = False
                        content = h.handle(content)
                    except:
                        pass
                else:
                    content = ""
                
                # 标题
                title_search = re.search(r's\d{1,5}.title="(.*?)"', fav_info)
                title = ""
                if title_search:
                    title = title_search.group(1).encode('latin-1').decode('unicode_escape', errors="ignore")
                
                blogs_info.append({
                    "url": blog_url,
                    "author_name": author_name,
                    "author_ip": author_ip,
                    "public_time": public_time,
                    "img_urls": img_urls,
                    "content": content,
                    "title": title,
                    "has_img": len(img_urls) > 0
                })
                
            except Exception as e:
                continue
        
        add_log(f"✅ 解析完成，共 {len(blogs_info)} 条有效博客")
        
        # 保存内容
        img_count = sum(1 for b in blogs_info if b["has_img"])
        txt_count = sum(1 for b in blogs_info if not b["has_img"])
        add_log(f"📊 图片博客: {img_count} 篇, 文字博客: {txt_count} 篇")
        
        # 创建保存目录 - 按作者分类
        save_root = config.get('save_path', './dir')
        base_dir = os.path.join(save_root, f"{mode}_save")
        img_base_dir = os.path.join(base_dir, "img")
        txt_base_dir = os.path.join(base_dir, "txt")
        os.makedirs(img_base_dir, exist_ok=True)
        os.makedirs(txt_base_dir, exist_ok=True)
        
        saved_img = 0
        saved_txt = 0
        
        # 用于安全化文件名的函数
        def safe_name(name):
            return name.replace("/", "&").replace("\\", "&").replace(":", "：").\
                replace("*", "·").replace("?", "？").replace('"', "'").\
                replace("<", "《").replace(">", "》").replace("|", "&").\
                replace("\n", "").replace("\r", "").replace("\t", " ").strip()
        
        for idx, blog in enumerate(blogs_info):
            task_status['progress'] = 30 + int((idx / len(blogs_info)) * 70)
            
            try:
                # 生成作者目录名
                author_safe = safe_name(blog["author_name"])
                author_folder = f"{author_safe}[{blog['author_ip']}]"
                
                # 保存图片 - 按作者分类
                if blog["has_img"] and save_mode.get("img"):
                    # 创建作者专属图片目录
                    author_img_dir = os.path.join(img_base_dir, author_folder)
                    os.makedirs(author_img_dir, exist_ok=True)
                    
                    for img_idx, img_url in enumerate(blog["img_urls"]):
                        try:
                            # 确定图片类型
                            img_type = "gif" if "gif" in img_url else ("png" if "png" in img_url else "jpg")
                            
                            pic_name = f"{blog['public_time']}({img_idx+1}).{img_type}"
                            img_path = os.path.join(author_img_dir, pic_name)
                            
                            headers = useragentutil.get_headers()
                            headers["Referer"] = blog["url"].split("post")[0]
                            
                            img_content = requests.get(img_url, headers=headers, timeout=30).content
                            with open(img_path, "wb") as f:
                                f.write(img_content)
                            
                            saved_img += 1
                        except:
                            continue
                
                # 保存文章/文本 - 按作者分类
                if (blog["title"] and save_mode.get("article")) or (not blog["title"] and save_mode.get("text")):
                    # 创建作者专属文章目录
                    author_txt_dir = os.path.join(txt_base_dir, author_folder)
                    os.makedirs(author_txt_dir, exist_ok=True)
                    
                    if blog["title"]:
                        title_safe = safe_name(blog["title"])
                        file_name = f"{title_safe}.txt"
                    else:
                        file_name = f"{blog['public_time']}.txt"
                    
                    txt_path = os.path.join(author_txt_dir, file_name)
                    
                    # 避免文件名重复
                    counter = 1
                    original_path = txt_path
                    while os.path.exists(txt_path):
                        name_part = original_path.rsplit('.', 1)[0]
                        txt_path = f"{name_part}({counter}).txt"
                        counter += 1
                    
                    article_head = f"{blog['title'] or '无标题'} by {blog['author_name']}[{blog['author_ip']}]\n"
                    article_head += f"发表时间：{blog['public_time']}\n原文链接：{blog['url']}\n"
                    article_head += "=" * 50 + "\n\n"
                    
                    article = article_head + blog["content"]
                    
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(article)
                    
                    # 如果需要生成PDF
                    if export_pdf:
                        pdf_path = txt_path.replace('.txt', '.pdf')
                        generate_lofter_pdf(
                            title=blog['title'] or '无标题',
                            author=blog['author_name'],
                            author_ip=blog['author_ip'],
                            public_time=blog['public_time'],
                            url=blog['url'],
                            content=blog['content'],
                            pdf_path=pdf_path
                        )
                    
                    saved_txt += 1
                
                if idx % 20 == 0:
                    add_log(f"   进度: {idx+1}/{len(blogs_info)}, 已保存图片 {saved_img} 张, 文章 {saved_txt} 篇")
                    
            except Exception as e:
                continue
            
            time.sleep(0.1)
        
        add_log(f"✅ 保存完成！（文件按作者分类存放）")
        add_log(f"   📷 图片: {saved_img} 张 → {img_base_dir}/作者名/")
        add_log(f"   📝 文章: {saved_txt} 篇 → {txt_base_dir}/作者名/")
        
    except Exception as e:
        import traceback
        add_log(f"❌ 爬取失败: {str(e)}")
        add_log(traceback.format_exc())


def generate_epub(title, author, content_parts, chapters_info, metadata_list, filepath):
    """生成 EPUB 电子书"""
    try:
        from ebooklib import epub
        import uuid
        
        book = epub.EpubBook()
        
        # 设置元数据
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(title)
        book.set_language('zh')
        book.add_author(author)
        
        # 添加 CSS 样式
        style = '''
        body { font-family: "Noto Serif SC", "Source Han Serif", serif; line-height: 1.8; margin: 2em; }
        h1 { text-align: center; margin-bottom: 1em; }
        h2 { border-bottom: 1px solid #ccc; padding-bottom: 0.5em; margin-top: 2em; }
        p { text-indent: 2em; margin-bottom: 0.5em; }
        .meta { font-size: 0.9em; color: #666; margin-bottom: 2em; padding: 1em; background: #f5f5f5; border-radius: 5px; }
        .meta-item { margin-bottom: 0.3em; }
        '''
        css = epub.EpubItem(uid="style", file_name="style/main.css", media_type="text/css", content=style)
        book.add_item(css)
        
        chapters = []
        
        # 封面/元数据页
        if metadata_list:
            cover_content = f'<html><head><link rel="stylesheet" href="style/main.css"/></head><body>'
            cover_content += f'<h1>{title}</h1>'
            cover_content += f'<p style="text-align:center;">by {author}</p>'
            cover_content += '<div class="meta">'
            for meta in metadata_list:
                if meta.strip():
                    cover_content += f'<div class="meta-item">{meta}</div>'
            cover_content += '</div></body></html>'
            
            cover_chapter = epub.EpubHtml(title='作品信息', file_name='cover.xhtml', lang='zh')
            cover_chapter.content = cover_content
            cover_chapter.add_item(css)
            book.add_item(cover_chapter)
            chapters.append(cover_chapter)
        
        # 内容章节
        if chapters_info:
            for idx, (ch_title, ch_content) in enumerate(chapters_info):
                ch = epub.EpubHtml(title=ch_title, file_name=f'chapter_{idx+1}.xhtml', lang='zh')
                content = f'<html><head><link rel="stylesheet" href="style/main.css"/></head><body>'
                content += f'<h2>{ch_title}</h2>'
                for para in ch_content:
                    if para.strip():
                        content += f'<p>{para}</p>'
                content += '</body></html>'
                ch.content = content
                ch.add_item(css)
                book.add_item(ch)
                chapters.append(ch)
        else:
            # 单章节
            main_ch = epub.EpubHtml(title='正文', file_name='content.xhtml', lang='zh')
            content = f'<html><head><link rel="stylesheet" href="style/main.css"/></head><body>'
            content += f'<h1>{title}</h1>'
            for para in content_parts:
                if para.strip() and not para.strip().startswith('='*10):
                    content += f'<p>{para}</p>'
            content += '</body></html>'
            main_ch.content = content
            main_ch.add_item(css)
            book.add_item(main_ch)
            chapters.append(main_ch)
        
        # 目录
        book.toc = chapters
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ['nav'] + chapters
        
        # 保存
        epub.write_epub(filepath, book)
        return True
    except Exception as e:
        print(f"EPUB生成失败: {e}")
        return False


def run_ao3_task(params):
    """运行AO3文章爬取任务 - 参考 https://github.com/610yilingliu/download_ao3_v2"""
    from lxml import etree
    from bs4 import BeautifulSoup
    import html as html_module
    
    urls = params.get('urls', [])
    mode = params.get('mode', 'work')  # work, series, author, tag
    download_chapters = params.get('download_chapters', True)
    save_metadata = params.get('save_metadata', True)
    export_pdf = params.get('export_pdf', False)  # 是否导出PDF
    export_epub = params.get('export_epub', False)  # 是否导出EPUB
    
    # PDF生成的HTML模板
    def generate_html_content(title, author, work_url, metadata_list, content_parts, chapters_info=None):
        """生成美化的HTML内容 - 书籍风格"""
        import datetime
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 处理元数据
        meta_html = ""
        fandom = ""
        rating = ""
        
        if metadata_list:
            for meta in metadata_list:
                meta = meta.strip()
                if not meta: continue
                
                # 提取关键信息用于封面
                if meta.startswith("Fandom:"):
                    fandom = meta.split(":", 1)[1].strip()
                elif meta.startswith("Rating:"):
                    rating = meta.split(":", 1)[1].strip()
                
                if ':' in meta:
                    key, value = meta.split(':', 1)
                    meta_html += f'<div class="meta-item"><span class="meta-label">{key.strip()}:</span> <span class="meta-value">{value.strip()}</span></div>\n'
                else:
                    meta_html += f'<div class="meta-item">{meta}</div>\n'
        
        # 处理正文内容
        content_html = ""
        if chapters_info:
            # 多章节
            for i, (ch_title, ch_content) in enumerate(chapters_info):
                content_html += f'<div class="chapter">\n'
                content_html += f'<h2 class="chapter-title">{ch_title}</h2>\n'
                for para in ch_content:
                    if para.strip():
                        content_html += f'<p>{para}</p>\n'
                content_html += '</div>\n'
                # 章节结束后添加分页符（除最后一章外）
                if i < len(chapters_info) - 1:
                    content_html += '<div class="page-break"></div>\n'
        else:
            # 单章节
            content_html += '<div class="chapter">\n'
            for para in content_parts:
                # 过滤掉TXT格式的分隔符
                if para.strip() and not para.strip().startswith('='*10):
                    content_html += f'<p>{para}</p>\n'
            content_html += '</div>\n'
        
        html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title} - {author}</title>
    <style>
        @page {{
            size: A4;
            margin: 2.5cm 2cm;
            @bottom-center {{
                content: counter(page);
                font-size: 10pt;
                color: #666;
            }}
        }}
        
        body {{
            font-family: STSong-Light, SimSun, serif;
            font-size: 12pt;
            line-height: 1.8;
            color: #222;
            background: #fff;
        }}
        
        /* 封面样式 */
        .cover {{
            text-align: center;
            padding-top: 15%;
            page-break-after: always;
            height: 100%;
        }}
        
        .cover-title {{
            font-size: 32pt;
            font-weight: bold;
            margin-bottom: 30px;
            color: #2c3e50;
            line-height: 1.3;
        }}
        
        .cover-author {{
            font-size: 18pt;
            margin-bottom: 60px;
            color: #555;
        }}
        
        .cover-meta {{
            font-size: 12pt;
            color: #7f8c8d;
            margin-top: 100px;
            border-top: 1px solid #ddd;
            padding-top: 30px;
            width: 60%;
            margin-left: auto;
            margin-right: auto;
        }}
        
        .cover-fandom {{
            font-style: italic;
            margin-bottom: 10px;
        }}
        
        /* 元数据页 */
        .metadata-page {{
            page-break-after: always;
            padding: 2cm 0;
        }}
        
        .metadata-title {{
            font-size: 18pt;
            border-bottom: 2px solid #8B4513;
            padding-bottom: 10px;
            margin-bottom: 30px;
            color: #8B4513;
        }}
        
        .metadata-content {{
            background-color: #fafafa;
            padding: 20px;
            border: 1px solid #eee;
            border-radius: 5px;
        }}
        
        .meta-item {{
            margin-bottom: 8px;
            font-size: 11pt;
        }}
        
        .meta-label {{
            font-weight: bold;
            color: #555;
        }}
        
        /* 正文样式 */
        .content {{
            text-align: justify;
        }}
        
        .chapter-title {{
            font-size: 18pt;
            font-weight: bold;
            text-align: center;
            margin: 40px 0 30px 0;
            color: #2c3e50;
        }}
        
        p {{
            text-indent: 2em;
            margin-bottom: 12px;
            line-height: 1.8;
        }}
        
        .page-break {{
            page-break-after: always;
        }}
        
        a {{ color: #3498db; text-decoration: none; }}
    </style>
</head>
<body>
    <!-- 封面页 -->
    <div class="cover">
        <div class="cover-title">{title}</div>
        <div class="cover-author">By {author}</div>
        
        <div class="cover-meta">
            {f'<div class="cover-fandom">{fandom}</div>' if fandom else ''}
            <div>Rating: {rating or 'Not Rated'}</div>
            <div style="margin-top: 20px; font-size: 10pt;">
                Generated by Lofter Spider<br/>
                {current_date}
            </div>
        </div>
    </div>
    
    <!-- 元数据页 -->
    <div class="metadata-page">
        <div class="metadata-title">Work Details</div>
        <div class="metadata-content">
            {meta_html}
            <div class="meta-item" style="margin-top: 20px; border-top: 1px dashed #ccc; padding-top: 10px;">
                <span class="meta-label">Original URL:</span> 
                <span class="meta-value">{work_url}</span>
            </div>
        </div>
    </div>
    
    <!-- 正文内容 -->
    <div class="content">
        {content_html}
    </div>
</body>
</html>'''
        return html_template
    
    def save_as_pdf(html_content, filepath):
        """将HTML内容保存为PDF - 使用xhtml2pdf，支持中文"""
        try:
            from xhtml2pdf import pisa
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            
            # 注册中文CID字体 (ReportLab内置，支持简体中文)
            try:
                pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            except Exception:
                pass
            
            with open(filepath, 'wb') as pdf_file:
                pisa_status = pisa.CreatePDF(
                    html_content.encode('utf-8'),
                    dest=pdf_file,
                    encoding='utf-8'
                )
            
            if pisa_status.err:
                add_log(f"   ⚠️ PDF生成有警告，但文件已创建")
            return True
            
        except Exception as e:
            add_log(f"   ⚠️ PDF生成失败: {str(e)}")
            return False
    
    if not urls:
        add_log('❌ 请提供AO3链接')
        return
    
    add_log(f"📚 开始AO3爬取任务，模式: {mode}")
    add_log(f"📍 共 {len(urls)} 个链接")
    
    # 创建保存目录（使用自定义路径）
    save_root = config.get('save_path', './dir')
    base_dir = os.path.join(save_root, 'ao3')
    os.makedirs(base_dir, exist_ok=True)
    
    # AO3请求Session - 更好的连接管理
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    })
    # 设置cookie绕过年龄确认
    session.cookies.set('accepted_tos', '20180523', domain='.archiveofourown.org')
    session.cookies.set('view_adult', 'true', domain='.archiveofourown.org')
    
    # 用于兼容旧代码的headers变量
    ao3_headers = session.headers
    
    saved_count = 0
    
    def safe_filename(name):
        """生成安全的文件名"""
        # Windows非法字符
        invalid_chars = r'[\\/*?:"<>|\r\n\t]'
        name = re.sub(invalid_chars, '_', name).strip()
        # 移除连续空格和下划线
        name = re.sub(r'[_\s]+', ' ', name).strip()
        return name[:100] if name else "untitled"
    
    def fetch_with_retry(url, max_retries=3, wait_time=30):
        """带重试逻辑的请求函数"""
        for attempt in range(max_retries):
            try:
                response = session.get(url, timeout=30)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    # 请求过于频繁
                    add_log(f"   ⚠️ 请求过于频繁(429)，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 404:
                    add_log(f"   ⚠️ 作品不存在或已删除 (404)")
                    return None
                elif response.status_code == 403:
                    add_log(f"   ⚠️ 无权访问 (403)，可能需要登录或作品已锁定")
                    return None
                else:
                    add_log(f"   ⚠️ HTTP {response.status_code}，重试中...")
                    time.sleep(5)
                    
            except requests.exceptions.Timeout:
                add_log(f"   ⚠️ 请求超时，重试 {attempt + 1}/{max_retries}")
                time.sleep(10)
            except requests.exceptions.ConnectionError:
                add_log(f"   ⚠️ 连接错误，重试 {attempt + 1}/{max_retries}")
                time.sleep(10)
            except Exception as e:
                add_log(f"   ⚠️ 请求错误: {str(e)}")
                time.sleep(5)
        
        add_log(f"   ❌ 多次重试后仍然失败")
        return None
    
    def download_work(work_url):
        """下载单个作品"""
        nonlocal saved_count
        
        try:
            # 检查是否已下载（自动去重）
            if is_url_downloaded(work_url):
                add_log(f"⏭️ 已下载过，跳过: {work_url}")
                return
            
            add_log(f"📖 正在获取: {work_url}")
            
            # 处理 ?view_adult=true 参数
            if '?' not in work_url:
                work_url_with_adult = work_url + "?view_adult=true"
            else:
                work_url_with_adult = work_url + "&view_adult=true"
            
            # 获取作品页面 (带重试)
            response = fetch_with_retry(work_url_with_adult)
            if response is None:
                return
            
            html_content = response.content.decode('utf-8')
            soup = BeautifulSoup(html_content, 'html.parser')
            tree = etree.HTML(html_content)
            
            # 提取作品信息 - 使用BeautifulSoup
            title_elem = soup.find('h2', class_='title heading')
            title = title_elem.get_text(strip=True) if title_elem else "未知标题"
            
            author_elem = soup.find('a', rel='author')
            author = author_elem.get_text(strip=True) if author_elem else "未知作者"
            
            # 获取元数据
            metadata = []
            if save_metadata:
                # Fandom
                fandoms = tree.xpath('//dd[@class="fandom tags"]//a/text()')
                if fandoms:
                    metadata.append(f"Fandom: {', '.join(fandoms)}")
                
                # Rating
                rating = tree.xpath('//dd[@class="rating tags"]//a/text()')
                if rating:
                    metadata.append(f"Rating: {rating[0]}")
                
                # Warnings
                warnings = tree.xpath('//dd[@class="warning tags"]//a/text()')
                if warnings:
                    metadata.append(f"Warnings: {', '.join(warnings)}")
                
                # Relationships
                relationships = tree.xpath('//dd[@class="relationship tags"]//a/text()')
                if relationships:
                    metadata.append(f"Relationships: {', '.join(relationships[:5])}")
                
                # Characters
                characters = tree.xpath('//dd[@class="character tags"]//a/text()')
                if characters:
                    metadata.append(f"Characters: {', '.join(characters[:10])}")
                
                # Additional Tags
                tags = tree.xpath('//dd[@class="freeform tags"]//a/text()')
                if tags:
                    metadata.append(f"Tags: {', '.join(tags[:10])}")
                
                # Summary
                summary_elem = tree.xpath('//div[@class="summary module"]//blockquote//text()')
                if summary_elem:
                    summary = ' '.join([s.strip() for s in summary_elem if s.strip()])
                    metadata.append(f"\nSummary:\n{summary}")
                
                # Stats
                words = tree.xpath('//dd[@class="words"]/text()')
                chapters = tree.xpath('//dd[@class="chapters"]/text()')
                if words:
                    metadata.append(f"\nWords: {words[0]}")
                if chapters:
                    metadata.append(f"Chapters: {chapters[0]}")
            
            add_log(f"   📝 标题: {title}")
            add_log(f"   👤 作者: {author}")
            
            # 获取正文内容
            content_parts = []
            chapters_info = []  # 用于PDF生成: [(章节标题, [段落列表]), ...]
            
            # 检查是否有多章节
            chapter_links = tree.xpath('//div[@id="chapter_index"]//option/@value')
            
            if chapter_links and download_chapters and len(chapter_links) > 1:
                add_log(f"   📑 共 {len(chapter_links)} 章节")
                
                for idx, chapter_id in enumerate(chapter_links):
                    chapter_url = f"{work_url.split('?')[0]}/chapters/{chapter_id.split('/')[-1]}?view_adult=true"
                    add_log(f"      第 {idx+1}/{len(chapter_links)} 章...")
                    task_status['progress'] = int((idx / len(chapter_links)) * 50) + 50
                    
                    try:
                        ch_response = fetch_with_retry(chapter_url)
                        if ch_response is None:
                            continue
                        ch_soup = BeautifulSoup(ch_response.content.decode('utf-8'), 'html.parser')
                        ch_tree = etree.HTML(ch_response.content.decode('utf-8'))
                        
                        # 章节标题
                        ch_title_elem = ch_tree.xpath('//h3[@class="title"]//text()')
                        ch_title = ' '.join([t.strip() for t in ch_title_elem if t.strip()])
                        if not ch_title:
                            ch_title = f"第 {idx + 1} 章"
                        
                        # 章节内容
                        ch_content_elem = ch_tree.xpath('//div[@class="userstuff module"]//p')
                        ch_content = []
                        for p in ch_content_elem:
                            text = etree.tostring(p, method='text', encoding='unicode')
                            if text.strip():
                                ch_content.append(text.strip())
                        
                        # 保存章节信息用于PDF
                        chapters_info.append((ch_title, ch_content))
                        
                        # TXT格式
                        if ch_title:
                            content_parts.append(f"\n\n{'='*60}\n{ch_title}\n{'='*60}\n")
                        content_parts.append('\n\n'.join(ch_content))
                        
                        time.sleep(0.5)  # 避免请求过快
                        
                    except Exception as e:
                        add_log(f"      ⚠️ 获取章节失败: {str(e)}")
            else:
                # 单章节或不下载全部章节
                content_elem = tree.xpath('//div[@class="userstuff module"]//p | //div[@id="chapters"]//div[@class="userstuff"]//p')
                for p in content_elem:
                    text = etree.tostring(p, method='text', encoding='unicode')
                    if text.strip():
                        content_parts.append(text.strip())
            
            if not content_parts:
                # 尝试其他方式获取内容
                content_elem = tree.xpath('//div[contains(@class, "userstuff")]//text()')
                content_parts = [t.strip() for t in content_elem if t.strip() and len(t.strip()) > 10]
            
            # 组装TXT文章
            article = f"{title}\nby {author}\n"
            article += f"原文链接: {work_url}\n"
            article += "\n" + "="*60 + "\n"
            
            if metadata:
                article += "\n".join(metadata)
                article += "\n\n" + "="*60 + "\n"
            
            article += "\n\n".join(content_parts)
            
            # 创建作者目录
            author_dir = os.path.join(base_dir, safe_filename(author))
            os.makedirs(author_dir, exist_ok=True)
            
            # 保存TXT文件
            txt_filename = f"{safe_filename(title)}.txt"
            txt_filepath = os.path.join(author_dir, txt_filename)
            
            # 避免重名
            counter = 1
            original_filepath = txt_filepath
            while os.path.exists(txt_filepath):
                name_part = original_filepath.rsplit('.', 1)[0]
                txt_filepath = f"{name_part}({counter}).txt"
                counter += 1
            
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(article)
            
            saved_count += 1
            add_log(f"   ✅ 已保存: {txt_filename}")
            
            # 记录到下载历史
            add_to_history(
                item_type='ao3',
                url=work_url,
                title=title,
                author=author,
                file_path=txt_filepath,
                source='ao3'
            )
            
            # 如果需要导出PDF
            if export_pdf:
                add_log(f"   📄 正在生成PDF...")
                pdf_filename = txt_filename.replace('.txt', '.pdf')
                pdf_filepath = txt_filepath.replace('.txt', '.pdf')
                
                # 生成HTML内容
                html_content = generate_html_content(
                    title=title,
                    author=author,
                    work_url=work_url,
                    metadata_list=metadata,
                    content_parts=content_parts if not chapters_info else [],
                    chapters_info=chapters_info if chapters_info else None
                )
                
                # 同时保存HTML文件（方便调试和自定义）
                html_filepath = txt_filepath.replace('.txt', '.html')
                with open(html_filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # 生成PDF
                if save_as_pdf(html_content, pdf_filepath):
                    add_log(f"   📄 已生成PDF: {pdf_filename}")
            
            # 如果需要导出EPUB
            if export_epub:
                add_log(f"   📖 正在生成EPUB...")
                epub_filename = txt_filename.replace('.txt', '.epub')
                epub_filepath = txt_filepath.replace('.txt', '.epub')
                
                if generate_epub(
                    title=title,
                    author=author,
                    content_parts=content_parts,
                    chapters_info=chapters_info if chapters_info else None,
                    metadata_list=metadata,
                    filepath=epub_filepath
                ):
                    add_log(f"   📖 已生成EPUB: {epub_filename}")
            
        except Exception as e:
            add_log(f"   ❌ 下载失败: {str(e)}")
    
    def get_works_from_series(series_url):
        """获取系列中的所有作品链接"""
        try:
            add_log(f"📚 获取系列作品列表: {series_url}")
            response = fetch_with_retry(series_url)
            if response is None:
                return []
            tree = etree.HTML(response.content.decode('utf-8'))
            
            work_links = tree.xpath('//ul[@class="series work index group"]//h4[@class="heading"]//a[1]/@href')
            work_urls = [f"https://archiveofourown.org{link}" for link in work_links if '/works/' in link]
            
            add_log(f"   找到 {len(work_urls)} 篇作品")
            return work_urls
        except Exception as e:
            add_log(f"   ❌ 获取系列失败: {str(e)}")
            return []
    
    def get_works_from_author(author_url, max_pages=20):
        """获取作者的所有作品链接"""
        try:
            add_log(f"👤 获取作者作品列表: {author_url}")
            
            all_works = []
            page = 1
            
            while True:
                page_url = f"{author_url}?page={page}"
                response = fetch_with_retry(page_url)
                if response is None:
                    break
                tree = etree.HTML(response.content.decode('utf-8'))
                
                work_links = tree.xpath('//ol[@class="work index group"]//h4[@class="heading"]//a[1]/@href')
                new_works = [f"https://archiveofourown.org{link}" for link in work_links if '/works/' in link]
                
                if not new_works:
                    break
                
                all_works.extend(new_works)
                add_log(f"   第 {page} 页: 找到 {len(new_works)} 篇")
                
                # 检查是否有下一页
                next_page = tree.xpath('//li[@class="next"]//a/@href')
                if not next_page:
                    break
                
                page += 1
                if page > max_pages:
                    add_log(f"   ⚠️ 已达到 {max_pages} 页限制")
                    break
                
                time.sleep(0.5)
            
            add_log(f"   共找到 {len(all_works)} 篇作品")
            return all_works
            
        except Exception as e:
            add_log(f"   ❌ 获取作者作品失败: {str(e)}")
            return []
    
    def get_works_from_tag(tag_url, max_pages=5):
        """获取Tag下的所有作品链接"""
        try:
            # 提取tag名称用于显示
            tag_match = re.search(r'/tags/([^/]+)/works', tag_url)
            tag_name = tag_match.group(1) if tag_match else "未知标签"
            tag_name = requests.utils.unquote(tag_name)
            
            add_log(f"🏷️ 获取Tag作品列表: {tag_name}")
            
            all_works = []
            page = 1
            
            while True:
                # AO3 tag页面的分页格式
                if '?' in tag_url:
                    page_url = f"{tag_url}&page={page}"
                else:
                    page_url = f"{tag_url}?page={page}"
                
                add_log(f"   正在获取第 {page} 页...")
                response = fetch_with_retry(page_url)
                
                if response is None:
                    add_log(f"   ⚠️ 获取页面失败")
                    break
                
                tree = etree.HTML(response.content.decode('utf-8'))
                
                # AO3 作品列表的选择器
                work_links = tree.xpath('//ol[contains(@class, "work index")]//h4[@class="heading"]//a[1]/@href')
                new_works = [f"https://archiveofourown.org{link}" for link in work_links if '/works/' in link]
                
                if not new_works:
                    add_log(f"   第 {page} 页没有更多作品")
                    break
                
                all_works.extend(new_works)
                add_log(f"   第 {page} 页: 找到 {len(new_works)} 篇")
                
                # 检查是否有下一页
                next_page = tree.xpath('//li[@class="next"]//a/@href')
                if not next_page:
                    add_log("   已到达最后一页")
                    break
                
                page += 1
                if page > max_pages:
                    add_log(f"   ⚠️ 已达到 {max_pages} 页限制")
                    break
                
                time.sleep(1)  # AO3对频繁请求比较敏感
            
            add_log(f"   🏷️ Tag [{tag_name}] 共找到 {len(all_works)} 篇作品")
            return all_works
            
        except Exception as e:
            add_log(f"   ❌ 获取Tag作品失败: {str(e)}")
            return []
    
    # 获取最大页数参数
    max_pages = params.get('max_pages', 5)
    
    # 处理每个URL
    all_work_urls = []
    
    for url in urls:
        url = url.strip()
        if not url:
            continue
        
        if '/series/' in url:
            # 系列作品
            work_urls = get_works_from_series(url)
            all_work_urls.extend(work_urls)
        elif '/users/' in url and '/works' in url:
            # 作者作品页
            work_urls = get_works_from_author(url, max_pages)
            all_work_urls.extend(work_urls)
        elif '/tags/' in url and '/works' in url:
            # Tag作品页
            work_urls = get_works_from_tag(url, max_pages)
            all_work_urls.extend(work_urls)
        elif '/works/' in url:
            # 单个作品
            all_work_urls.append(url)
        else:
            add_log(f"⚠️ 无法识别的链接格式: {url}")
    
    # 去重
    all_work_urls = list(dict.fromkeys(all_work_urls))
    add_log(f"📊 共 {len(all_work_urls)} 篇作品待下载")
    
    # 下载所有作品
    for idx, work_url in enumerate(all_work_urls):
        task_status['progress'] = int((idx / len(all_work_urls)) * 100)
        download_work(work_url)
        time.sleep(1)  # 避免请求过快
    
    add_log(f"✅ AO3下载完成！")
    add_log(f"   📚 共保存 {saved_count} 篇文章")
    add_log(f"   📁 保存位置: {base_dir}/作者名/")


# ============ API 路由 ============

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """处理配置"""
    if request.method == 'GET':
        cfg = load_config()
        hidden_auth = cfg['login_auth']
        if len(hidden_auth) > 10:
            hidden_auth = hidden_auth[:5] + '...' + hidden_auth[-5:]
        return jsonify({
            'login_key': cfg['login_key'],
            'login_auth': hidden_auth,
            'has_auth': bool(cfg['login_auth']),
            'file_path': cfg['file_path']
        })
    else:
        data = request.json
        save_login_info(data.get('login_key', ''), data.get('login_auth', ''))
        return jsonify({'success': True, 'message': '配置已保存'})

@app.route('/api/task/start', methods=['POST'])
def start_task():
    """启动任务"""
    if task_status['running']:
        return jsonify({'success': False, 'message': '已有任务在运行中'})
    
    data = request.json
    task_type = data.get('type')
    params = data.get('params', {})
    
    thread = threading.Thread(target=run_spider_task, args=(task_type, params))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': '任务已启动'})

@app.route('/api/task/status')
def get_task_status():
    """获取任务状态"""
    return jsonify(task_status)

@app.route('/api/task/stop', methods=['POST'])
def stop_task():
    """停止任务"""
    task_status['running'] = False
    add_log('⚠️ 任务已停止')
    return jsonify({'success': True, 'message': '任务已停止'})

@app.route('/api/files')
def list_files():
    """列出已下载的文件"""
    base_path = config['file_path']
    files = []
    
    if os.path.exists(base_path):
        for root, dirs, filenames in os.walk(base_path):
            for filename in filenames:
                if not filename.endswith('.json') and not filename.startswith('.'):
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, base_path)
                    file_size = os.path.getsize(full_path)
                    files.append({
                        'name': filename,
                        'path': rel_path,
                        'size': file_size,
                        'type': 'image' if filename.lower().endswith(('.jpg', '.png', '.gif', '.jpeg')) else 'text'
                    })
    
    # 按修改时间排序，最新的在前
    files.sort(key=lambda x: x['name'], reverse=True)
    return jsonify({'files': files[:200], 'total': len(files)})

@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    return send_from_directory('static', filename)

# ============ 下载历史 API ============

@app.route('/api/history')
def get_history():
    """获取下载历史"""
    history = load_download_history()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    filter_type = request.args.get('type', '')  # 'image', 'article', 'ao3', ''
    filter_source = request.args.get('source', '')  # 'lofter', 'ao3', ''
    search = request.args.get('search', '')
    
    items = history['items']
    
    # 过滤
    if filter_type:
        items = [i for i in items if i.get('type') == filter_type]
    if filter_source:
        items = [i for i in items if i.get('source') == filter_source]
    if search:
        search_lower = search.lower()
        items = [i for i in items if 
                 search_lower in i.get('title', '').lower() or 
                 search_lower in i.get('author', '').lower()]
    
    # 分页
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    items = items[start:end]
    
    return jsonify({
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'stats': history['stats']
    })

@app.route('/api/history/clear', methods=['POST'])
def api_clear_history():
    """清空下载历史"""
    result = clear_download_history()
    if result:
        return jsonify({'success': True, 'message': '历史记录已清空'})
    return jsonify({'success': False, 'message': '清空失败'})

@app.route('/api/history/delete/<item_id>', methods=['DELETE'])
def delete_history_item(item_id):
    """删除单条历史记录"""
    history = load_download_history()
    history['items'] = [i for i in history['items'] if i.get('id') != item_id]
    save_download_history(history)
    return jsonify({'success': True, 'message': '记录已删除'})

@app.route('/api/history/check', methods=['POST'])
def check_downloaded():
    """检查URL是否已下载"""
    data = request.json
    url = data.get('url', '')
    downloaded = is_url_downloaded(url)
    return jsonify({'downloaded': downloaded, 'url': url})

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    """处理应用设置"""
    global config
    if request.method == 'GET':
        # 确保加载最新配置
        load_config_file()
        return jsonify({
            'save_path': config.get('save_path', './dir'),
            'dark_mode': config.get('dark_mode', False),
            'auto_dedup': config.get('auto_dedup', True),
            'notify_on_complete': config.get('notify_on_complete', True)
        })
    else:
        data = request.json
        if 'save_path' in data:
            save_path = data['save_path']
            config['save_path'] = save_path
            # 确保目录存在
            try:
                os.makedirs(save_path, exist_ok=True)
                os.makedirs(os.path.join(save_path, 'img'), exist_ok=True)
                os.makedirs(os.path.join(save_path, 'article'), exist_ok=True)
            except Exception as e:
                return jsonify({'success': False, 'message': f'创建目录失败: {str(e)}'})
        if 'dark_mode' in data:
            config['dark_mode'] = data['dark_mode']
        if 'auto_dedup' in data:
            config['auto_dedup'] = data['auto_dedup']
        if 'notify_on_complete' in data:
            config['notify_on_complete'] = data['notify_on_complete']
        # 保存配置到文件
        save_config_file()
        return jsonify({'success': True, 'message': '设置已保存'})

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # 加载配置文件
    load_config()
    
    save_path = config.get('save_path', './dir')
    os.makedirs(save_path, exist_ok=True)
    os.makedirs(os.path.join(save_path, 'img'), exist_ok=True)
    os.makedirs(os.path.join(save_path, 'article'), exist_ok=True)
    
    print("=" * 50)
    print("Lofter Spider Web Application")
    print("=" * 50)
    print(f"保存路径: {save_path}")
    print("Visit http://localhost:5000 to start")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
