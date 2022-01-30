import os
import json
from utils.videogen import videogen

def create_paths(out):
    folders = ['bg_frames', 'frames', 'audio', 'video']
    for folder in folders:
        try:
            os.mkdir(out + folder)
        except FileExistsError:
            pass

def main():
    with open('./config.json', 'r') as f:
        data = json.load(f)
    out = data['out_path'] + ('/' if data['out_path'][-1] != '/' else '')
    create_paths(out)
    videogen(data).generate()

if __name__ == "__main__":
    main()