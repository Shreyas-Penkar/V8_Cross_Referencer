# V8_Cross_Referencer
Tool to cross reference between V8 and Chrome Versions using Chromium Dash API.

Run main.py for using the Tool, it supports V8<->Chrome Version Cross Referencing.
Available for Chromium versions of all OS and all channels.

The db/ folder consists of the versions data for all OS and channels taken from Chromium dash API and also the final versions.json which is produced after all the references have been combined and matched.

The cache/ folder consists of the cached V8 lookups which do the update DB function faster since it reduces the number of HTTP requests. Github puts a rate limit on the requests so a delay of 1 second is added in the script (although this causes the update to take long time, hence the caching). 

The chrome_downloader.py is a script to download Chromium binaries in bulk. (Useful in some situations).

##### Things to Fix
- During Update DB some V8 commits fail to get the version although the version is present.
- Add more comments to the code
