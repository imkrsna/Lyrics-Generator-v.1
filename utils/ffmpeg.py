import subprocess

FFMPEG = "./utils/FFMPEG/bin/ffmpeg.exe"
FFPROBE = "./utils/FFMPEG/bin/ffprobe.exe"

def vid_to_frames(vid_path, out_path, fps):
    command = [FFMPEG, '-y', '-i', vid_path, '-vf', f'fps={fps}', out_path]
    subprocess.run(command)

def frames_to_vid(frames, out_path, fps):
    # command = [ FFMPEG, '-y', '-r', f'{fps}',
    #             '-i', frames, '-c:v', 'libx264', '-vf', f'fps={fps}',
    #             '-pix_fmt', 'yuv420p', out_path
    #             ]
    command = [ FFMPEG, '-y', '-framerate', f'{fps}',
                '-i', frames, '-c:v', 'libx264', out_path
                ]
    subprocess.run(command)

def vid_audio_combine(vid_path, audio_path, out_path):
    command = [ FFMPEG, '-y', '-i', vid_path,
                '-i', audio_path,
                '-c:a', 'aac', out_path
                ]
    subprocess.run(command)

def get_size(file_path):
    command = [ FFPROBE, '-v', 'error', '-show_entries', 'stream=width,height', '-of', 'default=noprint_wrappers=1', file_path]
    txt = subprocess.run(command, capture_output=True, text=True).stdout.split('\n')
    return (int(txt[0][6:]), int(txt[1][7:]))