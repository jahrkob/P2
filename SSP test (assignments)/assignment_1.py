def checkInputValue(value):
	"""
	Check which category the input falls into:
		1) Bigger than 10 (incl) -> "Value is larger than or equal to 10"
		2) Between 3 and 10 (excl, excl) -> "Value is larger than 3 and smaller than 10"
		3) between 0 and 3 (incl, incl) -> "Value is between zero and three"
		4) Negative value -> "Value is negative"
	Invalid input returns:
		"Not a number"
	"""

	if type(value) not in [int, float]: # added for black box testing 
		return "Not a number"

	if (value>3):
		if (value<10):
			return "Value is larger than 3 and smaller than 10"
		else:
			return "Value is larger than or equal to 10"
	else:
		if (value<0):
			return "Value is negative"
		else:
			return "Value is between zero and three"

if __name__ == '__main__':
	values = (-5, -0.4, 0, 0.7, 1, 4, 3452)
	for valToBeChecked in values:
		print('For value '+str(valToBeChecked))
		checkInputValue(valToBeChecked)
