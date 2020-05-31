import requests, re, os, json
from bs4 import BeautifulSoup
from time import sleep

class Wilma:
	def __init__(self, username=os.environ.get('WUSERNAME').replace("_", "."), password=os.environ.get('WPASSWORD')):
		self.sessionID = None
		self.Wilma2SID = None

		self.username = username
		self.password = password

		watch = {}

	def login(self):
		def sendRequest():
			sessId = self.getSessionID()

			if sessId != None:

				try:
					r = requests.post("https://wilma.espoo.fi/login", {
						"Login": self.username,
						"Password": self.password,
						"SESSIONID": sessId
					}, allow_redirects=False)

					if ("Location" in r.headers and r.headers['Location'] == "https://wilma.espoo.fi/?loginfailed") or 499 >= r.status_code >= 400:
						print("[-] Incorrect username/password")

						return False
					else:
						self.Wilma2SID = r.cookies.get_dict()["Wilma2SID"]
						print(f"[+] Logged in as {self.username}, Wilma2SID: {self.Wilma2SID}")

						return True
				except Exception as e:
					print(f"[–] Exception while logging in: {e}")
					return False
			else:
				return False

		while sendRequest() == False:
			sleep(60*10)

	def getSessionID(self):
		try:
			r = requests.get("https://wilma.espoo.fi/login")
			sessId = r.cookies.get_dict()["Wilma2LoginID"]
			print(f"[+] Session ID: {sessId}")
			return sessId
		except Exception as e:
			print("[-] Error occured while getting login session ID")
			return None

	def checkCourse(self, courseId): # Return true if there is room in a course
		try:
			r = requests.get(
				f"https://wilma.espoo.fi/selection/getback?message=group-info&target={courseId}",
				allow_redirects=False,
				cookies={ "Wilma2SID": self.Wilma2SID }
			)

			if r.status_code != 200:
				print("[-] Error occured while checking course")
				return None

			soup = BeautifulSoup(r.text, features="html.parser")
			tags = soup.find_all(["th", "td"])
			name = soup.find_all("td", class_="coursename")[0].text

			for index in range(0, len(tags)):
				if tags[index].text == "Ilmoittautuneita":
					ilmoittautuneita = tags[index + 1].text
				elif tags[index].text == "Maksimikoko":
					maksimikoko = tags[index + 1].text

			if int(ilmoittautuneita) < int(maksimikoko):
				print("\nKurssilla on tilaa!!\n")
				self.sendPush(name, f"Kurssilla on tilaa: {ilmoittautuneita}/{maksimikoko}")
				return True
			else:
				print(f"Ei tilaa: {ilmoittautuneita}/{maksimikoko}")
				return False
		except Exception as e:
			print(f"Exception while checking course: {e}")
			return None


	def sendPush(self, name, message):
		token = os.environ.get("PTOKEN")
		user = os.environ.get("PUSER")
		requests.post(
			os.environ.get("SURL"),
			data = json.dumps({"text": f"{name}:\n{message}"})
		)
		print(f"Sent '{message}'")

if __name__ == "__main__":
	courses = os.environ.get('COURSEID').split(",")
	w = loginWilma()
	w.()

	while True:
		for course in courses:
			check = w.checkCourse(course)

			while check == None:
				w.login()
				check = w.checkCourse(course)
				sleep(10*60)

			sleep(1)

		sleep(60*8)
