import pandas as pd


#  Series is essentially a one-dimensional array-like object that can hold data
#   of any type (integers, floats, strings, etc.).
# Each element in a Series is associated with an index, which allows for easy
#   data retrieval and manipulation.
# You can create a Series from various data types, including lists, dictionaries
#   and NumPy arrays.

data = [20, 40, 30, 10]
# Creating a Series from a list
series = pd.Series(data)

print(series)
