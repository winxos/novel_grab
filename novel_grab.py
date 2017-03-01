# coding:utf-8
'''
general novel scraper
env:python 3.5
license:MIT
author:winxos
since:2017-02-19
'''
import urllib.request
from urllib.parse import urlsplit
from lxml import etree
import json
from multiprocessing import Pool, Manager
from time import clock
import traceback
from functools import partial

POOLS_SIZE = 20
TRY_TIMES = 3
SINGLE_THREAD_DEBUG = False

with open('novels_config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)


def get_chapter(url, loc, RULE_ID):
    try:
        f = urllib.request.urlopen(url)
        c = etree.HTML(f.read().decode(CONFIG["rules"][RULE_ID]["charset"]))
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
        for x in CONFIG["rules"][RULE_ID]["replace"]:
            for src, des in x.items():
                data = data.replace(src, des)
    except Exception as e:  # 捕捉访问异常，一般为timeout，信息在e中
        print("[err] %s" % url)
        print(traceback.format_exc())
        return None
    return data


def save_txt(name, data, mode='a'):
    with open(name, mode, encoding='utf8') as f:
        f.write(data)


def scrape(RULE_ID, chapter_info):
    global TRY_TIMES
    h, c = chapter_info
    p = get_chapter(h, CONFIG["rules"][RULE_ID]["chapter_content"], RULE_ID)
    if p == None and TRY_TIMES > 0:
        print("[err] retry downloading %d:%s %s" % (TRY_TIMES, c, h))
        TRY_TIMES -= 1
        _, p = scrape(RULE_ID, chapter_info)
    if p == None:
        print("[err] downloaded %s failed. %s" % (c, h))
        p = ""
    else:
        print("[debug] downloaded %s" % c)
    return (c, p)


def download_novel(url_entry):
    server_vars = Manager()
    rule_id = server_vars.Value('i', -1)
    server_url = "{0.scheme}://{0.netloc}/".format(urlsplit(url_entry))
    for i, info in enumerate(CONFIG["rules"]):
        if server_url == info["site"]:
            rule_id = i
            print("[debug] match config %s" % server_url)
            break
    if rule_id == -1:
        print("[err] 系统暂不支持该网站下载，请自行修改配置文件以支持。")
        exit()
    if url_entry.endswith("/"):  # for some relative site
        server_url = url_entry
    st = clock()
    html = etree.HTML(urllib.request.urlopen(url_entry).read())
    title = html.xpath(CONFIG["rules"][rule_id]["title"])[0].xpath("string(.)")
    author = html.xpath(CONFIG["rules"][rule_id]["author"])[
        0].xpath("string(.)")
    file_name = title + " " + author + ".txt"
    href = html.xpath(CONFIG["rules"][rule_id]["chapter_href"])
    if not str(href[0]).startswith("http"):  # not absolute link
        href = [server_url + h for h in href]
    capital = html.xpath(CONFIG["rules"][rule_id]["chapter_name"])
    save_txt(file_name, title + "\n" + author + "\n", mode='w')
    chapter_info = zip(href, capital)
    print("[debug] downloading: %s" % file_name)
    func = partial(scrape, rule_id)  # wrap multiple arguments
    if not SINGLE_THREAD_DEBUG:
        pool = Pool(processes=POOLS_SIZE)
        results = pool.map(func, chapter_info)
        pool.close()
        pool.join()
    else:
        results = []
        for hc in list(chapter_info)[:10]:
            results.append(func(hc))

    print('[debug] done. used:%f s' % (clock() - st))
    for c, k in results:
        save_txt(file_name, c + "\n" + k + "\n")

'''
usage:
download_novel("your novel chapter lists page link")
'''
if __name__ == '__main__':
    # download_novel('http://book.zongheng.com/showchapter/390021.html')
    # download_novel('http://www.aoyuge.com/9/9007/index.html')
    # download_novel('http://www.quanshu.net/book/38/38215/')
    download_novel('http://book.zongheng.com/showchapter/403749.html')
