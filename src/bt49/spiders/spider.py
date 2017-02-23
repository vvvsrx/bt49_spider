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
import logging
import chardet
from bs4 import UnicodeDammit


path = dirname(dirname(dirname(os.path.abspath(os.path.dirname(__file__)))))
sys.path.append(path)


class BT49Spider(CrawlSpider):
    name = "bt49"
    allowed_domains = ["87lou.com"]
    start_urls = [
        "http://www.87lou.com/forum-%d-1.html" % d for d in range(2, 104)
        # "http://www.87lou.com"
        #"http://www.87lou.com/thread-172442-1-1.html"
    ]
    rules = (
        # Rule(LinkExtractor(allow=('/thread-\d+-1-1.html', )),
        #      callback='parse_page', follow=True),
        # Rule(LinkExtractor(allow=('/forum-\d*-\d*.html', )),
        #      callback='parse_forum', follow=True),
    )

    
    def __init__(self, name=None, **kwargs):
        pass

    def start_requests(self):
        logging.info('start')
        return [Request("http://www.87lou.com/member.php?mod=logging&action=login", meta={'cookiejar': 1}, callback=self.post_login)]

    def post_login(self, response):
        logging.info('Preparing login')
        hxs = Selector(response)
        actionUrl = hxs.xpath('//form[@name="login"]/@action').extract()[0]
        formhash = hxs.xpath('//input[@name="formhash"]/@value').extract()[0]
        logging.info(formhash)
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

    def parse(self, response):
        hxs = Selector(response)
        logging.info('forum  ----->' + response.url)
        #tbody[re:test(@id, "stickthread_\d*")]/tr/th/
        urls = hxs.xpath('//a/@href').extract()

        #print 'urls'
        #print urls
        pattern = re.compile('http://www.87lou.com/thread-\d+-1-\d+.html')
        pattern2 = re.compile('http://www.87lou.com/forum-\d+-\d+.html')

        for url in urls:
            m = pattern.match(url)
            if m is not None:
                #print 'Strart thread --->' + m.group()
                yield Request(m.group(), callback=self.parse_thread, meta={'cookiejar': response.meta['cookiejar']})

            m2 = pattern2.match(url)
            if m2 is not None:
                #print 'Strart forum --->' + m2.group()
                yield Request(m2.group(), callback=self.parse, meta={'cookiejar': response.meta['cookiejar']})
            #print 'group'

    def parse_thread(self, response):
        logging.info('############################# Start #####################################')
        threadModel = ThreadItem()
        logging.info('-------------thread---------------')
        pattern = re.compile(r'\d+')
        thread = pattern.findall(response.url)[1]
        logging.info(thread)
        threadModel["threadId"] = thread
        logging.info(response.body)
        hxs = Selector(response)
        titles = hxs.xpath('//h1/a/text()').extract()
        logging.info('-------------titles---------------')
        for title in titles:
            logging.info(title)
        threadModel["titles"] = titles
        breadCrumbs = hxs.xpath('//*[@id="pt"]/div/a/text()').extract()
        breadCrumbs = breadCrumbs[2:len(breadCrumbs) - 1]
        threadModel["breadCrumbs"] = breadCrumbs
        locks = hxs.xpath('///div[@class="locked"]/text()').extract()
        if len(locks) > 0:
            logging.info('-------------locks---------------')
            for lock in locks:
                logging.info(lock)
        #files = hxs.xpath('//span[re:test(@id, "attach_\d*")]/a/@href').extract()
        showhides = hxs.xpath('//div[@class="showhide"]')
        files = []
        files = hxs.xpath('//div[@class="showhide"]//a/@href').extract()
        #for i, f in enumerate(files):
        #    if f == 'javascript:;':
        #        del files[i]
        
        hideTexts = showhides.xpath('text()').extract()

        for i in range(len(files)-1, -1, -1):
            if files[i] == 'javascript:;':
                files.pop(i)

        if len(files) > 0:
            pass
        elif len(showhides.extract()) > 0 and len(hideTexts) > 0:
            hideText = hideTexts[0].strip()
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

        startStrings = ('thunder','ed2k','magnet','magnet','https://pan.baidu.com','http://pan.baidu.com','http://www.87lou.com/forum.php?mod=attachment','http://duwude.ctfile.com')

        allHref = hxs.xpath('//a/@href').extract()

        for link in allHref:
            if link.lower().startswith(startStrings):
                files.append(link)
        
        #func = lambda x,y:x if y in x else x + [y]

        #reduce(func, [[], ] + files)

        files = list(set(files))

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
            logging.info('-------------breadCrumbs---------------')
            for breadCrumb in breadCrumbs:
                logging.info(breadCrumb)
            logging.info('-------------files---------------')
            threadModel["files"] = files
            for file in files:
                if file.strip().startswith('http://www.87lou.com/forum.php?mod=attachment'):
                    yield Request(file, meta={'thread': thread}, callback=self.download)
                    pass
                logging.info(file)

        logging.info('############################# End #####################################')
        yield threadModel

    def download(self, response):
        logging.info('Start download ' + response.url)
        threadFile = ThreadFile()
        threadFile['threadId'] = response.meta['thread']
        attachment = response.headers['Content-Disposition']
        logging.info('Chardet result(attachment):')
        logging.info(chardet.detect(attachment))
        logging.info('UnicodeDammit result(attachment):')
        dammit = UnicodeDammit(attachment)
        logging.info(dammit.original_encoding)
        pattern = re.compile(r'filename="(.+)"')

        #fileString = ''
        #chardetResult = chardet.detect(attachment)
        #if chardetResult['confidence'] < 0.7:
        #    dammit = UnicodeDammit(attachment)
        #    fileString = UnicodeDammit(attachment).unicode_markup
        #else:
        #    fileString = attachment.decode(chardetResult['encoding'], 'replace') #codecs.decode(attachment, chardetResult['encoding'])

        #fileString = fileString.encode('utf-8', 'replace')
        filename = pattern.findall(codecs.decode(attachment, 'gbk'))[0]
        logging.info('File name:')
        logging.info(filename)

        blackExt = ('png','jpg','jpeg','gif')
        if not filename.strip().lower().endswith(blackExt) or filename is None or filename == '':
            return
        threadFile['fileName'] = filename
        threadFile['url'] = response.url
        
        logging.info('Chardet result(response.body):')
        logging.info(chardet.detect(response.body))
        logging.info('UnicodeDammit result(response.body):')
        logging.info(UnicodeDammit(response.body).original_encoding)

        threadFile['fileString'] = response.body
        return threadFile
        #filepath = '%s/%s' % (self.settings['DIR_PATH'],filename)
        # with open(filepath, 'wb') as handle:
        #    handle.write(response.body)
