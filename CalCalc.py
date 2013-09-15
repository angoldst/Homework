import argparse
import re
import urllib
import urllib2

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
	print 'asking API'
