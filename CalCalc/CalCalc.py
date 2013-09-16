import argparse
import re
import wolframalpha
import sys



def calculate(question, askAPI=False, return_float=False):
	comp = re.compile("[a-zA-Z]")
	if comp.search(question)==None and not askAPI:
		try:
			print eval(str(question))
		except IOError, e:
			pass
	else:
		
		client = wolframalpha.Client('UAGAWR-3X6Y8W777Q')
		res = client.query('%s' %question)
		ans = next(res.results).text
		if return_float:
			nums = re.compile("[0-9\+\-\*\^\.]+")
			ans = ans.encode('ascii', 'replace')
			ans=ans.replace('?', '*') 
			ans=ans.replace('^', '**')

			answer=re.findall(nums, ans)
			
			try:
				print 'asking wolframalpha'
				print eval(answer[0])
				return float(eval(answer[0]))


			except IOError, e:
				pass
				
		else:	
				print 'asking wolframalpha'
				print ans			

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


