import os
number = int(os.getenv("NUMBER", 0))
Cube = number * number * number
print(f"Number is: {number}")
print(f"Cube is: {Cube}")