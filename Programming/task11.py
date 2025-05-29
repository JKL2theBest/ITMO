import sys
import re

def main():
    filename = sys.argv[1]
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            groups = re.findall(r'\s{2,}', line)
            print(len(groups))

if __name__ == '__main__':
    main()
