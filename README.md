# CrookedConfluence
A secrets scanner for Confluence using wordlists

Based on https://github.com/antman1p/Conf-Thief - Had to make so many changes I made my own repo


## Usage
```bash
python CrookedConfluence.py -c https://confluence.<domain>.com -p <auth-token> -d ./dictionaries/test.txt
```
The links and titles will be output into './loot/confluence_content.txt'
