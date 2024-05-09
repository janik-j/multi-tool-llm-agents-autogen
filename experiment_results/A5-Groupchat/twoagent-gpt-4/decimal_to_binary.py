# filename: decimal_to_binary.py

def decimal_to_binary(n):
    return bin(n).replace("0b", "")

def save_to_file(filename, data):
    with open(filename, 'w') as f:
        f.write(data)

if __name__ == "__main__":
    decimal_number = 100
    binary_number = decimal_to_binary(decimal_number)
    save_to_file("decimal_to_binary.txt", binary_number)