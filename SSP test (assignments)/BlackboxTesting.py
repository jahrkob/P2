from assignment_1 import checkInputValue
from assignment_2 import bubbleSort
from assignment_3 import mySqrt
import math

def test_checkInputValue():
    assert checkInputValue(0) == "Value is between zero and three"
    assert checkInputValue(3) == "Value is between zero and three" # tests edge case
    assert checkInputValue(10) == "Value is larger than or equal to 10" # tests edge case
    assert checkInputValue(7) == "Value is larger than 3 and smaller than 10" # tests the between 3 and 10 case
    assert checkInputValue(-0.1) == "Value is negative" # tests both floats and negative numbers
    assert checkInputValue('one') == "Not a number" # tests outside testcase

def test_bubblesort():
    assert bubbleSort([1,2,3,4,5,6,7]) == [7,6,5,4,3,2,1] # tests an ideal use case
    assert bubbleSort([1,1.0,2,3,4,5,5,6]) == [6,5,5,4,3,2,1.0,1] # checks how duplicate values are handles
    assert bubbleSort([2**63,93/2,1,85]) == [2**63,85,93/2,1] # checks a not already ascending or descending array
    assert bubbleSort([2,5,3,'one',10]) == 'Array contains non number values' # checks invalid inputs

def test_mysqrt():
    assert mySqrt(9,0,0.000001,0.01) == 'Recursion limit exceeded' # checks exceeded recusion limit

    assert 2.99 <= mySqrt(9,0,0.01,0.01) <= 3.01 # checks tolerance

    assert math.sqrt(5)-0.01 <= mySqrt(5,0,0.01,0.01) <= math.sqrt(5)+0.01 # checks for non nice values
    assert math.sqrt(4.3)-0.01 <= mySqrt(4.3,0,0.01,0.01) <= math.sqrt(4.3)+0.01 # checks for non float values

    assert 3.9 <= mySqrt(16,2,0.01,0.1) <= 4.1 # checks for guess value higher than 0
    assert mySqrt(16,-1,0.01,0.1) == 'guess cannot be negative' # checks for guess value lower than 0

    assert mySqrt(25,0,0,0.01) == 'step size cant be zero or below' # checks for step value of zero
    assert mySqrt(36,0,-0.01,0.01) == 'step size cant be zero or below' # checks for step value lower than 0
    
    assert mySqrt(-1,0,0.1,0.01) == 'no negative values tolerated >:C'
    assert mySqrt(0,0,0.1,0.01) == 0
    assert 0.99 <= mySqrt(1,0,0.1,0.01) <= 1.01

#doing the of testing
test_checkInputValue()
test_bubblesort()
test_mysqrt()