#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 25 16:04:43 2019

@author: dimakarp1996
"""
from collections import defaultdict
from os import getenv
import _pickle as cPickle
import requests
import json
from bs4 import BeautifulSoup
from tqdm import tqdm

from common.utils import get_entities

QUERY_SERVICE_URL = getenv('COBOT_QUERY_SERVICE_URL')
ENTITY_SERVICE_URL = getenv('COBOT_ENTITY_SERVICE_URL')
QA_SERVICE_URL = getenv('COBOT_QA_SERVICE_URL')
API_KEY = getenv('COBOT_API_KEY')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': API_KEY}


def get_name(annotated_phrase, mode='author', return_plain=False):
    if type(annotated_phrase) == str:
        annotated_phrase = {'text': annotated_phrase}
    if mode == 'author':
        class_constraints = [{'dataType': 'aio:Entity', 'value': 'aio:Poet'},
                             {'dataType': 'aio:Entity', 'value': 'aio:BookAuthor'}]
    elif mode == 'book':
        class_constraints = [{'dataType': 'aio:Entity', 'value': 'aio:Book'}]
    else:
        raise Exception('Wrong mode')
    headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': API_KEY}
    named_entities = [annotated_phrase['text']]
    if 'annotations' in annotated_phrase:
        for tmp in get_entities(annotated_phrase, only_named=True, with_labels=False):
            if tmp not in named_entities:
                named_entities.append(tmp)
        for nounphrase in get_entities(annotated_phrase, only_named=False, with_labels=False):
            if nounphrase not in named_entities:
                named_entities.append(nounphrase)
    entityname = None
    for entity in named_entities:
        if entityname is None:
            try:
                answer = requests.request(url=ENTITY_SERVICE_URL, headers=headers,
                                          data=json.dumps({'mention': {'text': entity},
                                                           'classConstraints': class_constraints}),
                                          method='POST').json()
                entityname_plain = answer['resolvedEntities'][0]['value']
                entityname_plain = f'<{entityname_plain}>'
                if return_plain:
                    entityname = entityname_plain
                else:
                    answer = requests.request(
                        url=QUERY_SERVICE_URL, headers=headers, data=json.dumps(
                            {'query': {'text': f'query label|{entityname_plain} <aio:prefLabel> label'}}),
                        method='POST').json()
                    entityname = answer['results'][0]['bindingList'][0]['value']
            except BaseException:
                pass
    return entityname


def get_answer(phrase):
    headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': API_KEY}
    answer = requests.request(url=QA_SERVICE_URL, headers=headers,
                              data=json.dumps({'question': phrase}), method='POST').json()
    return answer['response']


authors = set()
booknames = set()
page0 = 'https://www.goodreads.com/list/show/1.Best_Books_Ever?page='
page1 = 'https://www.goodreads.com/list/show/264.Books_That_Everyone_Should_Read_At_Least_Once?page='
page2 = 'https://www.goodreads.com/list/show/43.Best_Young_Adult_Books?page='
page3 = 'https://www.goodreads.com/list/show/6.Best_Books_of_the_20th_Century?page='
for page_num in tqdm(range(1, 580)):
    urls = [page0 + str(page_num)]
    if page_num < 220:
        urls.append(page1 + str(page_num))
    if page_num < 123:
        urls.append(page2 + str(page_num))
    if page_num < 81:
        urls.append(page3 + str(page_num))
    for url in urls:
        data = requests.get(url)
        content = BeautifulSoup(data._content).prettify()
        book_content = content.split('<span aria-level="4" itemprop="name" role="heading">')
        book_content = [tmp.split('</span>')[0].strip() for tmp in book_content]
        author_content = content.split('<span itemprop="name">')
        author_content = [tmp.split('</span>')[0].strip() for tmp in author_content]
        booknames.update(set(book_content))
        authors.update(set(author_content))
authors = set(authors)
author_names = dict()
author_books = defaultdict(list)
for author in tqdm(authors):
    if author not in author_books:
        curr_books = get_answer(f'books of {author}')
        plain_author = get_name(author, 'author', return_plain=True)
        author_names[plain_author] = author
        author_books[author] = curr_books
cPickle.dump((author_names, author_books), open('author_namesbooks.pkl', 'wb'))
