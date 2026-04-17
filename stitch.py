from moviepy import VideoFileClip, concatenate_videoclips
clips = [VideoFileClip(f"/home/out_shot_{i}.mp4") for i in range(1, 10)]
final = concatenate_videoclips(clips)
final.write_videofile("/home/FINAL_SW1_MOVIE.mp4", codec="libx264")
