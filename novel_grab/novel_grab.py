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
from multiprocessing import Pool
import multiprocessing
from time import clock
import zipfile
import os  # remove file
import pkgutil  # 必须采用pkgutil.get_data才能读取egg格式包中的数据
import sys  # stdout flush
from functools import partial

SINGLE_THREAD_DEBUG = False
ENABLE_DEBUG_OUTPUT = True


def m_print(s):
    if ENABLE_DEBUG_OUTPUT:
        print(s)


sites_config = None
try:
    sites_config = json.loads(pkgutil.get_data("novel_grab", 'grab_config.json').decode('utf-8'))
except IOError as e:
    m_print("[error] %s" % e)
    exit()


def extract_data(selector, xpath):
    return selector.xpath(xpath)


def get_rule_id(url_entry):
    rule_id = -1
    server_url = "{0.scheme}://{0.netloc}/".format(urlsplit(url_entry))
    for i, info in enumerate(sites_config["sites"]):
        if server_url == info["site"]:
            rule_id = i
            m_print("[debug] match config %s with rule %s" % (server_url, rule_id))
            break
    return rule_id, server_url


def get_content(url, TRY_TIMES, charset):
    try:
        f = urllib.request.urlopen(url)
        TRY_TIMES = 10
        return etree.HTML(f.read().decode(charset))
    except UnicodeDecodeError as ude:
        m_print("[error] decode error %s" % url)
        m_print("[debug] info %s" % ude)
    except urllib.error.URLError or TimeoutError:  # 捕捉访问异常，一般为timeout，信息在e中
        m_print("[warning] %d retry %s" % (TRY_TIMES, url))
        # m_print(traceback.format_exc())
        TRY_TIMES -= 1
        if TRY_TIMES > 0:
            return get_content(url, TRY_TIMES, charset)
    return None


def get_chapter(url, site_args):
    try:
        s = get_content(url)
        if s is None:
            return
        c = extract_data(s, site_args["chapter_content"])[0]
        # raw elements of div filter none text element
        # support two type, div//p/text div/text
        raw_txt = [x.xpath("text()") for x in c.xpath(site_args["chapter_content"])]
        if len(raw_txt) > 1:
            raw_txt = [x[0] for x in raw_txt]
        else:
            raw_txt = raw_txt[0]
        # remove some strange blank.
        data = "\n".join([t.strip() for t in raw_txt])
        # data = data.replace('\xa0', '')
        for x in site_args["replace"]:
            for src, des in x.items():
                data = data.replace(src, des)
    except TimeoutError:  # 捕捉访问异常，一般为timeout，信息在e中
        m_print("[error] %s" % url)
        return None
    return data


def crawler(site_args, chapter_info):
    h, c = chapter_info
    p = get_chapter(h, site_args)
    if p is None:
        m_print("[error] downloaded %s failed. %s" % (c, h))
        p = "download error, failed at %s" % h
    # else:
    #     m_print("[debug] downloaded %s" % c)
    return c, p


class Downloader(multiprocessing.Process):
    TRY_TIMES = 99
    site_args = {}
    items = {}

    def __init__(self):
        multiprocessing.Process.__init__(self)
        print("[debug] processor %s initialized" % multiprocessing.current_process())

    def get_novel_info(self, url_entry):
        html = get_content(url_entry, self.TRY_TIMES, self.site_args["charset"])
        self.items["title"] = extract_data(html, self.site_args["title"])[0].xpath("string(.)")
        if not self.items["title"]:  # []
            m_print("[error] grab title pattern can't match.")
            return
        self.items["author"] = extract_data(html, self.site_args["author"])[0].xpath("string(.)")
        if not self.items["author"]:  # []
            m_print("[error] grab author pattern can't match.")
            return
        chapter_name = extract_data(html, self.site_args["chapter_name"])
        if not chapter_name:  # []
            m_print("[error] grab chapter links pattern can't match.")
            return
        chapter_href = extract_data(html, self.site_args["chapter_href"])
        if not chapter_href:  # []
            m_print("[error] grab chapter links pattern can't match.")
            return

        if not str(chapter_href[0]).startswith("http"):  # not absolute link
            chapter_href = [self.items["server_url"] + h for h in chapter_href]

        m_print("[debug] novel_info %s downloaded." % url_entry)
        m_print("[debug] title:%s" % self.items["title"])
        m_print("[debug] author:%s" % self.items["author"])
        m_print("[debug] chapters:%d" % len(chapter_name))
        return zip(chapter_href, chapter_name)

    def download(self, url_entry):
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
        # server_vars = Manager()
        # self.rule_id = server_vars.Value('i', -1)
        rule_id, server_url = get_rule_id(url_entry)
        if rule_id < 0:
            m_print("[error] 系统暂不支持该网站下载，请自行修改配置文件以支持。")
            exit()
        self.site_args = sites_config["sites"][rule_id]
        with Pool(processes=int(self.site_args["pool_size"])) as pool:
            if url_entry.endswith("/"):  # for some relative href site
                server_url = url_entry
            self.items["server_url"] = server_url
            chapters = self.get_novel_info(url_entry)
            st = clock()
            m_print("[debug] downloading: %s" % self.items["title"])
            func = partial(crawler, self.site_args)
            if not SINGLE_THREAD_DEBUG:
                results = []
                zip_len = len(list(chapters))
                gi = pool.imap(func, chapters)
                for i in range(zip_len):
                    results.append(gi.next())
                    if i % self.site_args["pool_size"] == 0:
                        m_print("\r[debug] downloading progress %.2f%%" % ((i + 1) * 100 / zip_len), end="")
                        # sys.stdout.flush()

            else:
                results = []
                for hc in list(self.items["chapter_info"])[:10]:
                    results.append(self.crawler(hc))
            m_print('\r[debug] download done. used:%f s' % (clock() - st))
            self.create_zip_file(results, method=zipfile.ZIP_LZMA)
            m_print('[debug] all done.')
            exit()

    # zip the file, ZIP_LZMA use lot of memory,
    def create_zip_file(self, results, method=zipfile.ZIP_DEFLATED):
        m_print('[debug] saving...')
        raw_file_name = "%s %s.txt" % (self.items["title"], self.items["author"])
        zip_file_name = "%s %s.7z" % (self.items["title"], self.items["author"])
        save_txt(raw_file_name, self.items["title"] + "\n" + self.items["author"] + "\n", mode='w')
        for c, k in results:
            save_txt(raw_file_name, c + "\n" + k + "\n\n")
        zf = zipfile.ZipFile(zip_file_name, 'w', method)  # zipfile.ZIP_LZMA
        zf.write(raw_file_name)
        zf.close()
        os.remove(raw_file_name)
        m_print('[debug] saved to [%s]' % zip_file_name)


def save_txt(name, data, mode='a'):
    with open(name, mode, encoding='utf8') as f:
        f.write(data)


def test():
    d = Downloader()
    d.download('http://book.zongheng.com/showchapter/403749.html')
    # download('http://www.quanshu.net/book/67/67604/')
    # download('http://book.zongheng.com/showchapter/390021.html')
    # download('http://www.aoyuge.com/14/14743/index.html')
    # download('http://www.quanshu.net/book/38/38215/')


'''
usage:
download("your novel chapter lists page link")
'''
if __name__ == '__main__':
    test()
else:
    # m_print(download.__doc__)
    pass
