from prometheus_client import (
    Gauge, Enum, generate_latest)

from paste.translogger import TransLogger
from flask import Flask, Response
from dataclasses import dataclass
from waitress import serve

import configparser
import requests
import logging
import socket


# Config class
@dataclass
class Config:
    IP: str
    URL: str
    Port: int
    MetricPort: int

  
# Initialize

parser = configparser.ConfigParser()
parser.read('patroni_exporter.conf')

conf = Config(IP=parser['DEFAULT']['IP'],
            URL='http://' + parser['DEFAULT']['IP'] + ':' + parser['DEFAULT']['Port'],
            Port=int(parser['DEFAULT']['Port']),
            MetricPort=int(parser['DEFAULT']['METRIC_PORT']))


# Setup Metrics
# see https://github.com/prometheus/client_python


graphs  = {}
graphs['lag'] = Gauge('patroni_exporter_replica_lag', "Replica Lag of the current node")
graphs['lag_mb'] = Gauge('patroni_exporter_replica_lag_mb', "Replica Lag of the current node in MB")
graphs['timeline'] = Gauge('patroni_exporter_node_timeline', "Timeline of the current node")
graphs['check'] = Enum('patroni_exporter_running_check', 'Check if This script is running', states=['running', 'stopped'])
graphs['role'] = Enum('patroni_exporter_role', "Role of the current node", states=['leader', 'replica'])
graphs['health'] = Enum('patroni_exporter_health', "Health of the current node", states=['OK', 'ERROR'])
graphs['liveness'] = Enum('patroni_exporter_liveness', "Liveness of the current node", states=['OK', 'ERROR'])
graphs['state'] = Enum('patroni_exporter_state', "State of the current node", states=['running', 'stopped'])

app = Flask(__name__)

# Scraping Function
def scrape():
    global graphs

    # Get General Node info
    try:
        node = requests.get(f'{conf.URL}/patroni')
        data = node.json()
    except Exception as e:
        # if we cant reach this endpoint, something is wrong
        for i in graphs.items():
            if isinstance(i[1], Gauge):
                i[1].set(0)
            elif isinstance(i[1], Enum):
                i[1].set('ERROR')    
        

    graphs['role'].state(data['role'])
    graphs['state'].state(data['state'])
    graphs['timeline'].set(data['timeline'])
    # Get HTTP status code based metrics
    
    try:
        health = requests.get(f'{conf.URL}/health')
        if health.status_code == 200:
            graphs['health'].state('OK')
        elif health.status_code != 200:
            graphs['health'].state('ERROR')
    except Exception as e:
        graphs['health'].state('ERROR')

    try:
        liveness = requests.get(f'{conf.URL}/liveness')
        if liveness.status_code == 200:
            graphs['liveness'].state('OK')
        elif liveness.status_code != 200:
            graphs['liveness'].state('ERROR')
    except Exception as e:
            graphs['liveness'].state('ERROR')
        
    
    # Metrics we can only get over the /cluster endpoint
    cluster = requests.get(f'{conf.URL}/cluster').json()
    for member in cluster["members"]:
        
        if member['name'] == socket.gethostname():
            # these metrics are only for replicas
            if data.get('role') == 'replica':

                graphs['lag'].set(member['lag'])
                graphs['lag_mb'].set(member['lag']/1024/1024)
                
    return graphs


# Main Route for Prometheus Metrics    
            
@app.route('/metrics')
def request():

    node = scrape()
    res = []

    for _k, v in node.items():
        res.append(generate_latest(v))

    graphs['check'].state('running')
    return Response(res, mimetype='text/plain')

@app.route('/')
def root():
    return Response('Patroni Exporter @ /metrics\n', mimetype='text/plain')

if __name__ == '__main__':
    # Setup logging
    logger = logging.getLogger('waitress')
    logger.setLevel(logging.INFO)
    
    # Start App using Waitress and Paste TransLogger
    serve(TransLogger(app, setup_console_handler=False), host='0.0.0.0', port=conf.MetricPort)