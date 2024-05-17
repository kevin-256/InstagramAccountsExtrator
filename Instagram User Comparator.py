#pip install Pillow
#https://www.instagram.com/api/v1/users/{user_id}/info/

import base64
from io import BytesIO
import selenium.webdriver
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import By
import re, json
import tkinter as tk
from tkinter import ttk
from os.path import exists
from os import remove
import requests
import urllib.parse
from PIL import Image, ImageTk
import json
from time import time
from time import sleep

driver = None
session = requests.Session()


class Cookie:
	filePath = "cookies.json"

	@staticmethod
	def get_cookies_from_file():
		if not exists(Cookie.filePath):
			return []
		with open(Cookie.filePath, 'r') as file:
			return json.load(file)
	
	@staticmethod
	def load_cookies_into_driver_from_file(driver):
		cookies = Cookie.get_cookies_from_file()
		if Cookie.areExpired(cookies):
			return True
		for cookie in cookies:
			driver.add_cookie(cookie)

	@staticmethod
	def load_cookies_into_session_from_file(session):
			cookies = Cookie.get_cookies_from_file()
			if Cookie.areExpired(cookies):
				return True
			for cookie in cookies:
				session.cookies.set(cookie['name'], cookie['value'])

	@staticmethod
	def save_cookies_to_file(driver):
		with open(Cookie.filePath, 'w') as file:
			json.dump(driver.get_cookies(), file)

	@staticmethod
	def areExpired(cookies):
		for cookie in cookies:
			if Cookie.isExpired(cookie):
				return True
		return False
	@staticmethod
	def isExpired(cookie):
		try:
			return (cookie['expiry']-int(time()))<0
		except:
			return False

	@staticmethod
	def deleteOldCookiesFile():
		try:
			remove(Cookie.filePath)
		except OSError:
			pass


class User:
	def __init__(self, username, session, fullName=""):
		self.username = username
		self.session = session
		self.fullName = fullName
		self.followers = []
		self.followings = []
		self.userId = None
		self.profileImageUrl = None
		if fullName=="":
			self.refreshUserData()

	@staticmethod
	def isUsernameValid(username):
		pattern = r'^[\w](?!.*?\.{2})[\w]{1,28}[\w]$'
		return re.match(pattern, username)
	def refreshUserData(self): # refresh data about this user but the followers and followings
		user_query_res = self.session.get(f"https://www.instagram.com/web/search/topsearch/?query={self.username}").json()
		if 'message' in user_query_res:
			raise Exception(f"You must login")
		if len(user_query_res['users'])==0:
			raise Exception(f"User {self.username} not found")
		user_query_json = user_query_res['users'][0]['user']
		self.userId = user_query_json['pk']
		self.username = user_query_json['username']
		self.fullName = user_query_json['full_name']
		self.profileImageUrl = user_query_json['profile_pic_url']
		self.profileImage = ImageTk.PhotoImage(Image.open(BytesIO(requests.get(self.profileImageUrl).content)).resize(size=(40,40)))

	def refreshData(self):
		if self.userId is None:
			user_query_res = self.session.get(f"https://www.instagram.com/web/search/topsearch/?query={self.username}").json()
			if len(user_query_res['users'])==0:
				raise Exception(f"User {self.username} not found")
			user_query_json = user_query_res['users'][0]['user']
			self.userId = user_query_json['pk']
			self.username = user_query_json['username']
			self.fullName = user_query_json['full_name']
			self.profileImageUrl = user_query_json['profile_pic_url']
  

		after = None
		has_next = True
		while has_next:
			res = self.session.get(f"https://www.instagram.com/graphql/query/?query_hash=c76146de99bb02f6415203be841dd25a&variables=" + urllib.parse.quote(json.dumps(
				{
					'id': self.userId,
					'include_reel': True,
					'fetch_mutual': True,
					'first': 50,
					'after': after
				}
			))).json()
			has_next = res['data']['user']['edge_followed_by']['page_info']['has_next_page']
			after = res['data']['user']['edge_followed_by']['page_info']['end_cursor']
			self.followers.extend([User(username=node['node']['username'], session=self.session, fullName=node['node']['full_name']) for node in res['data']['user']['edge_followed_by']['edges']])
		after = None
		has_next = True
		while has_next:
			res = self.session.get(f"https://www.instagram.com/graphql/query/?query_hash=d04b0a864b4b54837c0d870b0e77e076&variables=" + urllib.parse.quote(json.dumps(
				{
					'id': self.userId,
					'include_reel': True,
					'fetch_mutual': True,
					'first': 50,
					'after': after
				}
			))).json()
			has_next = res['data']['user']['edge_follow']['page_info']['has_next_page']
			after = res['data']['user']['edge_follow']['page_info']['end_cursor']
			self.followings.extend([User(username=node['node']['username'], session=self.session, fullName=node['node']['full_name']) for node in res['data']['user']['edge_follow']['edges']])




# ######################################        INIT        ######################################
# if not exists(Cookie.filePath): #login into instagram and save login cookies into file
# 	driver.get("https://instagram.com/")
# 	input("Press enter once you have logged into the browswer and accepted to save login info")
# 	Cookie.save_cookies_to_file(driver)
# else: #load login cookies into browser from file if user made login before
# 	driver.get("https://instagram.com/")
# 	Cookie.load_cookies_into_driver_from_file(driver)

# Cookie.load_cookies_into_session_from_file(session) #load login cookies into python session from file if user made login before
# ################################################################################################




class Window:
	def __init__(self, session):
		#users
		self.loadedUsers = []
		#interface
		self.session = session
		self.mainWindow = tk.Tk()
		self.mainWindow.geometry("1000x600")
		self.mainWindow.title("Instagram Profile Compatator")
		self.loginWindow = None
		tabControl = ttk.Notebook(self.mainWindow)

		# create a menubar
		menubar = tk.Menu(self.mainWindow)
		self.mainWindow.config(menu=menubar)
		optionsMenu = tk.Menu(menubar, tearoff=False)
		# add a menu item to the menu
		optionsMenu.add_command(label='Login Window', command=self.openLoginWindow)
		menubar.add_cascade(label="Options", menu=optionsMenu)

		# Add tabs
		userData = ttk.Frame(tabControl)
		compareUserData = ttk.Frame(tabControl)
		tabControl.add(userData, text='User Data')
		tabControl.add(compareUserData, text='Compare User Data')
		# Make the tabs visible
		tabControl.pack(expand=1, fill="both")

  		# add widgets to userData 
		userInputFrame = tk.Frame(userData, width=700, height=500, background="red")
		userInputFrame.grid(row=0, column=0)
		inputUsername = tk.Entry(userInputFrame, width=25)
		inputUsername.focus_set()
		inputUsername.place(x=20, y=20)
		self.combo = ttk.Combobox(
			userInputFrame,
			state="readonly",
			values=[]
		)
		self.combo.bind('<<ComboboxSelected>>', self.comboboxChangeSelected)
		self.combo.place(x=435,y=20)
		self.searchedUserInfo = tk.Frame(userInputFrame, height=50, width=206)
		
		btnSearchUser = tk.Button(userInputFrame, text ="Search", command=lambda: self.searchUser(inputUsername.get()))
		btnSearchUser.place(x=240,y=15)
		
		btnSearchAndLoad = tk.Button(userInputFrame, text ="Load ==>", command=lambda: self.addUser(inputUsername.get(), combo))
		btnSearchAndLoad.place(x=325,y=15)
		
		self.searchedUserInfo.place(x=20,y=70)
  
		self.user_list = tk.Listbox(userData, selectmode="multiple")
		self.user_list.place(x=60,y=100)
        
        #Selected user Followers/Following User List
		self.selectedUserList = tk.Frame(userInputFrame, height=50, width=206)
        # Adding scrollbar
		scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.user_list.yview)
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		self.user_list.config(yscrollcommand=scrollbar.set)
		
  		# creating login window
		self.openLoginWindow()
		# completed login by loading old cookies or creating cookies

	def start(self):
		self.mainWindow.mainloop()

	def openLoginWindow(self):
		self.loginWindow = tk.Toplevel(self.mainWindow)
		self.loginWindow.title("Login")
		self.mainWindow.eval(f'tk::PlaceWindow {str(self.loginWindow)} center')
		btnLogin = tk.Button(self.loginWindow, text ="Login", command=self.makeLogin)
		#btnLogin.grid(row=0, column=0)
		btnLogin.pack(padx=10, pady=20, side=tk.LEFT)

		btnLoadOldCookies = tk.Button(self.loginWindow, text ="Load old cookies", command=self.loadOldCookies)
		#btnLoadOldCookies.grid(row=0, column=1)
		btnLoadOldCookies.pack(padx=10, pady=20, side=tk.LEFT)

		if Cookie.areExpired(Cookie.get_cookies_from_file()):
			btnLoadOldCookies["state"] = "disabled"
		# Make the new window modal
		self.loginWindow.attributes('-topmost',True)
		self.loginWindow.grab_set()
		self.loginWindow.mainloop()
  	
	def makeLogin(self):
		Cookie.deleteOldCookiesFile()
		global driver
		driver = selenium.webdriver.Firefox()
		driver.get("https://instagram.com/")
		# wait to load login page
		try:
			print("waiting for user to login")
			elem = WebDriverWait(driver, 30).until(
					EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Allow all cookies')]"))
				)
		finally:
			pass
		# wait the user to login
		try:
			elem = WebDriverWait(driver, 600).until(
					EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'For you')]"))
				)
		except:
			return
		Cookie.save_cookies_to_file(driver)
		Cookie.load_cookies_into_session_from_file(session)
		self.loginWindow.grab_release()
		self.loginWindow.destroy()

	def loadOldCookies(self):
		if Cookie.areExpired(Cookie.get_cookies_from_file()):
			self.makeLogin()
			return
		Cookie.load_cookies_into_session_from_file(self.session)
		self.loginWindow.grab_release()
		self.loginWindow.destroy()
	
	def searchUser(self, username):
		for child in self.searchedUserInfo.winfo_children():
			child.destroy()
		if User.isUsernameValid(username):
			# try:
			user = User(username, self.session)
			self.img = user.profileImage
			image = tk.Label(self.searchedUserInfo, image=self.img, )
			image.place(x=5,y=5)
			username = tk.Label(self.searchedUserInfo, text=user.username)
			username.place(x=50, y=5)
			fullName = tk.Label(self.searchedUserInfo, text=user.fullName, font=('Helvetica', '9'))
			fullName.place(x=50, y=25)
			# except:
			# 	pass
			return user
		return None

	def addUser(self, username, combo):
		user = self.searchUser(self.searchedUserInfo, username)
		if user is None:
			return
		user.refreshData()
		combo['values'] += user.username
		self.loadedUsers.append(user)
	def comboboxChangeSelected(self):
		selectedUser = None
		for user in self.loadedUsers:
			if user.username == self.combo.get():
				selectedUser = user
				break
		if selectedUser != None: #selected user found inside loadedUser
			for child in self.searchedUserInfo.winfo_children():
				child.destroy()		
			self.img = selectedUser.profileImage
			image = tk.Label(self.searchedUserInfo, image=self.img, )
			image.place(x=5,y=5)
			username = tk.Label(self.searchedUserInfo, text=user.username)
			username.place(x=50, y=5)
			fullName = tk.Label(self.searchedUserInfo, text=user.fullName, font=('Helvetica', '9'))
			fullName.place(x=50, y=25)


		

w = Window(session)
w.start()