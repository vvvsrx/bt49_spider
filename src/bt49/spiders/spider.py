# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from scrapy.selector import Selector, HtmlXPathSelector
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request
#from scrapy.linkextractors.sgml import SgmlLinkExtractor
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request, FormRequest, HtmlResponse
import urlparse
import string
import re
import codecs
import sys
import os
from os.path import dirname
from bt49.items import *


path = dirname(dirname(dirname(os.path.abspath(os.path.dirname(__file__)))))
sys.path.append(path)


class BT49Spider(CrawlSpider):
    name = "bt49"
    allowed_domains = ["87lou.com"]
    start_urls = [
        "http://www.87lou.com/forum-%d-1.html" % d for d in range(2, 104)
    ]
    rules = (
        Rule(LinkExtractor(allow=('/thread-\d+-1-1.html', )),
             callback='parse_page', follow=True),
    )

    def start_requests(self):
        return [Request("http://www.87lou.com/member.php?mod=logging&action=login", meta={'cookiejar': 1}, callback=self.post_login)]

    def post_login(self, response):
        print 'Preparing login'
        hxs = Selector(response)
        actionUrl = hxs.xpath('//form[@name="login"]/@action').extract()[0]
        formhash = hxs.xpath('//input[@name="formhash"]/@value').extract()[0]
        print formhash
        return [FormRequest.from_response(response, formname="login",
                                          meta={'cookiejar': response.meta[
                                              'cookiejar']},
                                          formdata={
                                              'formhash': formhash,
                                              'username': 'username',
                                              'password': 'password',
                                              'referer': 'http://www.87lou.com/',
                                              'questionid': '0',
                                              'answer': ''
                                          },
                                          callback=self.after_login,
                                          dont_filter=True
                                          )]

    def _requests_to_follow(self, response):
        if not isinstance(response, HtmlResponse):
            return
        seen = set()
        for n, rule in enumerate(self._rules):
            links = [l for l in rule.link_extractor.extract_links(
                response) if l not in seen]
            if links and rule.process_links:
                links = rule.process_links(links)
            for link in links:
                seen.add(link)
                r = Request(url=link.url, callback=self._response_downloaded)

                r.meta.update(rule=n, link_text=link.text,
                              cookiejar=response.meta['cookiejar'])
                yield rule.process_request(r)

    def after_login(self, response):
        for url in self.start_urls:
            yield Request(url, meta={'cookiejar': response.meta['cookiejar']})

    def parse_List(self, response):
        hxs = Selector(response)
        
        pass

    def parse_page(self, response):
        print '############################# Start #####################################'
        threadModel = ThreadItem()
        print '-------------thread---------------'
        pattern = re.compile(r'\d+')
        thread = pattern.findall(response.url)[1]
        print thread
        threadModel["threadId"] = thread
        hxs = Selector(response)
        titles = hxs.xpath('//h1/a/text()').extract()
        print '-------------titles---------------'
        for title in titles:
            print title
        threadModel["titles"] = titles
        breadCrumbs = hxs.xpath('//*[@id="pt"]/div/a/text()').extract()
        breadCrumbs = breadCrumbs[2:len(breadCrumbs) - 1]
        threadModel["breadCrumbs"] = breadCrumbs
        locks = hxs.xpath('///div[@class="locked"]/text()').extract()
        if len(locks) > 0:
            print '-------------locks---------------'
            for lock in locks:
                print lock
        #files = hxs.xpath('//span[re:test(@id, "attach_\d*")]/a/@href').extract()
        showhides = hxs.xpath('//div[@class="showhide"]')
        files = []
        files = hxs.xpath('//div[@class="showhide"]//a/@href').extract()
        for i, f in enumerate(files):
            if f == 'javascript:;':
                del files[i]

        if len(files) > 0:
            pass
        elif len(showhides.extract()) > 0:
            hideText = showhides.xpath('text()').extract()[0].strip()
            if hideText.startswith('thunder') or hideText.startswith('ed2k') or hideText.startswith('magnet'):
                files.append(hideText)
        else:
            files = hxs.xpath(
                '//span[re:test(@id, "attach_\d*")]/a/@href').extract()

            if len(files) == 0:
                allLinkTag = hxs.xpath('//a')
                for linkTag in allLinkTag:
                    allText = linkTag.xpath('text()').extract()
                    if len(allText) > 0:
                        linkText = linkTag.xpath('text()').extract()[0]
                        if len(linkText) > 0:
                            linkText = linkText.strip()
                            if linkText.endswith('torrent'):
                                files.append(linkTag.xpath(
                                    '@href').extract()[0])

        passwords = []
        if len(showhides.extract()) > 0:
            hideTexts = showhides.xpath('text()').extract()
            if len(hideTexts) > 0:
                for ht in hideTexts:
                    if u'\u5bc6\u7801' in ht:
                        passwords.append(ht.strip())

        if len(passwords) > 0:
            threadModel["passwords"] = passwords

        if len(files) > 0:
            print '-------------breadCrumbs---------------'
            for breadCrumb in breadCrumbs:
                print breadCrumb
            print '-------------files---------------'
            threadModel["files"] = files
            for file in files:
                if file.strip().startswith('http://www.87lou.com/forum.php?mod=attachment'):
                    yield Request(file, meta={'thread': thread}, callback=self.download)
                    pass
                print file

        print '############################# End #####################################'
        print ''
        yield threadModel

    def download(self, response):
        threadFile = ThreadFile()
        threadFile['threadId'] = response.meta['thread']
        attachment = response.headers['Content-Disposition']
        pattern = re.compile(r'filename="(.+)"')
        filename = pattern.findall(codecs.decode(attachment, 'gbk'))[0]
        threadFile['fileName'] = filename
        threadFile['fileString'] = response.body
        return threadFile
        #filepath = '%s/%s' % (self.settings['DIR_PATH'],filename)
        # with open(filepath, 'wb') as handle:
        #    handle.write(response.body)
