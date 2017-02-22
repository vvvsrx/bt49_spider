# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class ThreadItem(Item):
    threadId = Field()
    titles = Field()
    breadCrumbs = Field()
    files = Field()
    passwords = Field()


class ThreadFile(Item):
    threadId = Field()
    url = Field()
    fileName = Field()
    fileString = Field()
