import pandas as pd

# Sample DataFrame
users_data = {
    'name': ['Alice', 'Bob', 'Charlie', 'David'],
    'age': [24, 30, 22, 35],
    'city': ['New York', 'Los Angeles', 'New York', 'Chicago']
}
users_df = pd.DataFrame(users_data)
print(users_df)

# Filter for rows where age is greater than 25
filtered_df = users_df[users_df['age'] > 25]
print(filtered_df)