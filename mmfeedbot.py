import requests
import feedparser
import pandas as pd
import os
from module import MyHTMLStripper
import json


class Tweetbot:
    def __init__(self):
        self.mattermosturl = "http://hogehoge/hooks/fugafuga"
        self.urltype = {"twitrss": 0, "queryfeed": 1}
        self.proxies = {
            "http": "http://username:password@proxy_adress:port/",
            "https": "https://username:password@proxy_adress:port/"
        }
        self.urls = [
            {
                "twitrss": "http://twitrss.me/twitter_user_to_rss/?user=arxivtimes",
                "queryfeed": "https://queryfeed.net/tw?q=%40arxivtimes"
            },
            {
                "twitrss": "http://twitrss.me/twitter_user_to_rss/?user=A_I_News",
                "queryfeed": "https://queryfeed.net/tw?q=%40A_I_News"
            },
            {
                "twitrss": "http://twitrss.me/twitter_user_to_rss/?user=AI_m_lab",
                "queryfeed": "https://queryfeed.net/tw?q=%40AI_m_lab"
            },
        ]
        self.filepath = "entries.csv"
        self.already_print_feeds = getDatabase(self.filepath)

    def createEntries(self, rss_data):
        feed = feedparser.parse(rss_data.content)
        entries = pd.DataFrame(feed.entries)
        return entries

    def reformatEntries(self, entries, urltype):
        '''
        タイトルの先頭の要素をentryに追加する
        splitでtab,spaceを消去します
        '''
        idx = entries.index.min()
        if urltype == self.urltype['queryfeed']:
            entries['author'] = entries.title[idx].split()[0]
            entries['author_detail'] = entries.title[idx].split()[0]
            entries['authors'] = entries.title[idx].split()[0]
        return entries

    def getNewFeed(self, rss_data, urltype):
        feeds_info = []
        entries = self.createEntries(rss_data)

        new_entries = entries[~entries['id'].isin(self.already_print_feeds['id'])]
        
        if not new_entries.empty:
            print("ditect new entries")
            for key,enrty in new_entries.iterrows():
                title = self.getTitle(entry, urltype)
                feedinfo = "[**%s**](%s)" % (title, entry['link'])
                feeds_info.append(feedinfo)
            new_entries = self.reformatEntries(new_entries, urltype)
            all_entries = pd.concat([self.already_print_feeds, new_entries])
            self.already_print_feeds = all_entries.reset_index(drop=True)
        else:
            print("not found new entries")

        return feeds_info

    def abstNewFeed(self, rss_data, urltype):
        feeds_info = self.getNewFeed(
            rss_data,
            urltype
        )
        self.saveFeed(self.already_print_feeds)
        return feeds_info

    def saveFeed(self, entries):
        entries.to_csv(self.filepath,encoding='utf-8')

    def getTitle(self, entry, urltype):
        if urltype == self.urltype["twitrss"]:
            title = entry['title'].split("http")[0]
            title = title.replace('\n', '')
            return title
        elif urltype == self.urltype["queryfeed"]:
            title = entry['summary']
            title = title.replace('\n', '')
            title = MyHTMLStripper.MyHtmlStripper(title)
            return title.value.split("http")[0]
        else:
            return None

    def setPostMessage(self, feedinfo, username):
        payload = {
            "text": feedinfo,
            "username": username
        }
        return payload

    def postToMattermost(self, feedinfo):
        header = {'content-Type': 'application/json'}
        username = 'Feed Bot'
        for info in feedinfo:
            payload = self.setPostMessage(info, username)
            try:
                requests.post(
                    self.mattermosturl,
                    headers=header,
                    data=json.dumps(payload)
                )
            except requests.exceptions.ProxyError:
                print('proxy error')

    def getRSSData(self, url, proxies):
        print(url)
        rss_data = requests.get(url, proxies=proxies)
        if rss_data.status_code == 200:
            return rss_data
        else:
            return None

    def getDatabase(self):
        col_names = [
            'no',
            'author',
            'author_detail',
            'authors',
            'guidislink',
            'id',
            'link',
            'links',
            'published',
            'published_parsed',
            'summary',
            'summary_detail',
            'title',
            'title_detail',
            'twitter_place',
            'twitter_source'
        ]
        if os.path.exists(self.filepath):
            already_print_feeds = pd.read_csv(
                self.filepath,
                header=0,
                index_col=0)
        else:
            already_print_feeds = pd.DataFrame(columns=col_names)
        return already_print_feeds

    def getUrlKeyword(self, url):
        for k in self.urltype.keys():
            if k in url:
                return k
        return None

    def scrapeFeeds(self, url, proxies):
        rss_data = self.getRSSData(url, proxies)
        kw = self.getUrlKeyword(url)
        if (rss_data is not None) and (kw is not None):
            feedinfo = self.abstNewFeed(
                rss_data,
                self.urltype[kw]
            )
            self.postToMattermost(feedinfo)
            return True
        else:
            print("404 Error or Undefined url and kw")
            return False

    def runDebug(self, kw, idx):
        self.scrapeFeeds(
            self.urls[idx][kw],
            self.proxies
        )

    def run(self):
        for url in urls:
            for key in list(self.urltype.keys()):
                status = self.scrapeFeeds(
                    self.url[key],
                    self.proxies
                )
                if status:
                    print('finish update database')
                    break
