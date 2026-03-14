import os
number = int(os.getenv("NUMBER", 0))
square = number * number
print(f"Number is: {number}")
print(f"Square is: {square}")