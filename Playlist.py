import os

class Playlist():

    def __init__(self):
        print("initializing...")
        self.thr_files = list()
        for file in os.listdir("."):
            if file.endswith(".thr"):
                self.thr_files.append(file)

        self.current_file_index = 0

    def getNextFile(self):
        self.current_file_index += 1
        if self.current_file_index < len(self.thr_files):
            self.current_file_index = 0
        return self.thr_files[self.current_file_index]