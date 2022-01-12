import os
from fastapi import Depends
from sqlalchemy.orm.session import Session
from starlette.responses import HTMLResponse
from models.database import SQLALCHEMY_DATABASE_URL, create_db, SessionLocal
from fastapi import FastAPI, Form, Cookie , Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
from typing import Optional
import uvicorn
import hmac
import hashlib
import base64
import json
from models import models 
from models import crud



app = FastAPI()

templates = Jinja2Templates(directory='templates')
# Детали безопасности
SECRET_KEY = "8c680338db222af993a2a80fe2e1b269911ca701f1d5c7ec29dafb1dff3e1b9b"
PASSWORD_SALT = "d43955a5688a5f61688efd38cec0e97ce499e038163b994bcbaf13b938a6fd73"
#создает сессию с БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def sign_data(data: str) -> str:
# подписывает данные, чтобы отслеживать измененные куки, целее будем
    return hmac.new(
        SECRET_KEY.encode(),
        msg=data.encode(),
        digestmod=hashlib.sha256
    ).hexdigest().upper() 

# Узнает пользователя из зашифрованной куки
def get_username_from_signed_string(username_signed: str) -> Optional[str]:
    username_base64, sign = username_signed.split(".")
    username = base64.b64decode(username_base64.encode()).decode()
    valid_sign = sign_data(username)
    if hmac.compare_digest(valid_sign, sign):
        return username

# Сравнивает пароль с захешированным паролем (Верифицирует пароль)
def verify_password(password:str, password_hash: str) -> bool:
    return hashlib.sha256( (password + PASSWORD_SALT).encode()).hexdigest().lower() == \
    password_hash.lower()
# хэширует пароль
def hash_password(password: str) -> str:
    return hashlib.sha256( (password + PASSWORD_SALT).encode()).hexdigest().lower()




@app.get('/admin', response_class=HTMLResponse)
def admin_page (request : Request, username : Optional[str] = Cookie(default=None),  db : Session = Depends(get_db), ):
    try:   
        # узнаем из куки имя пользователя, по нему находим обьект пользователя,
        #  и дальше проверяем поле с его правами. если 1 - админ, если 0 - не админ.
        valid_username = get_username_from_signed_string(username)
        valid_user = crud.get_user_by_login(valid_username, db)
        print(valid_username)
        if valid_user.level_of_access == 1:
        
            vie_users = crud.get_users(db)
        
            responce = templates.TemplateResponse('admin.html', {"request" : request, "users" : vie_users})
            return responce
        # если не админ - отправляем ответ json, что он не админ
        else:
            return Response(
                json.dumps({
                    'success' : True,
                    'message' : f"Hello, you not admin("
                }), 
                media_type='application/json'
                )
    except:
        # Так же запрещаем вход для тех, у кого кука в принципе отсутсвует
        return Response(
                json.dumps({
                    'success' : True,
                    'message' : f"Hello, you not admin("
                }), 
                media_type='application/json'
                )







@app.get('/', response_class=HTMLResponse)
def index_page(request : Request, username : Optional[str] = Cookie(default=None), db : Session = Depends(get_db)):
    with open('templates/login.html', 'r') as f:
        login_page = f.read()
    
    # если  куки нет - отправляем страничку для входа
    if not username :
        return Response(login_page, media_type='text/html')
    
        
    # Если кука есть, пытаемся достать из нее логин
    valid_username = get_username_from_signed_string(username)
    # Если логин не достается, мы стираем эту куку (возможно поддельная) и отправлякм на страничку входа
    if not valid_username:
        responce = Response(login_page, media_type='text/html')
        responce.delete_cookie(key="username")
        return responce
    # ищем в БД логин, который достали из куки
    try:
            user = crud.get_user_by_login(valid_username,db) 
    # Если такого логина в бд нет, тоже  стираем ее и проси войти заново. для пользователя на страничке ничего не происходит
    except KeyError:
            responce = Response(login_page, media_type = 'text/html')
            responce.delete_cookie(key="username")
            return responce
    
    # Если все прошло успешно, забираем из бд всех видимых (не удаленных) пользователей и загружаем в шаблон
    vie_users = crud.get_visible_users(db)
    
    responce = templates.TemplateResponse('home.html', {"request" : request, "users" : vie_users} )
    return responce
     



@app.post('/login')
def process_login_page(username : str = Form(...), password : str = Form(...), db = Depends(get_db)):
    # Получаем из формочки логи и пароль, забираем из бд логин, даем вход на страницу
    verified_user = crud.get_user_by_login(username, db)
    print (verified_user)
    # Если пароль или логин не верен, оправляем json, что что то не так
    if not verified_user or not verify_password(password, verified_user.passwordu):

        
        return Response(
            json.dumps({
                'success' : False,
                'message' : "I don't know you!" 
            }), 
            media_type='application/json'
            )
    print(username)
    responce = Response(
            json.dumps({
                'success' : True,
                'message' : f"Hello, {verified_user.nickname}!" 
            }), 
            media_type='application/json'
            )
        

    username_signed = base64.b64encode(username.encode()).decode() + '.' + sign_data(username)
    
    responce.set_cookie(key="username", value=username_signed)
    return responce


# route регистрации 
@app.get('/reg')
def registration_func():
    with open('templates/reg.html', 'r') as f:
        reg_page = f.read()
    return Response(reg_page, media_type='text.html')

# Роут, принимающий форму регистрации
@app.post('/reg')
def process_login_page(username : str = Form(...), nickname : str =Form(...), password1 : str = Form(...),\
    password2 : str = Form(...), level_of_access: int = Form(...), visibility = True, db: Session = Depends(get_db)):
    if password1 == password2:
        successful = crud.create_user(username,nickname,password1, level_of_access, visibility, db)

    if successful:
       responce = Response(
        json.dumps({
            'success' : True,
            'message' : f"Hello, { username}"
        }),
        media_type='application/json')
    return responce 



# Принимающие роуты для админов.
# Делает пользователя админом по кнопке на админской страничке
@app.post('/do_admin')
def process_login_page(request : Request, userlogin: str = Form(...), db: Session = Depends(get_db)):
    user = crud.get_user_by_login(userlogin, db)
    crud.change_level_of_access_to_admin(user, db)
    vie_users = crud.get_visible_users(db)
    responce = templates.TemplateResponse('admin.html', {"request" : request, "users" : vie_users})
    return responce

# устанавливает атрибут level_of_access = 0, что запрещает ему доступ в админ-панель
@app.post('/do_user')
def process_login_page(request : Request, userlogin: str = Form(...), db: Session = Depends(get_db)):
    user = crud.get_user_by_login(userlogin, db)
    crud.change_level_of_access_to_user(user, db)
    vie_users = crud.get_visible_users(db)
    responce = templates.TemplateResponse('admin.html', {"request" : request, "users" : vie_users})
    return responce


# "Удаляет" пользователя. на самом деле просто убирает его из области видимости простых пользователей
@app.post('/delete_user')
def process_login_page(request : Request, userlogin: str = Form(...), db: Session = Depends(get_db)):
    user = crud.get_user_by_login(userlogin, db)
    crud.delete_user(user, db)
    vie_users = crud.get_users(db)
    responce = templates.TemplateResponse('admin.html', {"request" : request, "users" : vie_users})
    return responce

# Восстанавливает удаленного юзера
@app.post('/recover_user')
def process_login_page(request : Request, userlogin: str = Form(...), db: Session = Depends(get_db)):
    user = crud.get_user_by_login(userlogin, db)
    crud.recover_user(user, db)
    vie_users = crud.get_users(db)
    responce = templates.TemplateResponse('admin.html', {"request" : request, "users" : vie_users})
    return responce


#запуск сервера ювикорн при выполнении файла + создание бд, если ее не обнаружено.
if __name__ == "__main__":
    uvicorn.run("server:app", port=8000, host= "127.0.0.1", reload=True)
    db_is_created = os.path.exists(SQLALCHEMY_DATABASE_URL)
    if not db_is_created:
        create_db()

