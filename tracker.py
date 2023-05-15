import requests


class Tracker:
    def __init__(self, url:str, text:str) -> None:
        self.url = url
        self.track_text = text
    
    def search(self):
        response = requests.get(self.url)
        if response.text.find(self.track_text) != -1:
            return False
        else:
            return True
