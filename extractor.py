'''
Basic Function:
Fetch BairesDev Jobs (https://jobs.bairesdev.com/data/BairesDevjobposting.xml)
Foreach job check if the job is saved on db
If is not open a thread to fetch jobs data https://applicants.bairesdev.com/api/JobPosting?JobPostingId=XXXXXXXXXXXX and https://applicants.bairesdev.com/api/Job?JobOfferId=XXXXXXXXXXXX
wait 2 seconds tops to fetch the data
Format the rss xml filling 
'''

import boto3
import requests

from datetime import datetime
from lxml import etree

from FetchThread import FetchThread

filter_query = None
debug_log = ''
debug_enable = None
all_qualities = None


def debug(*args):
    if not debug_enable:
        return
    global debug_log
    now = datetime.now()
    to_print=''
    for data in args:
        to_print += f' {str(data)}'
        
    print(f'[DEBUG][{now}]', to_print)
    debug_log += f'[DEBUG]{now}{to_print}\n'


def downloadURLpage():
    debug('downloadURLpage')
    mainURL = 'https://jobs.bairesdev.com/data/BairesDevjobposting.xml'

    debug('url', mainURL)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"}
    req  = requests.get(mainURL, headers=headers, timeout=2.001)

    status = req.status_code
    debug(f'status:{status}')

    return status, req.text


def parse_rss_with_lxml(content):
    debug('parse_rss_with_lxml')
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    tree = etree.fromstring(content)
    debug('tree')
    entries = tree.xpath("//item")
    debug('entries')
    return [{
        "id": item.findtext("id")
        , "title": item.findtext("title")
        , "shortDesc": item.findtext("shortdescription")
        , "technology": item.findtext("technology")
        , "area": item.findtext("area")
        , "link": item.findtext("joburl")
    } for item in entries]


def extractFromRSS(rss):
    if not rss:
        return None
    debug('extractFromRSS')
    items = parse_rss_with_lxml(rss)
            
    return items


def getMoreData(elements):
    if not elements:
        return None
    debug('getMoreData')

    table = boto3.resource('dynamodb').Table('BairesDevJobs')  

    threads = [FetchThread(ele,table) for ele in elements]
    [t.start() for t in threads]
    [t.join(2) for t in threads]

    items = []
    i=0
    for t in threads:
        i=i+1
        debug(f'thread:{i}')
        id = t['id']
        element = t['data']

        description = f"""<![CDATA[ Area: {element.get('area')}<BR>
        Technology: {element.get('technology')}<BR>
        Description: {element.get('description')}]]>
        """
        temp = {
            'title': element.get('title'),
            'link': f"<![CDATA[{element.get('link')}]]>",
            'description': description,
            'category': element.get('area'),
            'guid': id,
            'pubDate': element.get('postDate') ,
            'source': '<![CDATA[https://jobs.bairesdev.com/data/BairesDevjobposting.xml]]>',
        }
        items.append(temp)
    return items


def montaXML(items, now = None, title = None, link = None):
    debug('montaXML')
    if not now:
        now = datetime.now().astimezone().strftime('%a, %d %b %Y %H:%M:%S %z')
    if not title:
        title = 'Job RSS'
    if not link:
        link = 'https://findMyJob.com/:)'

    conteudo = ''
    for item in items:
        conteudo += '    <item>\n'
        for key, value in item.items():
            if value:
                conteudo += f'		    <{key}>{value}</{key}>\n'
            else:
                conteudo += f'          <{key} />\n'
        conteudo += '    </item>\n'
            
    text = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:torrent="http://xmlns.ezrss.it/0.1/">
    <channel>
        <title>{title}</title>
        <link><![CDATA[{link}]]></link>
        <description>RSS Job feed</description>
        <lastBuildDate>{now}</lastBuildDate>\n{conteudo}    </channel>
</rss>
'''
    return text


def getItemsFromBairesDev():
    debug(f'getItemsFromBairesDev')
    status, webpage = downloadURLpage()
    debug(f'got downloadURLpage result')
    if status != 200:
        print('WARNING: Falha ao fazer o download da pagina')
        debug(f'status:{status}')
        debug(f'webpage:{webpage}')
        return None, status
    
    items = extractFromRSS(webpage)

    return items, status


def filterItems(items):
    debug('filterItems')

    temp = []
    try:
        i = 0
        for item in items:
            if filter_query in str(item.get('title')).lower() or \
                filter_query in str(item.get('shortDesc')).lower() or\
                filter_query in str(item.get('technology')).lower() or\
                filter_query in str(item.get('area')).lower():
                temp.append(item)
    except Exception as e:
        debug(f'Aborting filterEpisode:{e}')
        return items

    return temp        
  

def main(param, arg = {}):

    global filter_query
    global debug_enable
    global debug_log
    debug_log = ''

    debug_enable = param.get('debug')
    filter_query = param.get('rawPath')
    debug(f'arg:{arg}')
    
    status = 200
    items, status = getItemsFromBairesDev()

    if not items:
        return 503, 'Fail to get Jobs XML'
    debug(f'Full Items Lenght:{len(items)}')

    if filter_query:
        items = filterItems(items)
        debug(f'Filtered Items Lenght:{len(items)}')

    items = getMoreData(items)
    xml = montaXML(items, title = f'BairesDev RSS Filter:{filter_query}', link = 'https://jobs.bairesdev.com')
    if not xml:
        status = 500
        text = 'Falha ao montar XML'
    else:
        text = xml

    debug('Done')
    return status, debug_log + text
