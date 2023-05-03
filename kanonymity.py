import pandas as pd

# Function to generalize the data in a column
def generalize(column, level):
    if isinstance(column.iloc[0], int):
        return column.apply(lambda x: int(x/level)*level)
    else:
        return column.apply(lambda x: str(x)[:level])

# Function to delete data from a column
def suppress(column):
    return column.apply(lambda x: "*"*len(str(x)))

# Function to determine if a group complies with k-anonymity
def is_k_anonymous(group, k):
    return len(group) >= k