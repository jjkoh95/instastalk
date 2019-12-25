# instastalk
Instastalk is a library initiated by a creep who develops massive crush to instagram celebrities and wishes to automate the process of backing up their photos.

## How to use
`pip install instastalk`
```python
from instastalk import (
    AnonyStalker,
    InstaStalker,
)

# no auth - only public posts (no stories)
stalker = AnonyStalker()
stalker.download_user('jjkoh95', timesleep_factor=45) # will need to create a directory 'jjkoh95'
stalker.to_pickle('anony.pkl')

# with auth
login_stalker = InstaStalker('your_username', 'your_password')
login_stalker.download_user('jjkoh95', timesleep_factor=45)
login_stalker.to_pickle('user.pkl')

# to continue last download
import pickle
with open('user.pkl', 'rb') as f:
    s: InstaStalker = pickle.load(f)
s.download_user('jjkoh95')
```

# Disclaimer
This project is initiated as a python practice and I have no intention of going against any rules and regulations of Instagram. Be a discrete creep.