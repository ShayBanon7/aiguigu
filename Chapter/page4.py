# ===============================
# 1️⃣ 导入所需模块
# ===============================

import requests
# requests：用于发送 HTTP 请求，获取网页内容

from bs4 import BeautifulSoup
# BeautifulSoup：HTML 解析库，用来提取网页中的数据

from threading import Thread, Lock
# Thread：创建线程
# Lock：线程锁，防止多线程同时操作共享资源

from queue import Queue
# Queue：线程安全的队列，用于线程之间分发任务

import csv
# csv：用于将爬取的数据保存为 CSV 文件

import time
# time：用于延时，防止请求过快被封 IP


# ===============================
# 2️⃣ 全局变量配置
# ===============================

BASE_URL = "http://quotes.toscrape.com/page/{}/"
# 爬虫目标 URL 模板，{} 用于后面格式化页码

NUM_PAGES = 10
# 爬取前 10 页内容

THREADS = 5
# 启动 5 个线程并发爬取

output_file = "quotes.csv"
# 数据保存的 CSV 文件名

lock = Lock()
# 创建线程锁，用于保护写文件、去重等共享资源

queue = Queue()
# 创建任务队列，用来存放待爬取的 URL

seen_quotes = set()
# 使用 set 做去重
# set 查询速度快，适合判断“是否已存在”


# ===============================
# 3️⃣ 爬取单个页面函数
# ===============================

def fetch_page(url):
    """
    负责：请求单个页面
    """
    try:
        # 向目标 URL 发送 GET 请求，设置超时时间 10 秒
        response = requests.get(url, timeout=10)

        # 判断请求是否成功
        if response.status_code == 200:
            # 请求成功，进入页面解析逻辑
            parse_page(response.text)
        else:
            # 请求失败，打印警告信息
            print(f"[WARN] 请求失败: {url} 状态码 {response.status_code}")

    except Exception as e:
        # 捕获请求过程中的异常，防止程序中断
        print(f"[ERROR] 请求异常: {url} {e}")


# ===============================
# 4️⃣ 解析页面数据函数
# ===============================

def parse_page(html):
    """
    负责：解析 HTML，提取数据，并写入 CSV
    """

    # 使用 BeautifulSoup 解析 HTML 字符串
    soup = BeautifulSoup(html, "html.parser")

    # 使用 CSS 选择器，找到所有 class="quote" 的 div
    quotes = soup.select("div.quote")

    # 用于临时存放当前页面解析出的数据
    data_list = []

    # 遍历每一条名言模块
    for quote in quotes:
        # 提取名言文本，并去除首尾空白
        text = quote.select_one("span.text").get_text(strip=True)

        # 提取作者名字
        author = quote.select_one("small.author").get_text(strip=True)

        # 提取标签列表，并转换为字符串列表
        tags = [
            tag.get_text(strip=True)
            for tag in quote.select("div.tags a.tag")
        ]

        # ===============================
        # 去重逻辑
        # ===============================

        # 如果这条名言之前没出现过
        if text not in seen_quotes:
            # 添加到已见集合
            seen_quotes.add(text)

            # 将数据整理成一行
            data_list.append([
                text,
                author,
                ",".join(tags)  # 标签用逗号拼接
            ])

    # ===============================
    # 写入 CSV（加锁）
    # ===============================

    # 多线程写文件必须加锁
    with lock:
        # 以追加模式打开 CSV 文件
        with open(output_file, "a", newline="", encoding="utf-8") as f:
            # 创建 CSV 写入对象
            writer = csv.writer(f)

            # 一次性写入多行数据
            writer.writerows(data_list)


# ===============================
# 5️⃣ 线程工作函数
# ===============================

def worker():
    """
    每个线程执行的任务函数
    """
    # 当队列中还有任务时
    while not queue.empty():
        # 从队列中取出一个 URL
        url = queue.get()

        # 爬取并解析该页面
        fetch_page(url)

        # 标记该任务已完成
        queue.task_done()

        # 延时 1 秒，防止请求过快
        time.sleep(1)


# ===============================
# 6️⃣ 主函数
# ===============================

def main():
    # ===============================
    # 写入 CSV 表头
    # ===============================

    # 使用 w 模式，确保每次运行是全新文件
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # 写入 CSV 表头
        writer.writerow(["Quote", "Author", "Tags"])

    # ===============================
    # 将所有页面 URL 加入队列
    # ===============================

    for i in range(1, NUM_PAGES + 1):
        # 格式化 URL，例如 page/1、page/2 ...
        queue.put(BASE_URL.format(i))

    # ===============================
    # 启动线程
    # ===============================

    threads = []

    for _ in range(THREADS):
        # 创建线程，指定执行 worker 函数
        t = Thread(target=worker)

        # 启动线程
        t.start()

        # 保存线程对象，方便后面 join
        threads.append(t)

    # ===============================
    # 等待队列中的任务全部完成
    # ===============================

    queue.join()
    # 阻塞主线程，直到所有任务被处理完

    # ===============================
    # 等待所有线程结束
    # ===============================

    for t in threads:
        t.join()

    # 程序结束提示
    print("[INFO] 爬取完成！数据已保存到", output_file)


# ===============================
# 7️⃣ 程序入口
# ===============================

if __name__ == "__main__":
    # 只有直接运行该文件时，才执行 main()
    main()
