#!/bin/bash

echo "$(date) - Wallbox Launcher started..." >> /home/pi/wallbox.log
echo "$(date) - Wallbox Launcher started..." | wall

cd /home/pi/RasPi-JukeBox-Wallbox

# Check WiFi connection...
iwgetid >> /home/pi/wallbox.log 2>&1

# Make sure git is available...
if command -v git >/dev/null 2>&1; then
    echo "Updating Wallbox code from GitHub..." >> /home/pi/wallbox.log
    echo "Updating Wallbox code from GitHub..." | wall
    git fetch --all >> /home/pi/wallbox.log 2>&1
    git reset --hard origin/master >> /home/pi/wallbox.log 2>&1
    #git clean --fd # Commented out as this will remove logs and any history of any reported problems

    echo "Wallbox project files update completed!" >> /home/pi/wallbox.log
    echo "Wallbox project files update completed!" | wall
else
    echo "Wallbox project files update failed - git not installed!" >> /home/pi/wallbox.log
    echo "Wallbox project files update failed - git not installed!" | wall
fi

# Run the Wallbox script
python Wallbox.py

