def mySqrt(number, guess, step, tol):
	"""
	Estimates the squareroot down to a given tolerance (tol):
		number: value to estimate squareroot of
		guess: the current best guess (should be 0 when run)
		step: the rate of change (percentage of change for each iteration)
		tol: the tolerance the of the estimate
	return 'Recursion limit exceeded' if too many recursions occured
	return 'step size cant be zero or below' if step is zero or below
	return 'tolerance cant be under zero' if tol is set to negative values
	return 'no negative values tolerated >:C' if number is negative
	return 'guess cannot be negative' if guess is negative
	"""
	try:
		if step <= 0: # added for black box testing
			return 'step size cant be zero or below'
		elif tol < 0: # added for black box testing
			return 'tolerance cant be under zero'
		elif guess < 0:
			return 'guess cannot be negative'


		#We need to take out negative numbers...
		if (number<0):
			return 'no negative values tolerated >:C'
			
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
	except RecursionError:
		return 'Recursion limit exceeded'
	

if __name__ == '__main__':
	values = (-4, 0, 0.5, 1, 3, 9, 34)
	for testVal in values:
		print('Squareroot of '+str(testVal)+' is ')
		print(mySqrt(testVal,0,0.01, 0.001))
