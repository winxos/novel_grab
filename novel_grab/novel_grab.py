# coding:utf-8
# general novel scraper
# env:python 3.5
# license:MIT
# author:winxos
# since:2017-02-19

import urllib.request
import urllib.error
from urllib.parse import urlsplit
from lxml import etree
import json
from multiprocessing import Pool, Manager
from time import clock
from functools import partial
import zipfile
import os  # remove file
import pkgutil  # 必须采用pkgutil.get_data才能读取egg格式包中的数据
import sys  # stdout flush

POOLS_SIZE = 20
TRY_TIMES = 3
SINGLE_THREAD_DEBUG = False

CONFIG = None

try:
    CONFIG = json.loads(pkgutil.get_data("novel_grab", 'grab_config.json').decode('utf-8'))
except IOError as e:
    print("[error] %s" % e)
    exit()


def get_content(url, charset):
    global TRY_TIMES
    try:
        f = urllib.request.urlopen(url)
        TRY_TIMES = 10  # todo 用类进行封装
        return etree.HTML(f.read().decode(charset))
    except UnicodeDecodeError as ude:
        print("[error] decode error %s" % url)
        print("[debug] info %s" % ude)
    except urllib.error.URLError or TimeoutError:  # 捕捉访问异常，一般为timeout，信息在e中
        print("[warning] %d retry %s" % (TRY_TIMES, url))
        # print(traceback.format_exc())
        TRY_TIMES -= 1
        if TRY_TIMES > 0:
            return get_content(url, charset)
    return None


def get_items(selector, xpath):
    return selector.xpath(xpath)


def get_chapter(url, loc, rule_id):
    try:
        s = get_content(url, CONFIG["rules"][rule_id]["charset"])
        if s is None:
            return
        c = get_items(s, loc)[0]
        # raw elements of div filter none text element
        # support two type, div//p/text div/text
        raw_txt = [x.xpath("text()") for x in c.xpath(loc)]
        if len(raw_txt) > 1:
            raw_txt = [x[0] for x in raw_txt]
        else:
            raw_txt = raw_txt[0]
        # remove some strange blank.
        data = "\n".join([t.strip() for t in raw_txt])
        # data = data.replace('\xa0', '')
        for x in CONFIG["rules"][rule_id]["replace"]:
            for src, des in x.items():
                data = data.replace(src, des)
    except TimeoutError:  # 捕捉访问异常，一般为timeout，信息在e中
        print("[error] %s" % url)
        return None
    return data


def save_txt(name, data, mode='a'):
    with open(name, mode, encoding='utf8') as f:
        f.write(data)


def scrape(rule_id, chapter_info):
    global TRY_TIMES
    h, c = chapter_info
    p = get_chapter(h, CONFIG["rules"][rule_id]["chapter_content"], rule_id)
    if p is None:
        print("[error] downloaded %s failed. %s" % (c, h))
        p = "download error, read at %s" % h
    # else:
    #     print("[debug] downloaded %s" % c)
    return c, p


def download(url_entry):
    """
    usage:
    from novel_grab import novel_grab
    novel_grab.download('the url or the novel all chapter page')
    if the site supported, then will download all the content and create a zip file.
    if you wanna make it support other site, let me know
    have fun
    winxos 2017-04-02
    just for educational purpose.
    """
    server_vars = Manager()
    rule_id = server_vars.Value('i', -1)
    server_url = "{0.scheme}://{0.netloc}/".format(urlsplit(url_entry))
    for i, info in enumerate(CONFIG["rules"]):
        if server_url == info["site"]:
            rule_id = i
            print("[debug] match config %s" % server_url)
            break
    if rule_id == -1:
        print("[error] 系统暂不支持该网站下载，请自行修改配置文件以支持。")
        exit()
    if url_entry.endswith("/"):  # for some relative site
        server_url = url_entry
    st = clock()
    html = get_content(url_entry, CONFIG["rules"][rule_id]["charset"])
    title = get_items(html, CONFIG["rules"][rule_id]["title"])[0].xpath("string(.)")
    author = get_items(html, CONFIG["rules"][rule_id]["author"])[0].xpath("string(.)")
    file_name = title + " " + author + ".txt"
    href = get_items(html, CONFIG["rules"][rule_id]["chapter_href"])
    if not href:  # []
        print("[error] grab pattern can't match.")
        return
    if not str(href[0]).startswith("http"):  # not absolute link
        href = [server_url + h for h in href]
    capital = get_items(html, CONFIG["rules"][rule_id]["chapter_name"])
    chapter_info = zip(href, capital)
    print("[debug] downloading: %s" % file_name)
    func = partial(scrape, rule_id)  # wrap multiple arguments
    pool = Pool(processes=int(CONFIG["rules"][rule_id]["pool_size"]))
    if not SINGLE_THREAD_DEBUG:
        results = []
        gi = pool.imap(func, chapter_info)
        for i in range(len(href)):
            results.append(gi.next())
            if i % POOLS_SIZE == 0:
                print("\r[debug] downloading progress %.2f%%" % (i * 100 / len(href)), end="")
                sys.stdout.flush()
    else:
        results = []
        for hc in list(chapter_info)[:10]:
            results.append(func(hc))
    print('[debug] done. used:%f s' % (clock() - st))
    print('[debug] saving to file...')
    create_zip_file(title, author, results)
    exit()


# zip the file, ZIP_LZMA use lot of memory,
def create_zip_file(title, author, results, method=zipfile.ZIP_DEFLATED):
    file_name = title + " " + author + ".txt"
    zip_file_name = title + " " + author + ".zip"
    save_txt(file_name, title + "\n" + author + "\n", mode='w')
    for c, k in results:
        save_txt(file_name, c + "\n" + k + "\n\n")
    zf = zipfile.ZipFile(zip_file_name, 'w', method)  # zipfile.ZIP_LZMA
    zf.write(file_name)
    zf.close()
    os.remove(file_name)
    print('[debug] save to %s' % zip_file_name)


def test():
    # download('http://book.zongheng.com/showchapter/390021.html')
    # download('http://www.aoyuge.com/14/14743/index.html')
    # download('http://www.quanshu.net/book/38/38215/')
    download('http://book.zongheng.com/showchapter/403749.html')
    # download('http://www.quanshu.net/book/67/67604/')


'''
usage:
download("your novel chapter lists page link")
'''
if __name__ == '__main__':
    test()
else:
    print(download.__doc__)
