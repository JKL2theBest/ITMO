import datetime

def time_before(format: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            print(datetime.datetime.now().strftime(format))
            return func(*args, **kwargs)
        return wrapper
    return decorator

@time_before('%d.%m.%y %H:%M:%S')
def test_1():
    print('test_1() called')

@time_before('%m/%d %Y %H:%M')
def test_2(*args, **kwargs):
    print(f'test_2() called: {args=}, {kwargs=}')
#
@time_before('%Y-%m-%d %H:%M:%S')
def test_3():
    print('test_3() called')

@time_before('%A, %B %d, %Y')
def test_4(*args, **kwargs):
    print(f'test_4() called: {args=}, {kwargs=}')

@time_before('%I:%M %p')
def test_5(*args):
    print(f'test_5() called: {args=}')
#
def main():
    test_1()
    test_2(11, 22, key1=33, key2=44)
    test_3()
    test_4(55, 66, key3=77, key4=88)
    test_5(99, 100)
    #

if __name__ == '__main__':
    main()
