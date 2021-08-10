import os
from dotenv import load_dotenv
load_dotenv()
from baa.settings.ssm_parameter_store import SSMParameterStore
import boto3

my_session = boto3.session.Session()
my_region = my_session.region_name
ssm_client = boto3.client('ssm', region_name=os.getenv('AWS_REGION'))
store = SSMParameterStore(ssm_client=ssm_client, prefix='/projects/baa/env/')

def get_env(val, **kwargs):
    return store.get(val,**kwargs)

os.environ['SECRET_KEY'] = get_env('SECRET_KEY')
os.environ['DEBUG'] = get_env('DEBUG')
os.environ['DB_NAME'] = get_env('DB_NAME')
os.environ['DB_USERNAME'] = get_env('DB_USERNAME')
os.environ['DB_PASSWORD'] = get_env('DB_PASSWORD')
os.environ['DB_HOSTNAME'] = get_env('DB_HOSTNAME')
os.environ['DB_PORT'] = get_env('DB_PORT')
os.environ['DB_ENGINE'] = get_env('DB_ENGINE')
os.environ['REDIS_URL'] = get_env('REDIS_URL')
os.environ['EMAIL_HOST'] = get_env('EMAIL_HOST')
os.environ['EMAIL_PORT'] = get_env('EMAIL_PORT')
os.environ['EMAIL_HOST_USER'] = get_env('EMAIL_HOST_USER')
os.environ['EMAIL_HOST_PASSWORD'] = get_env('EMAIL_HOST_PASSWORD')
os.environ['ADMIN_EMAIL'] = get_env('ADMIN_EMAIL')
os.environ['GOOGLE_SERVICE_REDIRECT_URI'] = get_env('GOOGLE_SERVICE_REDIRECT_URI')
os.environ['SOCIAL_AUTH_GOOGLE_OAUTH_2_KEY'] = get_env('SOCIAL_AUTH_GOOGLE_OAUTH_2_KEY')
os.environ['SOCIAL_AUTH_GOOGLE_OAUTH_2_SECRET'] = get_env('SOCIAL_AUTH_GOOGLE_OAUTH_2_SECRET')
os.environ['GOOGLE_CONFIG'] = get_env('GOOGLE_CONFIG')
os.environ['STEP_FUNCTION_ARN'] = get_env('STEP_FUNCTION_ARN')

from .base import *

SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
ALLOWED_HOSTS = ['*']
MIDDLEWARE.append('aws_xray_sdk.ext.django.middleware.XRayMiddleware')
INSTALLED_APPS.append('aws_xray_sdk.ext.django')
XRAY_RECORDER = {
    'AUTO_INSTRUMENT': True,
    'AWS_XRAY_CONTEXT_MISSING': 'LOG_ERROR',
    'AWS_XRAY_TRACING_NAME': 'BAA',
    'PLUGINS': ('ECSPlugin','EC2Plugin'),
    'SAMPLING': False,
}