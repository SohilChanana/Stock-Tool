"""
ansi_format.py

This module defines ANSI escape codes for styling command-line text.
It provides a consistent look for:
  - Menu options
  - Awaiting input prompts
  - Error messages
  - Success messages
  - Labels

Feel free to adjust the color choices or effects as needed.
"""

# ANSI escape sequences
RESET = "\033[0m"

# Basic styles
BOLD = "\033[1m"
UNDERLINE = "\033[4m"

# Colors
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Specific text styles for the app
MENU_OPTION = BOLD + BLUE    # Bold blue text for menu options
AWAITING_INPUT = CYAN        # Cyan text for input prompts
ERROR = BOLD + RED           # Bold red text for error messages
SUCCESS = BOLD + GREEN       # Bold green text for success messages
LABEL = BOLD + YELLOW        # Bold yellow text for labels

# Optionally, you might add additional styles, e.g.:
INFO = MAGENTA               # Magenta for informational messages

def style_menu_option(text: str) -> str:
    """Wrap the text for menu options styling."""
    return f"{MENU_OPTION}{text}{RESET}"

def style_input_prompt(text: str) -> str:
    """Wrap the text for awaiting input prompts styling."""
    return f"{AWAITING_INPUT}{text}{RESET}"

def style_error(text: str) -> str:
    """Wrap the text for error messages styling."""
    return f"{ERROR}{text}{RESET}"

def style_success(text: str) -> str:
    """Wrap the text for success messages styling."""
    return f"{SUCCESS}{text}{RESET}"

def style_label(text: str) -> str:
    """Wrap the text for label styling."""
    return f"{LABEL}{text}{RESET}"

def style_info(text: str) -> str:
    """Wrap the text for informational messages styling."""
    return f"{INFO}{text}{RESET}"
