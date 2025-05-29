class OnlyPrime:
    def __init__(self):
        self._value = None

    def __get__(self, instance, owner):
        return self._value

    def __set__(self, instance, value):
        if not self.is_prime(value):
            raise AttributeError(f'Only prime numbers are acceptable: {value} is not prime')
        self._value = value

    def is_prime(self, n):
        if n <= 1:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(n ** 0.5) + 1, 2):
            if n % i == 0:
                return False
        return True


def test_1():
    print('\ntest_1:')
    class Test1:
        id = OnlyPrime()
    

    t1 = Test1()

    print(f'{t1.id=}')              # None

    try:
        t1.id = 5                   # OK
    except AttributeError as e:
        print(f'ERROR: {e}')

    print(f'{t1.id=}')

    try:
        t1.id = 12                  # Ошибка
    except AttributeError as e:
        print(f'ERROR: {e}')
    
    print(f'{t1.id=}')

    try:
        t1.id = 2                   # OK
    except AttributeError as e:
        print(f'ERROR: {e}')
    
    print(f'{t1.id=}')

def test_2():
    print('\ntest_2:')
    class Test2:
        n = OnlyPrime()
    
        def __init__(self, n):
            self.n = n

    t2 = Test2(11)                  # OK

    t3 = Test2(10)                  # Ошибка


def main():
    test_1()
    test_2()

if __name__ == '__main__':
    main()