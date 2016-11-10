#!/usr/bin/env python
import urllib2
import json
import argparse
from pyzabbix import ZabbixAPI

def authenticate(url, username, password):
    values = {'jsonrpc': '2.0',
              'method': 'user.login',
              'params': {
                  'user': username,
                  'password': password
              },
              'id': '0'
              }

    data = json.dumps(values)
    req = urllib2.Request(url, data, {'Content-Type': 'application/json-rpc'})
    response = urllib2.urlopen(req, data)
    output = json.loads(response.read())

    try:
        message = output['result']
    except:
        message = output['error']['data']
        print message
        quit()

    return output['result']

def getGraph(hostname, url, auth, graphtype, dynamic, columns):
    if (graphtype == 0):
        selecttype = ['graphid']
        select = 'selectGraphs'
    if (graphtype == 1):
        selecttype = ['itemid', 'value_type']
        select = 'selectItems'

    values = {'jsonrpc': '2.0',
              'method': 'host.get',
              'params': {
                  select: selecttype,
                  'output': ['hostid', 'host'],
                  'searchByAny': 1,
                  'filter': {
                      'host': hostname
                  }
              },
              'auth': auth,
              'id': '2'
              }
    
    data = json.dumps(values)
    req = urllib2.Request(url, data, {'Content-Type': 'application/json-rpc'})
    response = urllib2.urlopen(req, data)
    host_get = response.read()

    output = json.loads(host_get)
    # print json.dumps(output)

    graphs = []
    if (graphtype == 0):
        for i in output['result'][0]['graphs']:
            graphs.append(i['graphid'])

    if (graphtype == 1):
        for i in output['result'][0]['items']:
            if int(i['value_type']) in (0, 3):
                graphs.append(i['itemid'])

    graph_list = []
    x = 0
    y = 0

    for graph in graphs:
        graph_list.append({
            "resourcetype": graphtype,
            "resourceid": graph,
            "width": "500",
            "height": "100",
            "x": str(x),
            "y": str(y),
            "colspan": "1",
            "rowspan": "1",
            "elements": "0",
            "valign": "0",
            "halign": "0",
            "style": "0",
            "url": "",
            "dynamic": str(dynamic)
        })
        x += 1
        if x == columns:
            x = 0
            y += 1

    return graph_list


def screenCreate(url, auth, screen_name, graphids, columns):
    # print graphids
    if len(graphids) % columns == 0:
        vsize = len(graphids) / columns
    else:
        vsize = (len(graphids) / columns) + 1

    values = {"jsonrpc": "2.0",
              "method": "screen.create",
              "params": [{
                  "name": screen_name,
                  "hsize": columns,
                  "vsize": vsize,
                  "screenitems": []
              }],
              "auth": auth,
              "id": 2
              }

    for i in graphids:
        values['params'][0]['screenitems'].append(i)

    data = json.dumps(values)
    req = urllib2.Request(url, data, {'Content-Type': 'application/json-rpc'})
    response = urllib2.urlopen(req, data)
    host_get = response.read()

    output = json.loads(host_get)

    try:
        message = output['result']
    except:
        message = output['error']['data']

    print json.dumps(message)

def main():
    
    parser = argparse.ArgumentParser(description='Create Zabbix screen from all of a host Items or Graphs.')

    parser.add_argument('-s',dest='serverurl',default='http://localhost/zabbix',
            type=str,
            help='server url e.g. http://10.0.0.0.1/zabbix')

    parser.add_argument('-c', dest='columns', type=int, default=3,
                        help='number of columns in the screen (default: 3)')

    parser.add_argument('-g', dest='groupid',type=str,default=1,
            help='host group id to use default 1')

    parser.add_argument('-d', dest='dynamic', action='store_true',
                        help='enable for dynamic screen items (default: disabled)')

    parser.add_argument('-t', dest='screentype', 
            action='store_true',
                        help='set to 1 if you want item simple graphs created (default: 0, regular graphs)')

    parser.add_argument('-u', dest='username', type=str, help="admin username")
    
    parser.add_argument('-p', dest='password', type=str, help="admin password")

    args = parser.parse_args()
   
    if not args.serverurl:
        print("Requires a server url")
        sys.exit(1)
    if not args.username or not args.password:
        print("Requires username and password")
        sys.exit(1)

    zapi = ZabbixAPI(args.serverurl)
    zapi.login(args.username, args.password)

    zh = zapi.host.get(output='extend',groupids=args.groupid)

    url = args.serverurl + "/api_jsonrpc.php"

    columns = args.columns
    dynamic = (1 if args.dynamic else 0)
    screentype = (1 if args.screentype else 0)
    auth = authenticate(url, args.username, args.password)

    for host in zh:
        graphids = getGraph(host['name'], url, auth, screentype, dynamic, columns)
        print "Total Number of Graphs: " + str(len(graphids))
        screenCreate(url, auth, host['name'], graphids, columns)

if __name__ == '__main__':
    main()
