# ANSI color codes
class Color:
    RESET = '\033[0m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'

# def print_all_colors():
#     for color_name, color_code in vars(Color).items():
#         if color_name.isupper() and isinstance(color_code, str):
#             print(f"{color_code}This text is {color_name.lower().replace('_', ' ')}{Color.RESET}")
#
# # Call the function to print all colors
# print_all_colors()

print("\033[1mThis text is bold\033[0m")
print('\033[4m'+"This text is bold")