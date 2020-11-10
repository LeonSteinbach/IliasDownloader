import os
import os.path
import json
import time
import m3u8
import requests
import subprocess
from tkinter import *
from tkinter import ttk
from tkinter import scrolledtext
from threading import Thread
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller


def write_json(data, filename):
    with open(filename, "w+") as f:
        f.write(json.dumps(data))


def read_json(filename):
    f = open(filename, "r")
    data = json.loads(f.read())
    f.close()
    return data


class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)

        # OS
        if not os.path.exists(".\\downloads"):
            os.makedirs(".\\downloads")

        # Tkinter
        self.master = master

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.master.geometry("1200x800")
        self.master.title("ILIAS TOOLS")

        self.debug_mode = BooleanVar(value=True)
        self.selected = []
        self.ilias_item = None
        self.crawl_types = ["Kurs", "Ordner", "VIMP", "Interaktives Video"]

        self.create_widgets()

        # Selenium
        self.chrome_options = Options()
        #self.chrome_options.add_argument("--no-sandbox")
        #self.chrome_options.add_argument("--headless")
        #self.chrome_options.add_argument("--test-type")
        self.chrome_options.add_experimental_option("prefs", {
                "profile.default_content_settings.popups": 0,
                "download.default_directory": os.getcwd() + "\\downloads",
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing_for_trusted_sources_enabled": False,
                "safebrowsing.enabled": False
        })
        self.browser = webdriver.Chrome(options=self.chrome_options)

        # ILIAS
        self.logged_in = False
        self.login_error = False
    
    def on_closing(self):
        self.master.destroy()
        self.browser.quit()
        exit()

    def create_widgets(self):
        # Login frame
        self.frame_login = ttk.Frame(self.master)
        self.frame_login.grid(row=0, column=0, padx=(10, 10), pady=(10, 10), sticky="w")

        # Username label and entry
        self.label_username = ttk.Label(self.frame_login, text="Username")
        self.label_username.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky="w")
        self.entry_username = ttk.Entry(self.frame_login)
        self.entry_username.grid(row=1, column=0, padx=(0, 0), pady=(0, 0), sticky="w")

        # Password label and entry
        self.label_password = ttk.Label(self.frame_login, text="Password")
        self.label_password.grid(row=0, column=1, padx=(10, 0), pady=(0, 0), sticky="w")
        self.entry_password = ttk.Entry(self.frame_login)
        self.entry_password.grid(row=1, column=1, padx=(10, 0), pady=(0, 0), sticky="w")

        # Login button
        self.button_login = ttk.Button(self.frame_login, text="Login", command=self.login)
        self.button_login.grid(row=1, column=2, padx=(10, 0), pady=(0, 0), sticky="w")

        # Login status
        self.frame_login_status = ttk.Frame(self.frame_login)
        self.frame_login_status.grid(row=2, column=0, padx=(0, 0), pady=(0, 0), sticky="w")

        self.label_login_status_text = ttk.Label(self.frame_login_status, text="Status: ")
        self.label_login_status_text.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky="w")
        self.label_login_status = ttk.Label(self.frame_login_status, text="logged out", foreground="orange")
        self.label_login_status.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky="w")

        # TreeView
        self.tree = ttk.Treeview(self.master, height=20)

        self.tree["columns"] = ("one", "two", "three")

        self.tree.column("#0", width=600, minwidth=300, stretch=NO)
        self.tree.column("one", width=50, minwidth=50, stretch=NO)
        self.tree.column("two", width=100, minwidth=100, stretch=NO)
        self.tree.column("three", width=150, minwidth=150)

        self.tree.heading("#0",text="Name", anchor=W)
        self.tree.heading("one", text="Type", anchor=W)
        self.tree.heading("two", text="Size", anchor=W)
        self.tree.heading("three", text="Last changed", anchor=W)

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_click)
        self.tree.grid(row=1, column=0, padx=(10, 0), pady=(10, 0), sticky="w")

        # Lower buttons frame
        self.frame_buttons = ttk.Frame(self.master)
        self.frame_buttons.grid(row=2, column=0, padx=(0, 0), pady=(0, 0), sticky="w")

        # Crawl button
        self.button_crawl = ttk.Button(self.frame_buttons, text="Update", command=self.crawl)
        self.button_crawl.grid(row=0, column=0, padx=(10, 0), pady=(10, 0), sticky="w")

        # Download button
        self.button_download = ttk.Button(self.frame_buttons, text="Download", command=self.download)
        self.button_download.grid(row=0, column=1, padx=(10, 0), pady=(10, 0), sticky="w")
    
    def login(self):
        thread = Thread(target=self.login_thread, args=())
        thread.start()

    def login_thread(self):
        username = self.entry_username.get()
        password = self.entry_password.get()

        # Log out first if already logged in
        if self.logged_in:
            self.logout()

        # Main login page
        self.browser.get(login_url)

        # Get button item
        button_login = self.browser.find_element_by_xpath("//form[@name='formlogin']//img")
        button_login.click()

        # Get entry/button items
        entry_username = self.browser.find_element_by_xpath("//form[@id='login-form']//input[contains(@name, 'username')]")
        entry_password = self.browser.find_element_by_xpath("//form[@id='login-form']//input[contains(@name, 'password')]")
        button_login = self.browser.find_element_by_xpath("//form[@id='login-form']//input[@type='submit']")

        # Write and submit
        entry_username.send_keys(username)
        entry_password.send_keys(password)
        button_login.click()
        
        # Validate login
        error_messages = self.browser.find_elements_by_xpath("//form[@id='login-form']//div[@class='errorMessage']")
        self.login_error = len(error_messages) > 0
        self.logged_in = not self.login_error

        # Change login status
        if self.logged_in:
            self.label_login_status["foreground"] = "green"
            self.label_login_status["text"] = "logged in"

            # Load tree from file
            if os.path.exists("data.json"):
                item = IliasItem.load("data.json")
                self.ilias_item = item
                self.clear_tree()
                self.set_tree(item, "")
        else:
            self.label_login_status["foreground"] = "orange"
            self.label_login_status["text"] = "logged out"
        if self.login_error:
            self.label_login_status["foreground"] = "red"
            self.label_login_status["text"] = "login error"

    def logout(self):
        thread = Thread(target=self.logout_thread, args=())
        thread.start()

    def logout_thread(self):
        self.logged_in = False
        self.login_error = False

        self.browser.get(logout_url)
        self.browser.quit()
        self.browser = webdriver.Chrome(options=self.chrome_options)
    
    def crawl(self):
        thread = Thread(target=self.crawl_thread, args=())
        thread.start()

    def crawl_thread(self, item=None):
        if item is None:
            item = IliasItem("base", "Module", self.browser.current_url, ["", "", ""])
        
        item.get_subitems(self.browser)

        for sub_item in item.sub_items:
            if sub_item.typ in self.crawl_types:
                self.crawl_thread(sub_item)
        
        if item.typ == "base":
            self.ilias_item = item
            self.ilias_item.save("data.json")
            self.clear_tree()
            self.set_tree(item, "")
    
    def set_tree(self, item, parent):
        tree_item = self.tree.insert(parent, "end", text=item.title, values=item.file_properties)
        for sub_item in item.sub_items:
            self.set_tree(sub_item, tree_item)
    
    def clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def on_tree_click(self, event):
        selection = event.widget.selection()
        self.selected = []
        for item in selection:
            self.selected.append(self.tree.item(item, "text"))
    
    def clean_filename(self, filename):
        return filename.replace("<", "-").replace(">", "-").replace(":", "-").replace("/", "-").replace(
            "\\", "-").replace("|", "-").replace("?", "-").replace("*", "-").replace("\"", "-")
    
    def download(self):
        thread = Thread(target=self.download_thread, args=())
        thread.start()

    def download_thread(self):
        for selected_title in self.selected:
            item = self.ilias_item.search(self.ilias_item, selected_title)

            # Exclude types
            if item.typ in ["Ordner", "Kurs"]:
                continue

            # Normal files
            if item.typ in ["Datei"]:
                self.browser.get(item.url)

            # Streams
            if item.typ == "TS":
                self.download_m3u8(item.url, item.title)
            
            # Interactive videos
            if item.typ == "Video":
                # Set cookies
                cookies = self.browser.get_cookies()
                s = requests.Session()
                for cookie in cookies:
                    s.cookies.set(cookie['name'], cookie['value'])
                
                # Download
                response = s.get(item.url, stream=True)

                filename = ".\\downloads\\" + self.clean_filename(item.title) + ".mp4"
                with open(filename, "wb") as f:
                    f.write(response.content)
    
    def download_m3u8(self, url, filename):
        base_url = "".join(url.split("playlist.m3u8?")[:-1])

        r = requests.get(url)
        m3u8_master = m3u8.loads(r.text)

        resolutions = []
        for i in range(len(m3u8_master.data["playlists"])):
            resolution = m3u8_master.data["playlists"][i]["stream_info"]["resolution"]
            resolutions.append(resolution)

        playlist_url = m3u8_master.data["playlists"][-1]["uri"]
        r = requests.get(base_url + playlist_url)
        playlist = m3u8.loads(r.text)

        r = requests.get(base_url + playlist.data["segments"][0]["uri"])

        length = len(playlist.data["segments"])

        print("\nDownloading video stream...\n")

        filename = ".\\downloads\\" + self.clean_filename(filename) + ".ts"
        with open(filename, "wb") as f:
            for i, segment in enumerate(playlist.data["segments"]):
                print("\rProgess: " + str(i / length * 100).split(".")[0] + "%", end="")
                url = segment["uri"]
                r = requests.get(base_url + url)
                f.write(r.content)
        
        print("\nFinished downloading video stream!\n")


class IliasItem:
    def __init__(self, typ, title, url, file_properties):
        self.typ = typ
        self.title = title
        self.url = url
        self.file_properties = file_properties
        self.sub_items = []
    
    def __str__(self):
        return self.str_recursive(self, 0)
    
    def str_recursive(self, item, level):
        text = item.title + "\t" + item.url[:20] + " ... " + item.url[-10:]
        for sub_item in item.sub_items:
            text += "\n" + "\t" * (level + 1) + self.str_recursive(sub_item, level + 1)
        return text
    
    def check_title(self, base_item):
        items = []
        self.get_all(base_item, items)
        titles = [item.title for item in items]
        
        count = titles.count(self.title)
        if count > 0:
            self.title = self.title + " (" + str(count) + ")"
    
    def get_all(self, item, result):
        if item is None:
            return
        result.append(item)
        for sub_item in item.sub_items:
            self.get_all(sub_item, result)
    
    def search(self, item, title):
        if item.title == title:
            return item
        
        for sub_item in item.sub_items:
            result = self.search(sub_item, title)
            if result is not None:
                return result
    
    def save(self, filename):
        data = {}
        self.to_json(self, data)
        write_json(data, filename)
    
    def to_json(self, item, data):
        data["typ"] = item.typ
        data["title"] = item.title
        data["url"] = item.url
        data["file_properties"] = item.file_properties
        data["sub_items"] = []

        for sub_item in item.sub_items:
            data["sub_items"].append({})
            self.to_json(sub_item, data["sub_items"][-1])

    @staticmethod
    def load(filename):
        data = read_json(filename)
        return IliasItem.load_recursive(data)
    
    @staticmethod
    def load_recursive(data):
        item = IliasItem(data["typ"], data["title"], data["url"], data["file_properties"])
        item.sub_items = []

        for i in range(len(data["sub_items"])):
            item.sub_items.append(IliasItem.load_recursive(data["sub_items"][i]))

        return item

    def get_subitems(self, browser):
        browser.get(self.url)

        # Normal files / folders
        links = browser.find_elements_by_xpath("//div[contains(@class, 'ContainerListItemOuter')]")
        for link in links:
            try:
                link_type = link.find_element_by_xpath(".//div[contains(@class, 'ContainerListItemIcon')]//img").get_attribute("title").split("Symbol ")[-1]

                if link_type not in app.crawl_types and link_type != "Datei":
                    continue

                link_url = link.find_element_by_xpath(".//a[contains(@class, 'ContainerItemTitle')]").get_attribute("href")
                link_title = link.find_element_by_xpath(".//a[contains(@class, 'ContainerItemTitle')]").text

                file_properties = ["", "", ""]
                if link_type == "Datei":
                    properties = link.find_elements_by_xpath(".//div[contains(@class, 'ItemProperties')]//span[contains(@class, 'ItemProperty')]")
                    file_type = properties[0].text
                    file_size = properties[1].text
                    file_changed = properties[2].text

                    file_properties = [file_type, file_size, file_changed]
                
                item = IliasItem(link_type, link_title, link_url, file_properties)
                item.check_title(self)
                self.sub_items.append(item)
            except:
                pass
        
        # Video streams
        link = browser.find_elements_by_xpath("//a[contains(@onclick, '.playVideo')]")
        if len(link) != 0:
            link[0].click()
            time.sleep(2)

            link_type = "TS"
            link_url = browser.find_element_by_xpath("//video//source").get_attribute("src")
            link_title = browser.find_element_by_xpath("//h4[@class='modal-title']").text + " - Stream"
            file_type = "TS"
            file_size = browser.find_elements_by_xpath("//div[contains(@id, 'video_container')]//p")[0].text
            file_changed = browser.find_elements_by_xpath("//div[contains(@id, 'video_container')]//p")[1].text

            file_properties = [file_type, file_size, file_changed]

            item = IliasItem(link_type, link_title, link_url, file_properties)
            item.check_title(self)
            self.sub_items.append(item)

        # Interactive videos
        link_urls = browser.find_elements_by_xpath("//div[contains(@class, 'InteractiveVideo')]//video//source")
        if len(link_urls) != 0:
            link_url = link_urls[0].get_attribute("src")

            link_type = "Video"
            if link_url.startswith("./"):
                link_url = base_url + link_url[2:]
            link_title = browser.find_element_by_xpath("//h1[contains(@class, 'media-heading')]").text + " - Video"
            file_type = "mp4" if "mp4" in link_url.lower() else "Video"
            file_size = ""
            file_changed = ""

            file_properties = [file_type, file_size, file_changed]

            item = IliasItem(link_type, link_title, link_url, file_properties)
            item.check_title(self)
            self.sub_items.append(item)


if __name__ == "__main__":
    base_url = "https://ilias.uni-freiburg.de/"
    login_url = base_url + "login.php?target=&client_id=unifreiburg&cmd=force_login&lang=de"
    logout_url = base_url + "logout.php?lang=de"

    chromedriver_autoinstaller.install()

    root = Tk()
    app = Application(master=root)
    app.mainloop()
