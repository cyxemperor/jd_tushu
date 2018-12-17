import scrapy
from scrapy_redis.spiders import RedisSpider
from copy import deepcopy


class DangdangSpider(RedisSpider):
    name = 'dangdang'
    allowed_domains = ['dangdang.com']
    info_str = '[ *] 如果需要启动amazon爬虫，请在配置的redis中执行：\n lpush dangdang "http://book.dangdang.com/" \n[ *] 请输入任意继续执行本程序'
    input(info_str)
    # start_urls = ['http://book.dangdang.com/']
    # lpush dangdang 'http://book.dangdang.com/'
    redis_key = "dangdang"

    def parse(self, response):
        #获取大分类分组
        div_list = response.xpath("//div[@class='con flq_body']/div")[1:-1]
        for div in div_list:
            item = {}
            #大分类的名字
            item["b_cate"] = div.xpath(".//dl[contains(@class,'primary_dl')]/dt//text()").extract()
            #获取中间分类的分组
            dl_list = div.xpath(".//dl[@class='inner_dl']")
            for dl in dl_list:
                #中间分类的名字
                item["m_cate"] = dl.xpath("./dt//text()").extract()
                #获取小分类的分组
                a_list = dl.xpath("./dd/a")
                for a in a_list:
                    #小分类的名字
                    item["s_cate"] = a.xpath("./text()").extract_first()
                    item["s_href"] = a.xpath("./@href").extract_first()
                    #发送小分类URL地址的请求，达到列表页
                    yield scrapy.Request(
                        item["s_href"],
                        callback=self.parse_book_list,
                        meta = {"item":deepcopy(item)}
                    )

    def parse_book_list(self,response): #提取列表页的数据
        item = response.meta["item"]
        #获取列表页图书的分组
        li_list = response.xpath("//ul[@class='bigimg']/li")
        for li in li_list:
            item["book_name"] = li.xpath("./a/@title").extract_first()
            item["book_href"] = li.xpath("./a/@href").extract_first()
            item["book_author"] = li.xpath(".//p[@class='search_book_author']/span[1]/a/text()").extract()
            item["book_press"] = li.xpath(".//p[@class='search_book_author']/span[3]/a/text()").extract_first()
            item["book_desc"] = li.xpath(".//p[@class='detail']/text()").extract_first()
            item["book_price"] = li.xpath(".//span[@class='search_now_price']/text()").extract_first()
            item["book_store_name"] = li.xpath(".//p[@class='search_shangjia']/a/text()").extract_first()
            item["book_store_name"] = "当当自营" if item["book_store_name"] is None else item["book_store_name"]
            yield item

        #实现列表页翻页
        next_url = response.xpath("//li[@class='next']/a/@href").extract_first()
        if next_url is not None:
            #构造翻页请求
            yield response.follow(
                next_url,
                callback = self.parse_book_list,
                meta = {"item":item}
            )
book/spiders/amazon.py

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy_redis.spiders import RedisCrawlSpider
import re


class AmazonSpider(RedisCrawlSpider):
    name = 'amazon'
    allowed_domains = ['amazon.cn']
    info_str = '[ *] 如果需要启动amazon爬虫，请在配置的redis中执行：\n lpush amazon "https://www.amazon.cn/%E5%9B%BE%E4%B9%A6/b/ref=sd_allcat_books_l1?ie=UTF8&node=658390051" \n[ *] 请输入任意继续执行本程序'
    input(info_str)
    # start_urls = ['https://www.amazon.cn/%E5%9B%BE%E4%B9%A6/b/ref=sd_allcat_books_l1?ie=UTF8&node=658390051']
    # lpush amazon 'https://www.amazon.cn/%E5%9B%BE%E4%B9%A6/b/ref=sd_allcat_books_l1?ie=UTF8&node=658390051'
    redis_key = "amazon"

    rules = (
        #实现提取大分类的URL地址,同时提取小分类的url地址
        Rule(LinkExtractor(restrict_xpaths=("//ul[contains(@class,'a-unordered-list a-nostyle a-vertical s-ref-indent-')]/div/li",)), follow=True),
        Rule(LinkExtractor(restrict_xpaths=("//ul[@class='a-unordered-list a-nostyle a-vertical s-ref-indent-two']/div/li",)), follow=True),

        # 实现提取图书详情页的url地址
        Rule(LinkExtractor(restrict_xpaths=("//div[@id='mainResults']/ul/li//h2/..",)), callback="parse_item"),
        #实现列表页的翻页
        Rule(LinkExtractor(restrict_xpaths=("//div[@id='pagn']//a",)),follow=True),
    )

    def parse_item(self, response):
        item = {}
        item["book_name"] = response.xpath("//span[contains(@id,'roductTitle')]/text()").extract_first()
        item["book_author"] = response.xpath("//div[@id='bylineInfo']/span[@class='author notFaded']/a/text()").extract()
        item["book_press"] = response.xpath("//b[text()='出版社:']/../text()").extract_first()
        item["book_cate"] = response.xpath("//div[@id='wayfinding-breadcrumbs_feature_div']/ul/li[not(@class)]//a/text()").extract()
        item["book_url"] = response.url
        item["book_desc"] = re.findall(r"\s+<noscript>(.*?)</noscript>\n  <div id=\"outer_postBodyPS\"",response.body.decode(),re.S)[0]
        # item["book_img"] = response.xpath("//div[contains(@id,'img-canvas')]/img/@src").extract_first()
        item["is_ebook"] = "Kindle电子书" in response.xpath("//title/text()").extract_first()
        if item["is_ebook"]:
            item["ebook_price"] = response.xpath("//td[@class='a-color-price a-size-medium a-align-bottom']/text()").extract_first()
        else:
            item["book_price"]= response.xpath("//span[contains(@class,'price3P')]/text()").extract_first()

        yield item
book/pipelines.py

import re

class DangDangPipeline(object):
    def process_item(self, item, spider):
        if spider.name == "dangdang":
            item["b_cate"] = "".join([i.strip() for i in item["b_cate"]])
            item["m_cate"] = "".join([i.strip() for i in item["m_cate"]])
            print(item)
        return item


class AmazonPipline:
    def process_item(self,item,spider):
        if spider.name == "amazon":
            item["book_cate"] = [i.strip() for i in item["book_cate"]]
            item["book_desc"] = item["book_desc"].split("<br><br>")[0].split("<br>")
            item["book_desc"] = [re.sub("<div>|</div>|<em>|</em>|\s+|\xa0|<p>|</p>","",i) for i in item["book_desc"]]
            print(item)
        return item