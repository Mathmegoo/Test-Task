
from sqlalchemy import text
from sqlalchemy.orm import Session, query
from sqlalchemy.sql.operators import exists
from server import hash_password
from . import models 


# Надеюсь этот модуль не нуждается в комментариях, т.к. функции названы прямо, и в них не происходит ничего сложного.
# разные варианты поиска юзера по атрибутам




def get_visible_users(db: Session ):
    # Момент использования raw sql, как использовать его без алхимии, я не нашел даже в документации, видимо, плохо искал((
    return db.query(models.Site_users).filter(text("visibility == TRUE")).all()



def get_user_by_id( user_id: int, db: Session ):
    return db.query(models.Site_users).filter(models.Site_users.id == user_id).first()


def get_user_by_nickname( nickname: str, db: Session ):
    return db.query(models.Site_users).filter(models.Site_users.nickname == nickname).first()

def get_user_by_login( login: str, db: Session ):
    return db.query(models.Site_users).filter(models.Site_users.login == login).first()

def get_users(db: Session ):
    return db.query(models.Site_users).all()

def create_user( login, nickname, password, level_of_access, local_visibility, db: Session ):
    db_user = models.Site_users(login=login, nickname= nickname, passwordu = hash_password(password), 
    level_of_access = level_of_access, visibility = local_visibility)
    print(db)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# функции CRUD для администраторов
def change_level_of_access_to_admin(user, db: Session):
    user.level_of_access = 1
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def change_level_of_access_to_user(user, db: Session):
    user.level_of_access = 0
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(user, db: Session):
    user.visibility = False
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def recover_user(user, db: Session):
    user.visibility = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
