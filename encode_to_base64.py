import base64

# Read the file content
with open("alert.json", "rb") as file:
    file_bytes = file.read()

# Encode to base64
base64_string = base64.b64encode(file_bytes).decode("utf-8")

# Output the base64 string
print(base64_string)