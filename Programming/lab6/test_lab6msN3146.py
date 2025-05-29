import pytest
from lab6msN3146 import MyDeque, FormatError, UndoError, RedoError

def test_append():
    dq = MyDeque()
    dq.append('А123АА123')
    assert dq == MyDeque(['А123АА123'])
    dq.append('В333ВВ333')
    assert dq == MyDeque(['А123АА123', 'В333ВВ333'])

def test_appendleft():
    dq = MyDeque()
    dq.appendleft('А123АА123')
    assert dq == MyDeque(['А123АА123'])
    dq.appendleft('В333ВВ333')
    assert dq == MyDeque(['В333ВВ333', 'А123АА123'])

def test_pop():
    dq = MyDeque(['А123АА123', 'В333ВВ333'])
    assert dq.pop() == 'В333ВВ333'
    assert dq == MyDeque(['А123АА123'])

def test_popleft():
    dq = MyDeque(['А123АА123', 'В333ВВ333'])
    assert dq.popleft() == 'А123АА123'
    assert dq == MyDeque(['В333ВВ333'])

def test_insert():
    dq = MyDeque(['А123АА123', 'В333ВВ333'])
    dq.insert(1, 'А456АА456')
    assert dq == MyDeque(['А123АА123', 'А456АА456', 'В333ВВ333'])

def test_remove():
    dq = MyDeque(['А123АА123', 'В333ВВ333'])
    dq.remove('А123АА123')
    assert dq == MyDeque(['В333ВВ333'])

def test_clear():
    dq = MyDeque(['А123АА123', 'В333ВВ333'])
    dq.clear()
    assert dq == MyDeque()

def test_undo_redo():
    dq = MyDeque(['А123АА12'])
    dq.append('В333ВВ333')
    assert dq == MyDeque(['А123АА12', 'В333ВВ333'])
    dq.undo()
    assert dq == MyDeque(['А123АА12'])
    dq.redo()
    assert dq == MyDeque(['А123АА12', 'В333ВВ333'])

def test_exceptions():
    dq = MyDeque()
    with pytest.raises(FormatError):
        dq.append('hren\'')
    with pytest.raises(UndoError):
        dq.undo()
    dq.append('А123АА123')
    with pytest.raises(RedoError):
        dq.redo()

def test_type_error():
    dq = MyDeque()
    with pytest.raises(TypeError):
        dq.append(123) 
    with pytest.raises(TypeError):
        dq.appendleft({'А123АА123'})
    with pytest.raises(TypeError):
        dq.insert(0, ['В333ВВ333'])
