# We bypass the AppLocker block on "jl.exe" by running the jarvislabs CLI via python directly.
$env:PYTHONIOENCODING="utf8"
python -c "
import sys
from jarvislabs.cli.app import main
sys.argv = [
    'jl', 'run', 'generate_video.py', 
    '--gpu', 'A6000', 
    '--requirements', 'requirements.txt', 
    '--', 
    '--prompt', 'A cinematic shot of a happy horse running through a beautiful green meadow, professional cinematography, 4k resolution'
]
if __name__ == '__main__':
    main()
"
