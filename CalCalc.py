def calculate(inString):
    comp = re.compile("[a-zA-Z]")
    if (comp.search(inString)==None):
        try:
            print eval(inString)
        except IOError, e:
            pass