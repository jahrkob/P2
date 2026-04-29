def checkInputValue(value):
	if (value>3):
		if (value<10):
			print("Value is larger than 3 and smaller than 10")
		else:
			print("Value is larger than or equal to 10")
	else:
		if (value<0):
			print("Value is negative")
		else:
			print("Value is between zero and three")

values = (-5, -0.4, 0, 0.7, 1, 4, 3452)
for valToBeChecked in values:
    print('For value '+str(valToBeChecked))
    checkInputValue(valToBeChecked)


