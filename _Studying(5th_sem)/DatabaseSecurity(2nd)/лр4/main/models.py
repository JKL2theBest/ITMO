from sqlalchemy import (Column, Integer, String, Text, DateTime, Numeric,
                        ForeignKey, CHAR, create_engine, func, LargeBinary)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import OperationalError

Base = declarative_base()

# --- Описание ORM-моделей для таблиц БД ---

class Zone(Base):
    __tablename__ = 'zone'
    zoneid = Column('ZoneID', Integer, primary_key=True)
    zonename = Column('ZoneName', String(100), nullable=False)
    boundaries = Column('Boundaries', Text)

class Tariff(Base):
    __tablename__ = 'tariff'
    tariffid = Column('TariffID', Integer, primary_key=True)
    tariffname = Column('TariffName', String(50), nullable=False)
    priceperminute = Column('PricePerMinute', Numeric(5, 2), nullable=False)
    startprice = Column('StartPrice', Numeric(5, 2), nullable=False, server_default='0.00')

class User(Base):
    __tablename__ = '"User"'
    userid = Column('UserID', Integer, primary_key=True)
    fio = Column('FIO', String(255), nullable=False)
    phonenumber = Column('PhoneNumber', String(20), unique=True, nullable=False)
    email = Column('Email', String(100), unique=True, nullable=False)
    registrationdate = Column('RegistrationDate', DateTime, nullable=False, server_default=func.now())
    lastlogin = Column('LastLogin', DateTime)

class Scooter(Base):
    __tablename__ = 'scooter'
    scooterid = Column('ScooterID', Integer, primary_key=True)
    model = Column('Model', String(50), nullable=False)
    chargelevel = Column('ChargeLevel', Integer, nullable=False)
    status = Column('Status', String(20), nullable=False, server_default='available')
    zoneid = Column('ZoneID', Integer, ForeignKey('zone.ZoneID'))
    zone = relationship("Zone")

class Maintenance(Base):
    __tablename__ = 'maintenance'
    maintenanceid = Column('MaintenanceID', Integer, primary_key=True)
    scooterid = Column('ScooterID', Integer, ForeignKey('scooter.ScooterID'), nullable=False)
    maintenancetype = Column('MaintenanceType', String(100), nullable=False)
    maintenancedate = Column('MaintenanceDate', DateTime, nullable=False)
    description = Column('Description', Text)
    scooter = relationship("Scooter")

class Trip(Base):
    __tablename__ = 'trip'
    tripid = Column('TripID', Integer, primary_key=True)
    userid = Column('UserID', Integer, ForeignKey('"User".UserID'), nullable=False)
    scooterid = Column('ScooterID', Integer, ForeignKey('scooter.ScooterID'), nullable=False)
    tariffid = Column('TariffID', Integer, ForeignKey('tariff.TariffID'), nullable=False)
    starttime = Column('StartTime', DateTime, nullable=False)
    endtime = Column('EndTime', DateTime)
    cost = Column('Cost', Numeric(8, 2))
    user = relationship("User")
    scooter = relationship("Scooter")
    tariff = relationship("Tariff")

class Payment(Base):
    __tablename__ = 'payment'
    paymentid = Column('PaymentID', Integer, primary_key=True)
    tripid = Column('TripID', Integer, ForeignKey('trip.TripID'), nullable=False)
    amount = Column('Amount', Numeric(8, 2), nullable=False)
    paymentdate = Column('PaymentDate', DateTime, nullable=False, server_default=func.now())
    paymentstatus = Column('PaymentStatus', String(20), nullable=False, server_default='completed')
    trip = relationship("Trip")

class ActionLog(Base):
    __tablename__ = 'action_log'
    log_id = Column(Integer, primary_key=True)
    operation_type = Column(CHAR(1), nullable=False)
    operation_time = Column(DateTime, nullable=False, server_default=func.now())
    db_user = Column(Text, nullable=False, server_default=func.current_user())
    table_name = Column(Text, nullable=False)
    old_data = Column(Text)
    new_data = Column(Text)

class UserApiKey(Base):
    __tablename__ = 'user_api_keys'
    key_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('"User".UserID'), nullable=False)
    api_key = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


# --- Функция для создания сессии подключения к БД ---

def get_session(role: str, password: str):
    """
    Создает и возвращает сессию SQLAlchemy для указанной роли PostgreSQL.
    Это ключевой механизм безопасности, использующий ролевую модель СУБД.

    :param role: Имя роли (пользователя) в PostgreSQL.
    :param password: Пароль для этой роли.
    :return: Объект сессии SQLAlchemy или None в случае ошибки подключения.
    """
    db_url = f"postgresql+psycopg2://{role}:{password}@localhost:7777/scooter_rental_db"
    try:
        engine = create_engine(db_url)

        connection = engine.connect()
        connection.close()
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal()
    except OperationalError as e:
        print(f"ОШИБКА: Не удалось подключиться к базе данных для пользователя '{role}': {e}")
        return None