import argparse
import re
#import wolframalpha
import sys
import urllib2
import urllib
from xml.dom.minidom import parseString

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def calculate(question, askAPI=False, return_float=False):
	comp = re.compile("[a-zA-Z]")
	if comp.search(question)==None and not askAPI:
		try:
			print eval(str(question))
			return eval(str(question))
		except IOError, e:
			print 'Unable to answer question in current form'
	else:
		print 'asking wolframalpha'
		#client = wolframalpha.Client('UAGAWR-3X6Y8W777Q')
		#res = client.query('%s' %question)
		url = 'http://api.wolframalpha.com/v2/query?input=%s&appid=UAGAWR-3X6Y8W777Q' %question.replace(" ", "+")
		ansURL = urllib2.urlopen(url)
		ansURLText = ansURL.read()
		podStart = ansURLText.find("<pod title='Result'")
		print podStart
		podEnd = ansURLText[podStart:].find("</pod>\n")+podStart+8
		
		ansSeg = ansURLText[podStart:podEnd]
		
		if ansSeg =='':
			print 'I have no answer for you from the current question'
		else:
			parsedSeg = parseString(ansSeg)
			ansPod = parsedSeg.getElementsByTagName("plaintext")[0]
			ans = getText(ansPod.childNodes)
			#ans = re.findall("<plaintext>(.*?)</plaintext>", ansSeg)
			#ans = ans[0]

			#ans = next(res.results).text
			if return_float:
			 	nums = re.compile("[0-9\+\-\*\^\.]+")
			 	ansF = ans.encode('ascii', 'replace')
			 	ansF=ansF.replace('?', '*') 
			 	ansF=ansF.replace('^', '**')

			 	answer=re.findall(nums, ansF)
				
			 	try:		 		
			 		print eval(answer[0])
					return float(eval(answer[0]))
			 	except:
			 		print 'Unable to convert to float'
			 		print 'Answer in text: %s' %ans
			 		print type(ans)	
			 		return ans
			else:	
			 		return ans
			 		print ans			

def test_1():
	#test basic calculation
	assert abs(4-calculate('2**2')) <.001

def test_2():
	#test pull rom wolframalpha
	assert calculate('mass of the moon in kg', return_float=True)==7.3459e+22

def test_3():
	#test small calculation
	assert calculate('1/10000.')	== .0001

def test_4():
	#test returns float if actual float
	assert isinstance(calculate('current temperature in paris', return_float=True), float)

def test_5():
	#tests retunrs string if not possible to convert to float
	assert isinstance(calculate('what is the california state flower', return_float=True), unicode)	


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='CalCalculate Input')
	parser.add_argument('inString', help ='Need to ask your question')
	parser.add_argument('-t', action='store_true', default=False, dest='askAPI', help='Set -t if you want to push question to API')
	parser.add_argument('-f', action='store_true', default=False, dest='floatOut', help='set -f if you want output to be float')

	results = parser.parse_args()
	qAnswer = calculate(results.inString, askAPI=results.askAPI, return_float=results.floatOut)
	



#question ='how much wood could a woodchuck chuck if a woodchuck could chuck wood?'
#return_float = False
#askAPI = False
#def calculate(question, return_float=False, askAPI=False):


