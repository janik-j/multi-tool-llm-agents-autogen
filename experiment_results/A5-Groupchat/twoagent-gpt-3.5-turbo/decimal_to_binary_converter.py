# filename: decimal_to_binary_converter.py

def decimal_to_binary(decimal_num):
    return bin(decimal_num)[2:]

# Convert 100 to binary
decimal_number = 100
binary_number = decimal_to_binary(decimal_number)

# Save the result to a file
with open('decimal_to_binary.txt', 'w') as file:
    file.write(binary_number)