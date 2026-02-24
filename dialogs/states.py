from aiogram.fsm.state import StatesGroup, State


class StartSG(StatesGroup):
    start = State()
    convert = State()
    contacts = State()
    date_select = State()
    fio = State()
    tel = State()
    guests = State()
    end = State()


class AddCarSG(StatesGroup):
    start = State()
    convert = State()
    price = State()
    bank = State()
    sbp = State()
    net = State()
    location = State()
    descr = State()
    info = State()
    confirm = State()
    finish = State()


class ProfileSG(StatesGroup):
    start = State()
    balance = State()


class BalanceSG(StatesGroup):
    start = State()
    balance = State()
    pay_photo = State()
    confirm = State()