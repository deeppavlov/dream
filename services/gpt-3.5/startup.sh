#! /bin/bash
echo $HOME
date
apt-get install snapd
apt install xvfb
apt install chromium-browser xvfb
echo "Config completed."
echo "Preparing to run server..."
gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300