# coding:utf-8
'''
general novel scraper
env:python 3.5
license:MIT
author:winxos
since:2017-02-19
'''
import urllib.request
from lxml import etree
import json
from multiprocessing import Pool
from time import clock

RULE_ID = 0
POOLS_SIZE = 50


# load json config file
def load_config():
    with open('novels_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)


CONFIG = load_config()
replaces = []#after deal novel by user
for x in CONFIG["rules"][RULE_ID]["replace"]:
    for k, v in x.items():
        replaces.append((k, v))

server_url = CONFIG["rules"][RULE_ID]["site"]


def get_chapter(url, loc):
    try:
        c = etree.HTML(urllib.request.urlopen(url).read())
        data = "".join(c.xpath(loc))
        data = data.replace('\xa0', '')
        for src, des in replaces:
            data = data.replace(src, des)
        return data
    except Exception as e:  # 捕捉访问异常，一般为timeout，信息在e中
        print("ERR: " + url)
        return None


def save_txt(name, data, mode='a'):
    with open(name, mode, encoding='utf8') as f:
        f.write(data)


def scrape(chapter_info):
    global finished_count
    h, c = chapter_info
    p = get_chapter(server_url + h, CONFIG["rules"][RULE_ID]["chapter_content"])
    if p == None:
        print("retry downloading:%s" % h)
        _, p = scrape(chapter_info)
    print("%s \t\t\t\t\tdownloaded" % c)
    return (c, p)


def download_novel(url_entry):
    global total_count
    st = clock()
    html = etree.HTML(urllib.request.urlopen(url_entry).read())
    title = "".join(html.xpath(CONFIG["rules"][RULE_ID]["title"]))
    author = "".join(html.xpath(CONFIG["rules"][RULE_ID]["author"]))
    file_name = title + author + ".txt"
    href = html.xpath(CONFIG["rules"][RULE_ID]["chapter_href"])
    capital = html.xpath(CONFIG["rules"][RULE_ID]["chapter_name"])
    save_txt(file_name, title + "\n" + author + "\n", mode='w')
    total_count = len(href)
    chapter_info = zip(href, capital)
    print("begin downloading: %s" % file_name)
    pool = Pool(processes=POOLS_SIZE)
    results = pool.map(scrape, chapter_info)
    pool.close()
    pool.join()
    print('done. used:%f s' % (clock() - st))
    for c, k in results:
        save_txt(file_name, c + "\n" + k + "\n")


if __name__ == '__main__':
    download_novel('http://www.aoyuge.com/9/9007/index.html')
