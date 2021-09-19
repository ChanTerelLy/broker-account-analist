# BAA service

Last deployment status: <br>
<img src="https://github.com/ChanTerelLy/broker-account-analist/actions/workflows/pipline.yml/badge.svg?branch=master"></img>


**BAA** - Broker Account Analist system.   
It's help to organize money assets and investment capital in one app.  
Current support integrations:
- SBERBANK Broker
- Tinkoff Broker
- Money Manager
- MOEX exchange

## Setup
---
```
pip install pipenv
pipenv install
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**To run using docker-compose**
---
```docker-compose up```
