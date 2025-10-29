import fileinput


file_path = "IPython/terminal/shortcuts/auto_suggest.py"



for line in fileinput.input(file_path, inplace=True):
    if "newline_autoindent" in line:
        print("newline_autoindent = 2") 
    else:
        print(line, end="")
