#!/bin/bash
cd /home
echo "=== Starting 9-shot pipeline ===" | tee -a master.log
for i in 1 2 3 4 5 6 7 8 9; do
  if [ -f "out_shot_${i}.mp4" ]; then
    echo "Shot ${i} already done, skipping." | tee -a master.log
    continue
  fi
  echo "--- Shot ${i}/9 starting at $(date) ---" | tee -a master.log
  python -u gen_single_shot.py ${i} 2>&1 | tee -a master.log
  echo "--- Shot ${i}/9 done at $(date) ---" | tee -a master.log
done
echo "All shots done! Stitching..." | tee -a master.log
python -u -c "
from moviepy import VideoFileClip, concatenate_videoclips
clips = [VideoFileClip(f'/home/out_shot_{i}.mp4') for i in range(1,10)]
concatenate_videoclips(clips).write_videofile('/home/FINAL_SW1_MOVIE.mp4', codec='libx264')
print('All done')
" 2>&1 | tee -a master.log
