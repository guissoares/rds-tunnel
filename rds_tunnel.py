# -*- coding: utf-8 -*-

import boto3
import json
import yaml
import os
import subprocess

try:
    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    config = {}

profiles = boto3.session.Session().available_profiles

#client = session.client('rds',
#    region_name='us-east-1'
#)
#r = client.describe_db_clusters()
##print(json.dumps(r, indent=4, default=str))
#print([x['DBClusterIdentifier'] for x in r['DBClusters']])

class AWS():

    def __init__(self):
        self.session = None
        self.db_clusters = None

aws = AWS()

def get_db_clusters():
    try:
        client = aws.session.client('rds')
        r = client.describe_db_clusters()
    except Exception as e:
        sg.popup_ok(e)
        return []
    aws.db_clusters = {x['DBClusterIdentifier']: x for x in r['DBClusters']}
    return list(aws.db_clusters.keys())

def create_tunnel(host, local_port):
    try:
        profile = config.get('profile')
        region = config.get('region')
        target = config.get('target')
        port = config.get('port', 5432)
        args = ['aws', 'ssm', 'start-session']
        if region:
            args += ['--region', region]
        if target:
            args += ['--target', target]
        args += ['--document-name', 'AWS-StartPortForwardingSessionToRemoteHost']
        args += ['--parameters', f'host={host},portNumber={port},localPortNumber={local_port}']
        if profile:
            os.environ['AWS_PROFILE'] = profile
        if os.name == 'nt': # Verifica se é Windows
            subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(['gnome-terminal', '--'] + args)
    except Exception as e:
        sg.popup_ok(e)


import PySimpleGUI as sg

sg.theme('DarkGrey')

layout = [
    [
        sg.Text('Profile: ', tooltip='Profile com as credenciais para acessar e listar os BDs do RDS'),
        sg.Combo(values=profiles, default_value='default', enable_events=True, readonly=True, size=(32,1), key='-PROFILE-')
    ],
    [
        sg.Text('Region: ', tooltip='Região AWS onde estão os BDs do RDS'),
        sg.Input(default_text='us-east-1', expand_x=True, key='-REGION-')
    ],
    [
        sg.Text('DB Cluster: ', tooltip='Banco do RDS com o qual se dará a conexão'),
        sg.Combo(values=[], default_value=None, readonly=True, enable_events=True, expand_x=True, key='-DBCLUSTER-')
    ],
    [
        sg.Text('Local port: ', tooltip='Porta local com a qual a conexão será associada'),
        sg.Input(default_text=None,  size=(5,1), enable_events=True, key='-PORT-'),
        sg.Button(button_text="Criar túnel", disabled=True, key='-CREATE-')
    ]
]

icon = b'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAAl1JREFUaENjZBjigHGIu59h1AMDHYOjMTBsYkArdCoPk5SCJRMTM\
    zM+TzGxMv5VlZc5vjpb+ws1PE9xEgI5/Bs7czLDf4YKXlG5fwxMTFL4Hcb4VFVJjIPhP8MUZra//avTTT5S4hGyPQBz+P///ysZGRjFQY7gFZV7RqQHpKGOfgv\
    yyL8/DBM2FBp+IMcjJHsAm8NhFpPhAbDW/wz/3zH+Z5xMjkdI8oC4W44ih6jWEkYGJitsoUWuB2Bm/fn379iDR29iLvW43yc2Noj2gJBnLh/7X8Yj7MLqfxiYm\
    A1p4YG///6ev/fgDQcD2x/ryx0+74nxBFEeMDZOY30uwrmVgYHBlU1I7TyNPWDIwMB48C/fR7drDWG/CHmCKA9IuedPY2BgyAQZRh8PgJ0973KfRzLFHpD0yHd\
    n/M+wA2YQHT3AwMT43+Nir+dOfJ4gGAPSHvmh//8zrBoIDzAw/A+73Oe5etQDozGAkgbATQlYTYwiAy1GkYro0STEwDCaiTGKkNEkhJqjCNV0o0loNAmN1sSjb\
    SG0XDBajI4Wo3ToUsICebQxx8Aw5LuUoMgciE49IwPj3Et97imEmjoE+8RgAxwaWKTY32+j27DKf4YDf/k/uVNtWAXkB3oObDH/Y7e6MMGRqLFS4mIAGo9Demg\
    RlhbFYxdxc/7/lgIaTmdgYJBATqMUjI2CR6nJGW4nKQaQHYvNI2R4gGyHw9xCtgewxciQmuBAL97Uk+bysvJKWBAzxSSnLn9iU7LGZ0JFJDHyFMcAMZbQUs2oB\
    2gZusSYPRoDxIQSLdUM+RgAAKiaTE8kkkMFAAAAAElFTkSuQmCC'
    
sg.set_global_icon(icon)


window = sg.Window(
    'Criar túnel RDS',
    layout=layout,
    #icon=icon,
    finalize=True
)
window['-REGION-'].bind("<Return>", "ENTER-")
window['-REGION-'].bind("<KP_Enter>", "ENTER-")


def update_db_clusters(values):
    aws.session = boto3.session.Session(profile_name=values['-PROFILE-'], region_name=values['-REGION-'])
    window['-DBCLUSTER-'].update(values=get_db_clusters())

def update_button(values):
    if values['-PROFILE-'] and values['-REGION-'] and values['-DBCLUSTER-'] and values['-PORT-']:
        window['-CREATE-'].update(disabled=False)
    else:
        window['-CREATE-'].update(disabled=True)

event, values = window.read(timeout=0)
update_db_clusters(values)

while True:
    event, values = window.read()
    #print(event)
    #print(values)
    if event in (None, 'Exit'):
            print("[LOG] Clicked Exit!")
            break
    elif event in {'-PROFILE-', '-REGION-ENTER-'}:
        update_db_clusters(values)
    elif event == '-CREATE-':
        host = aws.db_clusters[values['-DBCLUSTER-']]['Endpoint']
        create_tunnel(host, values['-PORT-'])
    update_button(values)
window.close()
