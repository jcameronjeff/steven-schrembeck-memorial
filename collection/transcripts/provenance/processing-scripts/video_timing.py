import pathlib,json,subprocess
base=pathlib.Path(__file__).resolve().parent.parent;d=json.loads((base/'outputs/job-ledger.json').read_text());root=pathlib.Path(d['archive_root']);rows=[]
for j in d['jobs']:
 if j['kind']!='video':continue
 r=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','a:0','-read_intervals','%+#10','-show_frames','-show_entries','frame=best_effort_timestamp_time,pts_time,nb_samples','-of','json',str(root/j['source_path'])],check=True,capture_output=True,text=True)
 frames=json.loads(r.stdout)['frames'];first=float(frames[0]['best_effort_timestamp_time']);offset=first-j['source_format_start_seconds'];rows.append({'source_path':j['source_path'],'first_decoded_audio_frame_pts_seconds':first,'format_start_seconds':j['source_format_start_seconds'],'original_media_offset_seconds':offset,'method':'First decoded audio frame presentation timestamp minus container start time; FLAC starts at first decoded sample. No splitting or trimming.'})
(base/'work/video-timing.json').write_text(json.dumps(rows,indent=2)+'\n');print('Video offsets',sorted(set(r['original_media_offset_seconds'] for r in rows)))
