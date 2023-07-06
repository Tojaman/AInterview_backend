DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', #1
        'NAME': 'audio', #2
        'USER': 'root', #3                      
        'PASSWORD': '1234',  #4              
        'HOST': 'localhost',   #5                
        'PORT': '8000', #6
    }
}
SECRET_KEY ='기존 settings.py에 있던 시크릿키를 붙여넣는다'