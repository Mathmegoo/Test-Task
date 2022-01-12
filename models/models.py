from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.sql.sqltypes import Boolean
from models.database import Base



class Site_users(Base):
    __tablename__ = 'site_users'

    id = Column(Integer, unique=True, primary_key=True, nullable=False, autoincrement=True)
    login = Column(String, unique=True, nullable=False)# почта пользоватя. Можно будет валидировать регулярными выражениями.
    nickname = Column(String, unique=True, nullable=False)
    passwordu = Column(String, nullable=False)# Пароль
    level_of_access = Column(Integer, nullable=False) # --> Увидел свою ошибку в последний момент, 
                                                      # надежнее было бы использовать булевый тип, 
                                                      # т.к. у нас всего два варианта, либо админ, либо нет
    visibility = Column(Boolean, nullable=False) #Видимость пользователя. При удалении данные не будут удалены, 
                                                 # дабы не нарушать структуру бд, пользователь просто не будет отображаться.
    def __repr__(self) -> str:
        info: str = f'Site_user [ID: {self.id}, login: {self.login}, nickname: {self.nickname}, \
        passwordu: {self.passwordu}, level_of_access: {self.level_of_access}] '
        return info