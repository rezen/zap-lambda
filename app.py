#!/usr/bin/env python
import sys

# Also PYTHONPATH
# https://joarleymoraes.com/hassle-free-python-lambda-deployment/
sys.path.append('vendor/')
import os
# os.environ['LD_LIBRARY_PATH'] = '/app'

from flask import Flask, request, render_template, redirect, abort
from flask_httpauth import HTTPBasicAuth
import boto3
from flask_wtf.csrf import CSRFProtect
import uuid
from secrets import SecretStore, generate_string
from datetime import datetime
import lambda_wsgi

config = {
  'HIDE_CONTROLS': os.environ.get('HIDE_CONTROLS', '1') in ["1", "true", "t", "y", "Y"],
  'DYNAMODB_PREFIX': os.environ.get('DYNAMODB_PREFIX', 'share-secrets'),
  'GENERATES_SECRET': os.environ.get('GENERATES_SECRET', '1') in ["1", "true", "t", "y", "Y"],
  'SECRET_KEY': os.environ.get('SECRET_KEY'),
  'MAX_VIEWS': os.environ.get('MAX_VIEWS', 7),
  'MAX_HOURS': os.environ.get('MAX_HOURS', 24),
  'REQUIRE_PASSWORD': os.environ.get('REQUIRE_PASSWORD', '0') in ["1", "true", "t", "y", "Y"],
  'IS_LOCAL': os.environ.get('IS_LOCAL', '0') in ["1", "true", "t", "y", "Y"],
}

config['MAX_VIEWS'] = int(config['MAX_VIEWS'])
config['MAX_HOURS'] = int(config['MAX_HOURS'])

def setup_flask():
    csrf = CSRFProtect()
    http = Flask(__name__)
    for key, value in config.iteritems():
        http.config[key] = value
    csrf.init_app(http)
    http.secret_key = os.environ.get('SECRET_KEY', 'Ur4BuIn5I0noe9oAshZK') # @todo
    return http

app = setup_flask()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
def index():

@app.route('/s/<key>', methods=['GET', 'POST'])
def view_secret(key):

@app.route('/s/<key>', methods=['DELETE'])
def delete_secret(key):

@app.route('/p/<key>', methods=['GET'])
def share_secret(key):


@app.route('/create', methods=['POST'])
def create_secret():
    

def handler(event, context):
    return lambda_wsgi.handle_request(app, event, context)

def main():
    app.run(debug=True, host='0.0.0.0')

if __name__ == '__main__':
    main()
