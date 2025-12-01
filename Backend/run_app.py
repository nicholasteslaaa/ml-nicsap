import subprocess

commands = [
    'start cmd /k "cd Backend && python -m uvicorn API:app --reload"',
    'start cmd /k "npm run dev"',
    'start cmd /k "cloudflared tunnel run rosblok-tunnel"'
]

for cmd in commands:
    subprocess.Popen(cmd, shell=True)
