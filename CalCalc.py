import argparse
import re
import wolframalpha


parser = argparse.ArgumentParser(description='CalCalculate Input')
parser.add_argument('inString', help ='Need to ask your question')
parser.add_argument('-t', action='store_true', default=False, dest='askAPI', help='Set -t if you want to push question to API')


results = parser.parse_args()




comp = re.compile("[a-zA-Z]")
if (comp.search(results.inString)==None) and not results.askAPI:
    try:
        print eval(str(results.inString))
    except IOError, e:
        pass

else:
	client = wolframalpha.Client('UAGAWR-3X6Y8W777Q')
	res = client.query('%s' %inString)
	ans = next(res.results).text)
	ans = ans.encode('ascii', 'replace')
	ans=ans.replace('?', '*') 
	ans=ans.replace('^', '**')

	nums = re.compile("[0-9\+\-\*\^\.]+")

	answer=re.findall(comp, ans)
	try:
		print 'asking API %s' %test
		print eval(answer[0])

	#quest = results.inString.replace(" ", "+")
	#url = 'http://api.wolframalpha.com/v2/query?input=%s&appid=UAGAWR-3X6Y8W777Q' %quest
	#resultsURL = urllib2.urlopen(url)
	#resultsURLText = resultsURL.read()
	#test = parseString(resultsURLText)
	
