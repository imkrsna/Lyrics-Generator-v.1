import sys
import glob
import textwrap
import requests
from PIL import Image, ImageFont, ImageDraw, ImageEnhance
from utils import ffmpeg



class ImageGen():
    """ImageGen: image generation functions"""
    def __init__(self, kwargs):
        self.channel = kwargs['channel']
        self.key = kwargs['key']
        self.name = kwargs['name']
        self.singer = kwargs['singer']
        
        self.isfade = kwargs['isfade']
        self.isoverlay = kwargs['isoverlay']
        self.bg_path = kwargs['bg_path']
        self.font_path = kwargs['font_path']
        self.output_path = kwargs['out_path'] + ('/' if kwargs['out_path'][-1] != '/' else '')

        self.fps = kwargs['fps']
        self.length = kwargs['length']
        self.M = kwargs['margin']
        self.W, self.H = ffmpeg.get_size(self.bg_path)

        self.max_length = 60
        self.timestamp, self.lyrics = self.get_lyrics(kwargs['lyrics'])
        self.font_size = self.get_font_size()
        self.font = ImageFont.truetype(self.font_path, self.font_size)
        self.def_font_path = "./ext/fonts/consola.ttf"

    """get_lyrics: return lyrics of song by its key"""
    def get_lyrics(self, lyrics):
        if lyrics == "":
            response = requests.get(f"https://api.textyl.co/api/lyrics?q={self.key}")
            if response.text == "No lyrics available":
                print("No Lyrics Found!")
                sys.exit()
            response = response.json()
        else:
            response = lyrics


        lyrics = [[], "\n"]
        current = 0
        for idx, data in enumerate(response):
            lyrics[0].append(data["seconds"] - current)
            lyrics[1] += data["lyrics"] + "\n"
            current = data["seconds"]
        
        lyrics[1] = lyrics[1][:-1]
        # appening timestamp for last line
        lyrics[0].append(self.length - current)

        return lyrics
    
    """get_max_line: return longest line in lyrics"""
    def get_max_line(self):
        max_line = ""
        for line in self.lyrics.split('\n'):
            for i in textwrap.wrap(line, width=self.max_length):
                max_line = max(max_line, i, key=len)
        return max_line
    
    """get_font_size: return size of font"""
    def get_font_size(self):
        tmp = Image.new(mode="RGB", size=(self.W, self.H))
        tmp_d = ImageDraw.Draw(tmp)

        max_line = self.get_max_line()
        size = 200

        while tmp_d.textsize(max_line, ImageFont.truetype(self.font_path, size))[0] > (self.W - 2 * self.M):
            size -= 10
        
        return size
    
    def get_def_font_size(self, width):
        tmp = Image.new(mode="RGB", size=(width,100))
        tmp_draw = ImageDraw.Draw(tmp)
        size = 70
        while tmp_draw.textsize(self.channel, ImageFont.truetype(self.def_font_path, size=size))[0] > width/2:
            size -= 5
        return size

    """get_background: return background image on basis of its type"""
    def get_background(self, frame):
        # temp brightness factor
        brightness = 0.7

        # if background is a still image file
        if self.bg_path.endswith('.jpg') or self.bg_path.endswith('.png'):
            if frame == 0:
                self.bg = Image.open(self.bg_path)
            
        # if background is a gif or mp4 video file
        elif self.bg_path.endswith('.gif') or self.bg_path.endswith('.mp4'):
            if frame == 0:
                ffmpeg.vid_to_frames(self.bg_path, self.output_path + "bg_frames/bg_frame%4d.jpg", self.fps)

            bg_frames = [file for file in glob.glob(self.output_path + "bg_frames/*jpg")]
            frame_no = frame % len(bg_frames)
            self.bg = Image.open(bg_frames[frame_no])
            
        # changing brightness of image
        new_bg = ImageEnhance.Brightness(self.bg)
        new_bg = new_bg.enhance(brightness).convert("RGBA")

        if self.isoverlay:
            if frame == 0:
                self.overlay_main = Image.open("./ext/overlays/player.png")
            overlay = self.overlay_main.copy()
            # player factor
            w = new_bg.size[0] / 3
            h = overlay.size[1] * (w / overlay.size[0])
            sf = w / overlay.size[0]
            overlay = overlay.resize((round(w),round(h)), Image.ANTIALIAS)
            
            # creating timeline node
            if frame == 0:
                self.knob_main = Image.open("./ext/overlays/knob.png")
            knob = self.knob_main.copy()
            w = knob.size[0] * sf
            h = knob.size[1] * sf
            knob = knob.resize((round(w),round(h)), Image.ANTIALIAS)

            # knob
            knob_x = frame * ((overlay.size[0] - knob.size[0]) / (self.length * self.fps))
            overlay.paste(knob, (round(knob_x),0), knob)
            
            txt = ImageDraw.Draw(new_bg)
            if frame == 0:
                self.def_font = ImageFont.truetype(self.def_font_path, self.get_def_font_size(overlay.size[0]))
            
            # channel name 
            channel_margin = 20
            txt_size = txt.textsize(self.channel, font=self.def_font)
            txt_pos = ((self.W - txt_size[0]) / 2, self.H - txt_size[1] - channel_margin)
            
            channel_color = (254, 176, 6, 255)
            txt.text(txt_pos, self.channel, fill=channel_color, font=self.def_font)

            pos = (round((self.W - overlay.size[0])/ 2), round((self.H - overlay.size[1] - txt_size[1] - 2 * channel_margin)))
            
            # song name 
            song_txt_size = txt.textsize(self.name + ' - ' + self.singer, font=self.def_font)
            song_txt_pos = ((self.W - song_txt_size[0]) / 2, pos[1] - song_txt_size[1] - channel_margin)
            txt.text(song_txt_pos ,self.name + ' - ' + self.singer, fill=(255,255,255,255), font=self.def_font)
            new_bg.paste(overlay, pos, overlay)

        print(f"Frame Generated: {frame}", end='\r')
        return new_bg


    """generate: generate images from lyrics and timestamp"""
    def generate(self):
        # fade frame condition
        if self.isfade:
            fade_factor = 0.2
        else:
            fade_factor = 0
        
        # line heigh because of overlay condition
        if self.isoverlay:
            y_factor = 3
        else:
            y_factor = 2
        
        # frame count
        fc = 0

        # looping through lyrics
        for idx, line in enumerate(self.lyrics.split('\n')):
            text = ""
            for i in textwrap.wrap(line, width=self.max_length):
                text += i + '\n'
            text = text[:-1]

            fade_frames = round(self.fps * fade_factor)

            # Start FadeIn Frames
            for i in range(fade_frames):
                bg = self.get_background(fc)
                tmp = Image.new(mode="RGBA", size=bg.size, color=(0,0,0,0))
                tmp_d = ImageDraw.Draw(tmp)

                # w, h = tmp_d.textsize(text, self.font)
                w, h = self.font.getsize(text)
                pos = ((self.W - w) / 2, (self.H - h) / y_factor)
                fade_per = i * round(255 / fade_frames) 

                tmp_d.text(pos, text, (255,255,255,fade_per), self.font, align="center")
                
                frame = Image.alpha_composite(bg, tmp)
                frame.convert("RGB").save(self.output_path + 'frames/frame{0:04d}.jpg'.format(fc))
                fc += 1

            # Normal Frames
            for i in range((self.timestamp[idx] * self.fps) - (2 * fade_frames)):
                bg = self.get_background(fc)
                bg_d = ImageDraw.Draw(bg)

                # w, h = tmp_d.textsize(text, self.font)
                w, h = self.font.getsize(text)
                pos = ((self.W - w) / 2, (self.H - h) / y_factor)

                bg_d.text(pos, text, (255,255,255,255), self.font, align="center")

                bg.convert("RGB").save(self.output_path + 'frames/frame{0:04d}.jpg'.format(fc))
                fc += 1
            
            # End FadeOut Frames
            for i in reversed(range(fade_frames)):
                bg = self.get_background(fc)
                tmp = Image.new(mode="RGBA", size=bg.size, color=(0,0,0,0))
                tmp_d = ImageDraw.Draw(tmp)

                # w, h = tmp_d.textsize(text, self.font)
                w, h = self.font.getsize(text)
                pos = ((self.W - w) / 2, (self.H - h) / y_factor)
                fade_per = i * round(255 / fade_frames) 

                tmp_d.text(pos, text, (255,255,255,fade_per), self.font, align="center")
                
                frame = Image.alpha_composite(bg, tmp)
                frame.convert("RGB").save(self.output_path + 'frames/frame{0:04d}.jpg'.format(fc))
                fc += 1



# l = [{"seconds":12,"lyrics":"I see your monsters, I see your pain"},{"seconds":17,"lyrics":"Tell me your problems, I'll chase them away"},{"seconds":23,"lyrics":"I'll be your lighthouse, I'll make it okay"},{"seconds":28,"lyrics":"When I see your monsters, I'll stand there so brave"},{"seconds":33,"lyrics":"And chase them all away, In the dark we we"},{"seconds":96,"lyrics":"We stand apart we we, Never see that the things"},{"seconds":101,"lyrics":"We need are staring right at us, You just wanna hide hide hide"},{"seconds":108,"lyrics":"Never show your smile smile, Stand alone when you need someone"},{"seconds":113,"lyrics":"It's the hardest thing of all, That you see are the bad bad"},{"seconds":119,"lyrics":"Bad memories take your time, And you'll find me"},{"seconds":128,"lyrics":"I see your monsters, I see your pain"},{"seconds":134,"lyrics":"Tell me your problems, I'll chase them away"},{"seconds":139,"lyrics":"I see your monsters, I see your pain"},{"seconds":144,"lyrics":"Tell me your problems, I'll chase them away"},{"seconds":150,"lyrics":"I'll be your lighthouse, I'll make it okay"},{"seconds":155,"lyrics":"When I see your monsters, I'll stand there so brave"},{"seconds":160,"lyrics":"And chase them all away, I'll be your lighthouse"},{"seconds":175,"lyrics":"I'll make it okay, When I see your monsters"},{"seconds":181,"lyrics":"I'll stand there"}]