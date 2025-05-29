import argparse
import os
import random
import string
import sys
import re
import struct

def generate_random_domain():
    domain = ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(3, 63)))
    if random.choice([True, False]):
        domain += '.' + ''.join(random.choices(string.ascii_lowercase, k=random.randint(2, 6)))
    domain += '.' + ''.join(random.choices(string.ascii_lowercase, k=random.randint(2, 6)))
    return domain

def generate_random_data(num_lines=None):
    num_lines = num_lines if num_lines else random.randint(10, 1000)
    return [generate_random_domain() for _ in range(num_lines)]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="store_true",
                        help="вывести ФИО и группу студента, который выполнил работу, и информацию о варианте задания")
    parser.add_argument("-n", "--num", type=int, default=None,
                        help="количество строк для записи в файл")
    parser.add_argument("filename", nargs='?', default=None,
                        help="имя файла, в который программа записывает набор случайных строк")
    args = parser.parse_args()

    if args.version:
        print("Суханкулиев Мухаммет, гр. N3146")
        print("Вариант: 4-2")
        sys.exit(0)

    if args.filename is None:
        print("Ошибка: не указано имя файла", file=sys.stderr)
        sys.exit(1)

    try:
        data = generate_random_data(args.num)
        data_bytes = [s.encode('utf-8') + b'\0' for s in data]
        data_area = b''.join(data_bytes)
        data_offsets = [sum(len(s) for s in data_bytes[:i]) for i in range(len(data_bytes))]
        index_area = struct.pack('H'*len(data_offsets), *data_offsets)
        offset_field = struct.pack('I', len(data_area))
        random_data_area = bytes(random.getrandbits(8) for _ in range(random.randint(0, 1000)))

        with open(args.filename, 'wb') as f:
            f.write(offset_field)
            f.write(data_area)
            f.write(random_data_area)
            f.write(index_area)

        print("Сгенерированные данные:")
        for i, (s, offset) in enumerate(zip(data, data_offsets)):
            print(f"Строка {i+1}, смещение (offset) {offset}: {s}")
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
