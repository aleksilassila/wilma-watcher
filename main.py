import requests, re, os
from bs4 import BeautifulSoup
from time import sleep

class Wilma:
	def __init__(self, username, password):
		self.sessionID = None
		self.Wilma2SID = None

		self.username = username
		self.password = password

		watch = {}

	def login(self):
		sessId = self.getSessionID()

		if sessId:
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


		else:
			print("[-] Could not obtain session ID")
			return False


	def getSessionID(self):
		r = requests.get("https://wilma.espoo.fi/login")
		try:
			sessId = r.cookies.get_dict()["Wilma2LoginID"]
			print(f"[+] Session ID: {sessId}")
			return sessId
		except Exception as e:
			print("[-] Error occured while getting login session ID")
			return None

	def checkCourse(self, courseId): # Return true if there is room in a course
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

		for index in range(0, len(tags)):
			if tags[index].text == "Ilmoittautuneita":
				ilmoittautuneita = tags[index + 1].text
			elif tags[index].text == "Maksimikoko":
				maksimikoko = tags[index + 1].text

		self.sendPush(f"Kurssilla on {ilmoittautuneita}/{maksimikoko}")
		return True

	def sendPush(self, message):
		print(message)

if __name__ == "__main__":
	course = os.environ.get('COURSEID')
	w = Wilma(os.environ.get('WUSERNAME').replace("_", "."), os.environ.get('WPASSWORD'))
	w.login()

	while True:
		check = w.checkCourse(course)
		if check == None:
			w.login()
			w.checkCourse(course)

		sleep(60*7)
