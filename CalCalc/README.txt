
CalCalc README
---------------------------
To add CalCalc module open terminal cd into directory and type: python setup.py install or sudo python setup.py install if you need permissions

CalCalc main function is calculate which accepts any string and attempts to evaluate the request. If it's an easy math calculation, calculate will return answer using eval(), if this is not possible it will query wolfram alpha. 

Calculate may be imported as a function by using the install code described above or may be used from the command line. 

From the command line it accepts the following options:
-t -- will force query to wolfram alpha
-f -- will force return a float value

To test if the function is working properly you may use the nosetests package within the project directory by typing: nosetests CalCalc