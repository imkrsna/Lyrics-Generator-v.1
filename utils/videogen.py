from utils import ffmpeg
from utils.imagegen import ImageGen
from pytube import YouTube


class videogen():
    """videogen: video generation function"""
    def __init__(self, kwargs):
        self.kwarg = kwargs
        self.url = kwargs['url']
        self.fps = kwargs['fps']
        self.out_path = kwargs['out_path'] + ('/' if kwargs['out_path'][-1] != '/' else '')
        self.yt = YouTube(self.url)
        self.kwarg['length'] = self.yt.length

    def download_audio(self):
        stream = self.yt.streams.get_audio_only()
        self.ext = stream.default_filename.split(".")[-1]
        stream.download(self.out_path + 'audio/' ,filename=f"audio.{self.ext}")
    
    def generate(self):
        # generating images
        ImageGen(self.kwarg).generate()

        # downloading audio
        self.download_audio()

        # making video
        ffmpeg.frames_to_vid(self.out_path + 'frames/frame%4d.jpg', self.out_path + 'video/video.mp4', self.fps)

        # combining video with audio
        ffmpeg.vid_audio_combine(self.out_path + 'video/video.mp4', self.out_path + f'audio/audio.{self.ext}',
                                self.out_path + '/result.mp4')