#####################
##### REDUNDANT #####
##################### 

#Terminal commands
import subprocess

#Regular expressions
import re

# Set regex and flags
# regex = re.compile(r"^(?!\s+IE:\sUnknown)\s+(.+)", flags=re.MULTILINE) # gets attributes (not divided by cell)
regex = re.compile(r'(Cell \d+ - Address:.*?)(?=Cell \d+ - Address:|\Z)', flags=re.S) # divided by cell
regex_unknown_lines = re.compile(r"^(\s+IE:\sUnknown:.*[\n|\S])", flags=re.MULTILINE) 

# Get WiFi information:
output = subprocess.run(["sudo", "iwlist", "wlan0", "scan"],capture_output=True).stdout.decode()

# Remove any unknown elements from output
output = regex_unknown_lines.sub('',output)

# Grab each aspect of a newtwork
# cells = regex.findall(output)

# Divide into cells
filtered = regex.findall(output)

for i in filtered:
    print('##### NEW CELL ######')
    print(i)
    print('##### END OF CELL #####')
