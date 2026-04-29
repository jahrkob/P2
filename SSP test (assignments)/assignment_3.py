def mySqrt(number, guess, step, tol):
	#We need to take out negative numbers...
	if (number<0):
		print('Error - we do not work with complex numbers here...')
		return float("NaN")
		
	#If we set guess to zero, we have to provide a number - we assume this is the initial call
	if (guess==0):
		if (number>1):        #If we have numbers larger than one, we can safely guess half as the sqrt
			guess=0.5*number
		else:
			guess=number*2	  #If we have numbers smaller than one, we need to double our guess
		
	tmp = guess*guess		  #Now compute the square of our guess
	if (abs(tmp-number)<tol):	  #Check if the (guess^2 - number) is lower than our tolerance level
		return guess
	else:
		if (guess**2>number):	  #If our guess was too high, then iterate by calling ourselves again with a slightly lower guess
			return mySqrt(number, (1-step)*guess, step, tol)
		else:				  #Else, our guess was too small, we need to increase the guess for our next call
			return mySqrt(number, (1+step)*guess, step, tol)
			

values = (-4, 0, 0.5, 1, 3, 9, 34)
for testVal in values:
    print('Squareroot of '+str(testVal)+' is ')
    print(mySqrt(testVal,0,0.01, 0.001))
