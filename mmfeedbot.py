import requests,feedparser
import pandas as pd
import os
from module import MyHTMLStripper
import json

class Tweetbot:
	def __init__(self):
		self.urltype = {"twitrss":0,"queryfeed":1}

	def getFeed(self,rss_data):
		feed = feedparser.parse(rss_data.content)
		entries = pd.DataFrame(feed.entries)
		return entries

	def reformatEntry(self,entry,urltype):
		idx = entry.index.min()
		if urltype == self.urltype['queryfeed']:
			entry['author'] = entry.title[idx].split()[0]
			entry['author_detail'] = entry.title[idx].split()[0]
			entry['authors'] = entry.title[idx].split()[0]
		return entry


	def getNewFeed(self,rss_data,already_print_feeds,urltype):
		feeds_info = []
		feed = feedparser.parse(rss_data.content)
		entries = pd.DataFrame(feed.entries)

		if already_print_feeds.empty:
			new_entries = entries
		else:
			new_entries = entries[~entries['id'].isin(already_print_feeds['id'])]
		if not new_entries.empty:
			for key,row in new_entries.iterrows():
				title = self.getTitle(row,urltype)
				feedinfo = "[**%s**](%s)" % (title,row['link'])
				feeds_info.append(feedinfo)

			new_entries = self.reformatEntry(new_entries,urltype)
			already_print_feeds = pd.concat([already_print_feeds,new_entries])
			#already_print_feeds = already_print_feeds.append(new_entries)
			already_print_feeds = already_print_feeds.reset_index(drop=True)
			print("ditect new entries")
		else:
			print("not found new entries")
		return already_print_feeds,feeds_info

	def abstNewFeed(self,rss_data,already_print_feeds,urltype,filepath):
		entries_all,feeds_info = self.getNewFeed(rss_data,already_print_feeds,urltype)
		self.saveFeed(entries_all,filepath)
		return entries_all,feeds_info

	def saveFeed(self,entry,filepath):
		entry.to_csv(filepath,encoding='utf-8')


	def getTitle(self,entry,urltype):
		if urltype == self.urltype["twitrss"]:
			title = entry['title'].split("http")[0]
			title = title.replace('\n','')
			return title
		elif urltype == self.urltype["queryfeed"]:
			title = entry['summary']
			title = title.replace('\n','')
			title = MyHTMLStripper.MyHtmlStripper(title)
			return title.value.split("http")[0]
		else:
			return None

	def setPostMessage(self,feedinfo,username):
		payload = {
		"text":feedinfo,
		"username":username
		}
		return payload

	def postForMattermost(self,feedinfo):
		mattermosturl = "http://hogehoge/hooks/fugafuga"
		header = {'content-Type':'application/json'}
		username = 'Feed Bot'
		for info in feedinfo:
			payload = self.setPostMessage(info,username)
			try:
				requests.post(mattermosturl,
					headers=header,
					data=json.dumps(payload))
			except requests.exceptions.ProxyError:
				print('proxy error')

	def getRSSData(self,url,proxies):
		print(url)
		rss_data = requests.get(url,proxies=proxies)
		if rss_data.status_code == 404:
			return rss_data,False
		else:
			return rss_data,True

	def getDatabase(self,filepath):
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
		if os.path.exists(filepath):
			already_print_feeds = pd.read_csv(filepath,header=0,index_col=0)
		else:
			already_print_feeds = pd.DataFrame(columns=col_names)
		return already_print_feeds

	def getUrls(self):
		urls = [
		{"twitrss":"http://twitrss.me/twitter_user_to_rss/?user=arxivtimes",
		"queryfeed":"https://queryfeed.net/tw?q=%40arxivtimes"},
    	{"twitrss":"http://twitrss.me/twitter_user_to_rss/?user=A_I_News",
    	"queryfeed":"https://queryfeed.net/tw?q=%40A_I_News"},
		{"twitrss":"http://twitrss.me/twitter_user_to_rss/?user=AI_m_lab",
		"queryfeed":"https://queryfeed.net/tw?q=%40AI_m_lab"},
		]
		return urls

	def getUrlKeyword(self,url):
		for k in self.urltype.keys():
			if k in url:
				return k
		return None

	def scrapeFeeds(self,url,proxies,already_print_feeds,filepath):
		rss_data,status = self.getRSSData(url,proxies)
		kw = self.getUrlKeyword(url)
		entries_all = already_print_feeds
		if status is True and kw is not None:
			entries_all,feedinfo = self.abstNewFeed(rss_data,already_print_feeds,self.urltype[kw],filepath)
			self.postForMattermost(feedinfo)
		else:
			print("404 Error or Undefined url and kw")
		return status,entries_all

	def getProxy(self):
		proxies = {
		"http":"http://username:password@proxy_adress:port/",
		"https":"https://username:password@proxy_adress:port/"
		}
		return proxies

	def mainDebug(self,kw,idx):
		proxies = self.getProxy()
		filepath = "entries.csv"
		already_print_feeds = self.getDatabase(filepath)
		urls = self.getUrls()
		self.scrapeFeeds(urls[idx][kw],proxies,already_print_feeds,filepath)

	def main(self):
		proxies = self.getProxy()
		filepath = "entries.csv"
		already_print_feeds = self.getDatabase(filepath)
		urls = self.getUrls()
		for url in urls:
			for key in list(self.urltype.keys()):
				status,already_print_feeds = self.scrapeFeeds(url[key],proxies,already_print_feeds,filepath)
				if status:
					break
