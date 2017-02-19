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
from multiprocessing import Pool
from time import clock
import traceback
from itertools import repeat

RULE_ID = 0
POOLS_SIZE = 40
try_times = 3

with open('novels_config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

#todo multiprocess vars not set
def get_chapter(url, loc):
    global RULE_ID
    try:
        f = urllib.request.urlopen(url)
        print(RULE_ID)
        print(CONFIG["rules"][RULE_ID]["charset"])
        c = etree.HTML(f.read().decode(CONFIG["rules"][RULE_ID]["charset"]))
        data = c.xpath(loc)[0].xpath("string(.)").strip()
        data = data.replace('\xa0', '')
        for x in CONFIG["rules"][RULE_ID]["replace"]:
            for src, des in x.items():
                data = data.replace(src, des)
    except Exception as e:  # 捕捉访问异常，一般为timeout，信息在e中
        print(traceback.format_exc())
        return None
    return data


def save_txt(name, data, mode='a'):
    with open(name, mode, encoding='utf8') as f:
        f.write(data)


def scrape(chapter_info, server_url):
    global try_times
    h, c = chapter_info
    if not str(h).startswith("http"):
        h = server_url + h
    p = get_chapter(h, CONFIG["rules"][RULE_ID]["chapter_content"])
    if p == None and try_times > 0:
        print("retry downloading:%s %s" % (c, h))
        try_times -= 1
        _, p = scrape(chapter_info, server_url)
    if p == None:
        print("downloaded %s failed. %s" % (c, h))
        p = ""
    return (c, p)


def download_novel(url_entry):
    global RULE_ID
    server_url = "{0.scheme}://{0.netloc}/".format(urlsplit(url_entry))
    RULE_ID = -1
    for i, info in enumerate(CONFIG["rules"]):
        if server_url == info["site"]:
            RULE_ID = i
            break
    if RULE_ID == -1:
        print("ERR: 系统暂不支持该网站下载，请自行修改配置文件以支持。")
        exit()
    print("RULE:%d" % RULE_ID)
    st = clock()
    html = etree.HTML(urllib.request.urlopen(url_entry).read())
    title = html.xpath(CONFIG["rules"][RULE_ID]["title"])[0].xpath("string(.)")
    author = html.xpath(CONFIG["rules"][RULE_ID]["author"])[0].xpath("string(.)")
    file_name = title + " " + author + ".txt"
    href = html.xpath(CONFIG["rules"][RULE_ID]["chapter_href"])
    capital = html.xpath(CONFIG["rules"][RULE_ID]["chapter_name"])
    save_txt(file_name, title + "\n" + author + "\n", mode='w')
    chapter_info = zip(href, capital)
    print("begin downloading: %s" % file_name)
    pool = Pool(processes=POOLS_SIZE)
    results = pool.starmap(scrape, zip(chapter_info, repeat(server_url))) #todo multi arguments pass in
    pool.close()
    pool.join()
    print('done. used:%f s' % (clock() - st))
    for c, k in results:
        save_txt(file_name, c + "\n" + k + "\n")


if __name__ == '__main__':
    # get_chapter('http://book.zongheng.com/chapter/390021/6494853.html', '//*[@id=\"chapterContent\"]')
    download_novel('http://book.zongheng.com/showchapter/390021.html')
    # download_novel('http://www.aoyuge.com/9/9007/index.html')
