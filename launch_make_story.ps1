$env:PYTHONIOENCODING="utf8"
python -c "
import sys
from jarvislabs.cli.app import main
sys.argv = [
    'jl', 'run', '.', 
    '--script', 'make_story.py',
    '--gpu', 'A6000', 
    '--requirements', 'requirements.txt'
]
if __name__ == '__main__':
    main()
"
