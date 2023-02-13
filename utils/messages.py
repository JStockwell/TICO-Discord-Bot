# Created by JStockwell on GitHub
from datetime import datetime

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def post(message, err_flag):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if err_flag:
        print(f"{now} {bcolors.FAIL}ERROR     {bcolors.HEADER}bot.py {bcolors.ENDC}{message}")

    else:
        print(f"{now} {bcolors.OKBLUE}INFO     {bcolors.HEADER}bot.py {bcolors.ENDC}{message}")