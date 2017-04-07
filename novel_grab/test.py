# coding:utf8
# multi processing with multi thread demo using python3
# winxos 2017-04-07
from time import sleep, clock
from multiprocessing import Pool, Manager, freeze_support
import multiprocessing
from multiprocessing.pool import ThreadPool
import itertools, os

threads_number = 20


def do_job(i, n):
    # sleep(1)
    print(os.getpid())
    return n * i.value


def multi_thread_do_job(l, func=do_job, size=threads_number):
    tp = ThreadPool(size)
    results = tp.map(func, l)
    tp.close()
    tp.join()
    return results


# def multi_processing_multi_thread_do_job(l, func=multi_thread_do_job, processes_num=multiprocessing.cpu_count() * 2):
#     pool = Pool(processes=processes_num)
#     ans = pool.map(func, list_1d_to_2d(l, threads_number))
#     pool.close()
#     pool.join()
#     return list_2d_to_1d(ans)


def list_1d_to_2d(li, col):
    row = len(li) // col
    ans = [li[col * i: col * (i + 1)] for i in range(row)]
    if li[col * row:]:
        ans.append(li[col * row:])
    return ans


def list_2d_to_1d(li):
    return list(itertools.chain.from_iterable(li))


class A(object):
    def __init__(self, *args, **kwargs):
        # do other stuff
        self.id = 5

    def multi_thread_do_job(self, l, size=threads_number):
        tp = ThreadPool(size)
        results = tp.map(self.do_something, l)
        tp.close()
        tp.join()
        return results

    def do_something(self, i):
        sleep(0.2)
        return i * self.id

    def run(self):
        pool = Pool(processes=4)
        l = [i for i in range(100)]
        ans = pool.map(self.multi_thread_do_job, list_1d_to_2d(l, threads_number))
        return ans


if __name__ == "__main__":
    # freeze_support()
    st = clock()
    li = [i for i in range(10)]

    a = A()
    print(a.run())
    # a = multi_thread_do_job(li,func=func)
    # a = multi_processing_multi_thread_do_job(li, func=func)
    print("time used: %.2fs" % (clock() - st))
