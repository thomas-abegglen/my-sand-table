import os
from Controller import CLEAR_MODE_IN_IN, CLEAR_MODE_IN_OUT, CLEAR_MODE_OUT_IN, CLEAR_MODE_OUT_OUT

FILENAME_PLAYLIST = "/home/sisyphus/my-sand-table/playlist.txt"
DIR_THR_FILES = "/home/sisyphus/my-sand-table/THR/"

class Playlist():

    def __init__(self):
        print("initializing...")
        self.thr_files = list()

        if os.path.isfile(FILENAME_PLAYLIST):
            self.read_playlist_file(FILENAME_PLAYLIST)

        self.append_new_files()       
        self.remove_non_existant_files()

        self.write_playlist_file(FILENAME_PLAYLIST)

        self.current_file_index = 0

    def read_playlist_file(self, file_name):
        with open(file_name, "rt") as playlist_file:
            for line in playlist_file.readlines():
                line = line.strip()
                self.thr_files.append(line)

    def append_new_files(self):
        for file in os.listdir(DIR_THR_FILES):
            if file.endswith(".thr") and (DIR_THR_FILES+file) not in self.thr_files:
                self.thr_files.append(DIR_THR_FILES+file)

    def write_playlist_file(self, file_name):
        print("write_playlist_file")
        with open(file_name, "wt") as playlist_file:
            for file in self.thr_files:
                playlist_file.write(file)
                playlist_file.write("\n")

    def remove_non_existant_files(self):
        for file in self.thr_files:
            if not os.path.exists(file):
                self.thr_files.remove(file)

    def get_clear_mode(self, current_rho):
        #determine clearing_mode:
        #where are we? Rho:0.0 or 1.0?
        next_start_rho = self.get_current_start_rho()

        if current_rho != next_start_rho:
            if current_rho == 0.0:
                #we have to clear 0.0 -> 1.0: IN_OUT
                clear_mode = CLEAR_MODE_IN_OUT
                reverse_file = False
            else:
                #we have to clear 1.0 -> 0.0: OUT_IN
                clear_mode = CLEAR_MODE_OUT_IN
                reverse_file = False
        else:
            #current_rho == next_start_rho
            #lets check with next_end_rho (we would have to reverse the file then)
            next_end_rho = self.get_current_end_rho()
            if current_rho != next_end_rho:
                if current_rho == 0.0:
                    #we have to clear 0.0 -> 1.0: IN_OUT
                    clear_mode = CLEAR_MODE_IN_OUT
                    reverse_file = True
                else:
                    #we have to clear 1.0 -> 0.0: OUT_IN
                    clear_mode = CLEAR_MODE_OUT_IN
                    reverse_file = True
            else:
                #even if we reverse the next file, both rho-coordinates are equal,
                #so we perform an CLEAR_MODE_IN_IN or CLEAR_MODE_OUT_OUT without reversing
                if current_rho == 0.0:
                    #we have to clear 0.0 -> 0.0: IN_IN
                    clear_mode = CLEAR_MODE_IN_IN
                    reverse_file = False
                else:
                    #we have to clear 1.0 -> 1.0: OUT_OUT
                    clear_mode = CLEAR_MODE_OUT_OUT
                    reverse_file = False

        return clear_mode, reverse_file

    def get_current_file(self):
        return self.thr_files[self.current_file_index]

    def get_current_end_rho(self):
        with open(self.thr_files[self.current_file_index]) as file:
            lines = file.readlines()

            #loop until last line without "//" at the beginning
            lineIndex = -1
            lastLine = lines[lineIndex].rstrip('\n')
            while lastLine.startswith("//"):
                lineIndex -= 1
                lastLine = lines[lineIndex].rstrip('\n')

            return self.get_rho_from_line(lastLine)

    def get_current_start_rho(self):
        with open(self.thr_files[self.current_file_index]) as file:
            lines = file.readlines()
            #loop until first line without "//" at the beginning
            lineIndex = 0
            firstLine = lines[lineIndex].rstrip('\n')
            while firstLine.startswith("//"):
                lineIndex += 1
                firstLine = lines[lineIndex].rstrip('\n')
            
            return self.get_rho_from_line(firstLine)

    def get_rho_from_line(self, line):
        if line != None:
            line = line.rstrip('\n')

            theta = float(line[:line.find(" ")])
            rho = float(line[line.find(" ")+1:])

            return rho
        else:
            return 0.0

    def get_next_file_index(self):
        if self.current_file_index + 1 < len(self.thr_files):
            return self.current_file_index + 1
        else:
            return 0

    def move_to_next_file(self):
        self.current_file_index = self.get_next_file_index()

    def print(self):
        print("current index:", self.current_file_index)
        print("files:")
        for file in self.thr_files:
            print(file)

        print("current file:", self.get_current_file())

