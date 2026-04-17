# AIR-AI-

# Text-to-Video Generation with JarvisLabs CLI

I've set up a complete text-to-video pipeline using the state-of-the-art **CogVideoX-5b** model. This model creates incredibly high-quality videos from text prompts.

I have created a dedicated folder containing the necessary files:
1.  `generate_video.py`: The AI script that handles downloading the model and generating the video.
2.  `requirements.txt`: The dependencies.

Here is exactly how to run this on JarvisLabs via their CLI.

## Step 1: Open Your Terminal in the Project Folder

First, navigate to this folder:

```powershell
cd "c:\log anyalysis\jarvis_video_gen"
```

## Step 2: The Magic "One-Shot" Command

Since you have the `jl` CLI configured, you can launch a GPU, install requirements, and run the generation—all seamlessly. The A6000 or RTX6000Ada GPUs are perfect for this due to their high VRAM.

Run this command:

```powershell
jl run generate_video.py --gpu A6000 --requirements requirements.txt -- --prompt "A cinematic shot of an astronaut riding a horse on Mars, professional cinematography, 4k resolution"
```

### What this command does:
1.  **`jl run generate_video.py`**: Tells Jarvis to upload your current directory and run the Python script.
2.  **`--gpu A6000`**: Provisions a powerful A6000 GPU instance automatically.
3.  **`--requirements requirements.txt`**: Automatically sets up the virtual environment and installs video dependencies.
4.  **`--`**: Separates CLI arguments from your Python script's arguments.
5.  **`--prompt "..."`**: The customized text you want to turn into a video!

## Step 3: Monitor the Logs

Because `jl run` runs in the background, it will give you a `run_id`. You can watch the generation progress in real-time (downloading the model weights takes a couple of minutes the first time):

```powershell
jl run logs <your_run_id>
```

## Step 4: Download Your Video

Once the logs print "✅ Video generation complete!", you can download your generated `output.mp4` to your PC. 

```powershell
# 1. Get your specific instance ID
jl list

# 2. Download the file from the instance to your local folder
jl download <instance_id> /home/output.mp4 ./output.mp4
```

## Step 5: Clean Up

**Do not forget to destroy the instance** once you have downloaded the video to stop billing!

```powershell
jl destroy <instance_id>
```
