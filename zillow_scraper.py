# https://www.geeksforgeeks.org/scrape-content-from-dynamic-websites/
import json 
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.firefox import GeckoDriverManager
import time
from datetime import date, datetime
from os import listdir
from os.path import isfile, join
import smtplib
import ssl

ssl.SSLContext.verify_mode = ssl.VerifyMode.CERT_OPTIONAL

class Home:
	def __init__(self, address, beds = None, baths = None, price = None):
		self.address = address
		self.beds = beds
		self.baths = baths
		self.price = price
		self.price_int = 0
		try:
			price_cleaned = price.replace("+/mo","").replace("$","").replace("/mo","").replace("+","").replace(",","")
			self.price_int = int(price_cleaned)
		except:
			pass

	def __str__(self):
		return ("Address:{}\tBeds:{}\tBaths:{}\tPrice:{}\tParsed_Price:{}".format(self.address, self.beds, self.baths, self.price, self.price_int))

	def __hash__(self):
		return hash((self.address, self.price))

	def __eq__(self, other):
		return self.address == other.address and self.price == other.price

def load_most_recent_snapshot():
	onlyfiles = sorted([f for f in listdir(".") if isfile(join(".", f)) and "homes" in f], reverse = True)
	if len(onlyfiles) == 0:
		return []

	most_recent_file = onlyfiles[0]

	snapshot = []

	with open(most_recent_file) as f:
		for line in f:
			address, beds, baths, price, price_int = map(lambda x: x.split(":")[1],line.strip().split("\t"))
			beds = None if beds == "None" else beds
			baths = None if baths == "None" else baths
			price = None if price == "None" else price
			price_int = eval(price_int)
			home = Home(address, beds, baths, price)
			snapshot.append(home)

	return snapshot

def save_current_snapshot(snapshot):
	now = datetime.now()
	now_str = now.strftime("%Y-%d-%m_%H-%M")

	with open("homes_{}.txt".format(now_str), "w") as f:
		for h in snapshot:
			f.write(str(h)+"\n");





def __notify_via_email(diff):
	try:
		gmail_user = 'hsyalexliu0809@gmail.com'
		gmail_password = 'lflnvmvsiygoxcbe' # nskvcsxdvnthjxkk for linux

		server = smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ssl._create_unverified_context())
		server.ehlo()  # Can be omitted
		server.login(gmail_user, gmail_password)

		sent_from = gmail_user
		to = ['e7liu@eng.ucsd.edu',]
		subject = 'New House Posted'
		body = "New Posts:\r\n"
		for d in diff:
			body += str(d) + "\r\n"
		
		email_text =  "\r\n".join([
		"From: {}".format(sent_from),
		"To: {}".format(", ".join(to)),
		"Subject: New Home Posted",
		"",
		"{}".format(body)
		])

		server.sendmail(sent_from, to, email_text)
		server.quit()

	except Exception as e:
		print('Something went wrong:{}'.format(e))

def compare_notify(current_snap, prev_snap):
	if len(prev_snap) == 0:
		return 

	diff = list(set(current_snap) - set(prev_snap))
	if len(diff) == 0:
		return

	diff_cleaned = []
	for d in diff:
		# Ignore old one
		if current_snap.index(d) >= 20:
			continue
		diff_cleaned.append(d)

	if len(diff_cleaned) > 0:
		print("New Post:")
		for d in diff_cleaned:
			print(d)
		print()
		__notify_via_email(diff_cleaned)

def main():
	# Debug
	# with open("loaded.html", 'r') as f:
	#   webpage = f.read()
	#   soup = BeautifulSoup(webpage, "html.parser")

	print("Requesting Data From Zillow")
	url = r"https://www.zillow.com/san-diego-ca/rentals/2-_beds/?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22usersSearchTerm%22%3A%2292037%22%2C%22mapBounds%22%3A%7B%22west%22%3A-117.24590349026118%2C%22east%22%3A-117.1956925375024%2C%22south%22%3A32.85766848585083%2C%22north%22%3A32.88506209326565%7D%2C%22mapZoom%22%3A15%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A54296%2C%22regionType%22%3A6%7D%5D%2C%22isMapVisible%22%3Atrue%2C%22filterState%22%3A%7B%22beds%22%3A%7B%22min%22%3A2%7D%2C%22fore%22%3A%7B%22value%22%3Afalse%7D%2C%22ah%22%3A%7B%22value%22%3Atrue%7D%2C%22sort%22%3A%7B%22value%22%3A%22days%22%7D%2C%22nc%22%3A%7B%22value%22%3Afalse%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22fsba%22%3A%7B%22value%22%3Afalse%7D%2C%22fr%22%3A%7B%22value%22%3Atrue%7D%2C%22fsbo%22%3A%7B%22value%22%3Afalse%7D%2C%22auc%22%3A%7B%22value%22%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%7D"
	driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
	driver.get(url) 
	html = driver.page_source
	soup = BeautifulSoup(html, "html.parser")
	driver.quit()

	print("Processing")
	variableDatas = soup.find_all('script')

	snapshot = []
	for idx, data in enumerate(variableDatas):
		if "variableData" in str(data):
			content = "".join(data.contents)
			content = content.replace("<!--","").replace("-->","").strip()
			j = json.loads(content)
			homes = j["cat1"]["searchResults"]["listResults"]
			for home in homes:
				address = None
				beds = None
				baths = None
				price = None

				if "address" in home:
					address = home["address"]
				
				if "beds" in home:
					beds = home["beds"]
				elif "units" in home and "beds" in home["units"][0]:
					beds = home["units"][0]["beds"]
				
				if "baths" in home:
					baths = home["baths"]
				elif "units" in home and "baths" in home["units"][0]:
					baths = home["units"][0]["baths"]

				if "price" in home:
					price = home["price"]
				elif "units" in home and "price" in home["units"][0]:
					price = home["units"][0]["price"]

				h = Home(address, beds, baths, price)
				snapshot.append(h)

			break

	prev_snapshot = load_most_recent_snapshot()
	save_current_snapshot(snapshot)
	compare_notify(snapshot, prev_snapshot)

if __name__ == "__main__":
	main()
