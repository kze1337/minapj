import disnake
from disnake.ext import commands

import string
import random
import time

import json
import os

class KeyUtils:

    # Function to generate a random string in the format "XXXX-XXXX-XXXX-XXXX"
    def generate_random_string():
        random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        formatted_string = '-'.join([random_string[i:i+4] for i in range(0, len(random_string), 4)])
        return formatted_string