# Demonstration: NameError and AttributeError Suggestions in Python 3.10+

# Example 1: NameError
print("=== NameError Example ===")
developer_name = "Sahitya Singh"
try:
    print(developer_name)  # Mistyped variable name
except NameError as e:
    print("Error:", e)
    print("Fixed Value:", developer_name)
# Example 2: AttributeError
print("\n=== AttributeError Example ===")
message = "Welcome to Hacktoberfest!"
try:
    print(message.upper())  # Mistyped method name
except AttributeError as e:
    print("Error:", e)
    print("Fixed Value:", message.upper())
