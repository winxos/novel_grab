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
from multiprocessing.pool import ThreadPool
from threading import Thread
import time
import itertools

ENABLE_DEBUG_OUTPUT = True
OPEN_MULTI_THREAD = False
THREAD_NUMS = 8


def m_print(s, end="\n"):
    if ENABLE_DEBUG_OUTPUT:
        print(s, end=end)


def list_1d_to_2d(li, col):
    row = len(li) // col
    ans = [li[col * i: col * (i + 1)] for i in range(row)]
    if li[col * row:]:
        ans.append(li[col * row:])
    return ans


def list_2d_to_1d(li):
    return list(itertools.chain.from_iterable(li))


def extract_data(selector, xpath):
    return selector.xpath(xpath)


class Downloader:
    site_args = {}
    items = {}
    info = {}

    def __init__(self, url):
        self.info["percent"] = 0
        sites_config = None
        try:
            sites_config = json.loads(pkgutil.get_data("novel_grab", 'grab_config.json').decode('utf-8'))
        except IOError as e:
            m_print("[error] %s" % e)
            exit()
        if not self.get_site_args(url, sites_config):
            exit()
        if not self.get_novel_info(url):
            exit()

    def get_site_args(self, url_entry, sc):
        rule_id = -1
        server_url = "{0.scheme}://{0.netloc}/".format(urlsplit(url_entry))
        for i, info in enumerate(sc["sites"]):
            if server_url == info["site"]:
                rule_id = i
                m_print("[debug] match config %s with rule %s" % (server_url, rule_id))
                break
        if rule_id < 0:
            print("[debug] 该网站暂时不支持")
            return False
        self.site_args = sc["sites"][rule_id]
        if url_entry.endswith("/"):  # for some relative href site
            server_url = url_entry
        self.items["server_url"] = server_url
        return True

    def get_content(self, url, try_times=10):
        try:
            f = urllib.request.urlopen(url)
            return etree.HTML(f.read().decode(self.site_args["charset"]))
        except UnicodeDecodeError as ude:
            m_print("[error] decode error %s" % url)
            m_print("[debug] info %s" % ude)
        except urllib.error.URLError or TimeoutError:  # 捕捉访问异常，一般为timeout，信息在e中
            m_print("[warning] %d retry %s" % (try_times, url))
            # m_print(traceback.format_exc())
            try_times -= 1
            if try_times > 0:
                return self.get_content(url, try_times)
        return None

    def get_chapter(self, url):
        try:
            s = self.get_content(url)
            if s is None:
                return
            c = extract_data(s, self.site_args["chapter_content"])[0]
            # raw elements of div filter none text element
            # support two type, div//p/text div/text
            raw_txt = [x.xpath("text()") for x in c.xpath(self.site_args["chapter_content"])]
            if len(raw_txt) > 1:
                raw_txt = [x[0] for x in raw_txt]
            else:
                raw_txt = raw_txt[0]
            # remove some strange blank.
            data = "\n".join([t.strip() for t in raw_txt])
            # data = data.replace('\xa0', '')
            for x in self.site_args["replace"]:
                for src, des in x.items():
                    data = data.replace(src, des)
        except TimeoutError:  # 捕捉访问异常，一般为timeout，信息在e中
            m_print("[error] %s" % url)
            return None
        return data

    def get_novel_info(self, url_entry):
        html = self.get_content(url_entry)
        self.items["title"] = extract_data(html, self.site_args["title"])[0].xpath("string(.)")
        if not self.items["title"]:  # []
            m_print("[error] grab title pattern can't match.")
            return False
        self.items["author"] = extract_data(html, self.site_args["author"])[0].xpath("string(.)")
        if not self.items["author"]:  # []
            m_print("[error] grab author pattern can't match.")
            return False
        chapter_name = extract_data(html, self.site_args["chapter_name"])
        if not chapter_name:  # []
            m_print("[error] grab chapter links pattern can't match.")
            return False
        chapter_href = extract_data(html, self.site_args["chapter_href"])
        if not chapter_href:  # []
            m_print("[error] grab chapter links pattern can't match.")
            return False

        if not str(chapter_href[0]).startswith("http"):  # not absolute link
            chapter_href = [self.items["server_url"] + h for h in chapter_href]

        m_print("[debug] novel_info %s downloaded." % url_entry)
        m_print("[debug] title:%s" % self.items["title"])
        m_print("[debug] author:%s" % self.items["author"])
        m_print("[debug] chapters:%d" % len(chapter_name))
        self.info["novel_name"] = "%s %s" % (self.items["title"], self.items["author"])
        self.items["chapters"] = zip(chapter_href, chapter_name)
        return True

    def crawler(self, chapter_info):
        h, c = chapter_info
        p = self.get_chapter(h)
        if p is None:
            m_print("[error] downloaded %s failed. %s" % (c, h))
            p = "download error, failed at %s" % h
        # else:
        #     m_print("[debug] downloaded %s" % c)
        return c, p

    def multi_thread_do_job(self, l, size=THREAD_NUMS):
        tp = ThreadPool(size)
        results = tp.map(self.crawler, l)
        tp.close()
        tp.join()
        return results

    def run(self):
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

        with Pool(processes=multiprocessing.cpu_count() * 2) as pool:

            st = clock()
            m_print("[debug] downloading: %s" % self.items["title"])
            # results = pool.map(self.crawler, chapters)

            tasks = []
            li = list(self.items["chapters"])
            fun = self.crawler
            if OPEN_MULTI_THREAD:
                li = list_1d_to_2d(li, THREAD_NUMS)
                fun = self.multi_thread_do_job
            for i, d in enumerate(li):
                tasks.append(pool.apply_async(fun, args=(d,)))
            pool.close()
            results = []
            for i, r in enumerate(tasks):
                results.append(r.get())
                self.info["percent"] = (i + 1) * 100 / len(tasks)
                if i % multiprocessing.cpu_count() == 0:
                    m_print("\r[debug] downloading progress %.2f%%" % (self.info["percent"]), end="")
            m_print('\r[debug] download done. used:%f s' % (clock() - st))
            if OPEN_MULTI_THREAD:
                results = list_2d_to_1d(results)
            self.create_zip_file(results, method=zipfile.ZIP_LZMA)
            m_print('[debug] all done.')

    def start(self):
        Thread(target=self.run()).start()

    def get_info(self):
        return self.info

    # zip the file, ZIP_LZMA use lot of memory,
    def create_zip_file(self, results, method=zipfile.ZIP_DEFLATED):
        def save_txt(name, data, mode='a'):
            with open(name, mode, encoding='utf8') as f:
                f.write(data)

        m_print('[debug] saving...')
        raw_file_name = self.info["novel_name"] + ".txt"
        zip_file_name = self.info["novel_name"] + ".7z"
        save_txt(raw_file_name, self.items["title"] + "\n" + self.items["author"] + "\n", mode='w')
        for c, k in results:
            save_txt(raw_file_name, c + "\n" + k + "\n\n")
        zf = zipfile.ZipFile(zip_file_name, 'w', method)  # zipfile.ZIP_LZMA
        zf.write(raw_file_name)
        zf.close()
        os.remove(raw_file_name)
        self.info["percent"] = 100
        self.info["file_name"] = zip_file_name
        m_print('[debug] saved to [%s]' % zip_file_name)


def test():
    d = Downloader('http://book.zongheng.com/showchapter/403749.html')
    d.start()
    # while d.get_info()["percent"] < 100:
    #     print("\rDownloaded %.2f" % d.get_info()["percent"], end="")
        # time.sleep(1)
        # d.download('http://www.quanshu.net/book/67/67604/')
        # d.download('http://book.zongheng.com/showchapter/390021.html')
        # d.download('http://www.aoyuge.com/14/14743/index.html')
        # download('http://www.quanshu.net/book/38/38215/')
    print(d.get_info())

'''
usage:
    d = Downloader('http://book.zongheng.com/showchapter/403749.html')
    d.start()
    print(d.get_info())
'''
if __name__ == '__main__':
    test()
else:
    # m_print(download.__doc__)
    pass
