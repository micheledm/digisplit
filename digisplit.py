# -*- coding: utf-8 -*-

import subprocess
from datetime import datetime

def find_between(s, start, end):
  return (s.split(start))[1].split(end)[0]


input_video = "Digitalia.fm #521 - Monopattini Tattici Nucleari.mp4" 
base_dir = "/home/micheledm/git/digisplit/"
vd_ext = "mp4"

input_video = base_dir + input_video #.replace(" ","\ ")
cue_file = 'chapters.cue'

d = open(cue_file).read().splitlines()

general = {}

tracks = {}

current_file = None

for line in d:
    if line.startswith('REM GENRE '):
        general['genre'] = ' '.join(line.split(' ')[2:])
    if line.startswith('REM DATE '):
        general['date'] = ' '.join(line.split(' ')[2:])
    if line.startswith('PERFORMER '):
        general['artist'] = ' '.join(line.split(' ')[1:]).replace('"', '')
    if line.startswith('TITLE '):
        general['album'] = ' '.join(line.split(' ')[1:]).replace('"', '')
    if line.startswith('FILE '):
        current_file = ' '.join(line.split(' ')[1:-1]).replace('"', '')

    if line.startswith('    TRACK '):
        current_track = line.strip().split(' ')[1]
        i = int(current_track)
        tracks[i] = {}
        tracks[i]['number'] = i

    if line.startswith('        TITLE '):
        current_title = find_between(line, '"', '"')
        tracks[i]['title'] = current_title
        
    if line.startswith('        INDEX 01 '):
        current_cue = line.strip().replace("INDEX 01 ","").split(':')
        hour = str((int(current_cue[0]) / 60)).zfill(2)
        minutes = str(int(current_cue[0]) % 60).zfill(2)
        current_cue = hour + ':' + minutes + ':' + current_cue[1]
        tracks[i]['cue_start'] = current_cue
        if i > 1:
            tracks[i-1]['cue_end'] = current_cue
            cue_start_p = tracks[i-1]['cue_start']
            cue_end_p = current_cue
            FMT = '%H:%M:%S'
            tracks[i-1]['duration']  = str(datetime.strptime(cue_end_p, FMT) - datetime.strptime(cue_start_p, FMT))
            fade = tracks[i-1]['duration'].split(":")
            fade = int(fade[0])*3600 + int(fade[1])*60 + int(fade[2]) - 1
            tracks[i-1]['fade'] = fade

print(tracks)

for i in tracks:
    if "cue_start" in tracks[i] and "cue_end" in tracks[i]:
        i = 2

        print("Cutting segment %s: %s (%s/%s-%s)" % (tracks[i]["number"], tracks[i]["title"],tracks[i]["cue_start"],tracks[i]["cue_end"],tracks[i]["duration"]))
        output_video = base_dir + str(i) + "-" + tracks[i]["title"] + '.' + vd_ext

        #TAGLIA VIDEO IN BASE AI CUE
        subprocess.call(['ffmpeg', '-i', input_video, '-y', '-ss', tracks[i]["cue_start"], '-t', tracks[i]["duration"], '-async', '1', '-strict', '2', 'tmp_a.' + vd_ext])


        #INSERISCE FADE INGRESSO E USCITA
        subprocess.call(['ffmpeg', '-i', 'tmp_a.' + vd_ext, '-y', '-vf', 'fade=type=in:duration=1,fade=type=out:duration=1:start_time='+ str(tracks[i]["fade"]), 'tmp_b.'  + vd_ext ])

        #PREPARA TS PER TRANSCODIFICAs     
        subprocess.call(['ffmpeg', '-i', 'tmp_b.' + vd_ext, '-c', 'copy', '-bsf:v', 'h264_mp4toannexb', '-y', '-f', 'mpegts', 'tmp_c.ts'])
            
        #JOIN SIGLA E VIDEO
        subprocess.call(['ffmpeg', '-f', 'mpegts', '-i', 'concat:intro.ts|tmp_c.ts', '-y', '-bsf:a', 'aac_adtstoasc', output_video])

        break

