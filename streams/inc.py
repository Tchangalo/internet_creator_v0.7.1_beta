import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_socketio import SocketIO, emit
import subprocess
import os
import select
import threading
import time

app = Flask(__name__)
app.secret_key = 'my_secret_key'  # Hier einen sicheren Schlüssel verwenden
#socketio = SocketIO(app)
socketio = SocketIO(app, async_mode='eventlet', logger=False, engineio_logger=False, ping_timeout=20, ping_interval=10)

GENERAL_SCRIPT_DIR = "/home/user/streams/ks/"
OTHER_SCRIPT_DIR = "/home/user/streams/"
IMAGE_PATH = "/static/style/mplan.png"

def ensure_config_dir_exists():
    if not os.path.exists(GENERAL_SCRIPT_DIR):
        os.makedirs(GENERAL_SCRIPT_DIR)

def call_script(script_dir, script_name, *args):
    command = f"bash {script_dir}{script_name} {' '.join(map(str, args))}"
    print(f"Executing command: {command}")  # Debug-Ausgabe

    env = os.environ.copy()
    env["ANSIBLE_FORCE_COLOR"] = "true"

    # Liste von Keywords, die in den zu ignorierenden Warnungen vorkommen
    ignore_keywords = ["interpreter", "ansible", "python", "idempotency", "configuration", "device"]

    try:
        with subprocess.Popen(command, shell=True, executable="/bin/bash",
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, env=env, bufsize=1) as process:
            while True:
                reads = [process.stdout.fileno(), process.stderr.fileno()]
                ret = select.select(reads, [], [])

                # Echtzeitausgabe von stdout (Download-Status)
                if process.stdout.fileno() in ret[0]:
                    line = process.stdout.readline()
                    if line:
                        print(line, end='', flush=True)  # Echtzeitausgabe für stdout

                # Filtern und Ausblenden von Warnungen basierend auf Keywords
                if process.stderr.fileno() in ret[0]:
                    line = process.stderr.readline()
                    if line:
                        # Ignorieren, wenn eine der Ignore-Keywords in der Zeile vorkommt
                        if not any(keyword in line.lower() for keyword in ignore_keywords):
                            print(line, end='', flush=True)  # Andere Fehler sofort anzeigen

                # Beenden, wenn der Prozess abgeschlossen ist
                if process.poll() is not None:
                    break

            # Warten, bis der Prozess vollständig abgeschlossen ist
            process.wait()

            if process.returncode == 0:
                flash(f"Script {script_name} executed successfully!", "success")
            else:
                flash(f"Script {script_name} failed with exit code {process.returncode}.", "error")

    except FileNotFoundError:
        flash(f"Script {script_name} not found or invalid command!", "error")
        print(f"Script {script_name} not found or invalid command!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/toggle_mode', methods=['POST'])
def toggle_mode():
    mode = request.json.get("mode")
    script_name = "togglemode.sh"
    call_script(OTHER_SCRIPT_DIR, script_name)
    return '', 204

@app.route('/creator', methods=['GET', 'POST'])
def creator():
    if request.method == 'POST':
        # Unterscheiden, welcher Button gesendet wurde und das entsprechende Skript aufrufen
        if 'provider' in request.form:
            args = [request.form.get(label, "") for label in ["Node", "Provider", "Routers", "Limit", "Start Delay"]]
            args.insert(2, "1")
            refresh_vyos_upgrade_version = "1" if request.form.get("refresh_vyos_upgrade") else "0"
            args.append(refresh_vyos_upgrade_version)
            script_name = "provider_serial.sh" if request.form.get("Serial Mode") else "provider.sh"
            call_script(OTHER_SCRIPT_DIR, script_name, *args)
        elif 'provider_turbo' in request.form:
            args = [request.form.get(label, "") for label in ["Node", "Provider", "Routers", "Limit"]]
            args.insert(2, "1")
            refresh_vyos_upgrade_version = "1" if request.form.get("refresh_vyos_upgrade") else "0"
            args.append(refresh_vyos_upgrade_version)
            call_script(OTHER_SCRIPT_DIR, "provider_turbo.sh", *args)
        elif 'single_router' in request.form:
            args = [request.form.get(label, "") for label in ["Node", "Provider", "Router"]]
            args.insert(2, "1")          
            refresh_vyos_upgrade_version = "1" if request.form.get("refresh_vyos_upgrade") else "0"
            args.append(refresh_vyos_upgrade_version)
            call_script(OTHER_SCRIPT_DIR, "single_router.sh", *args)

        return redirect(url_for('creator'))

    return render_template('creator.html')

@app.route('/general', methods=['GET', 'POST'])
def general():
    if request.method == 'POST':
        # Unterscheiden, welcher Button gesendet wurde und das entsprechende Skript aufrufen
        if 'restart_isp1' in request.form:
            isp1_routers = request.form.get("restart_isp1_routers", "")
            isp1_delay = request.form.get("restart_isp1_delay", "")
            call_script(GENERAL_SCRIPT_DIR, "restart_isp1.sh", isp1_routers, isp1_delay)
        elif 'restart_isp2' in request.form:
            isp2_routers = request.form.get("restart_isp2_routers", "")
            isp2_delay = request.form.get("restart_isp2_delay", "")
            call_script(GENERAL_SCRIPT_DIR, "restart_isp2.sh", isp2_routers, isp2_delay)
        elif 'restart_isp3' in request.form:
            isp3_routers = request.form.get("restart_isp3_routers", "")
            isp3_delay = request.form.get("restart_isp3_delay", "")
            call_script(GENERAL_SCRIPT_DIR, "restart_isp3.sh", isp3_routers, isp3_delay)

        elif 'start_isp1' in request.form:
            start_isp1_routers = request.form.get("start_isp1_routers", "")
            start_isp1_delay = request.form.get("start_isp1_delay", "")
            call_script(GENERAL_SCRIPT_DIR, "start_isp1.sh", start_isp1_routers, start_isp1_delay)
        elif 'start_isp2' in request.form:
            start_isp2_routers = request.form.get("start_isp2_routers", "")
            start_isp2_delay = request.form.get("start_isp2_delay", "")
            call_script(GENERAL_SCRIPT_DIR, "start_isp2.sh", start_isp2_routers, start_isp2_delay)
        elif 'start_isp3' in request.form:
            start_isp3_routers = request.form.get("start_isp3_routers", "")
            start_isp3_delay = request.form.get("start_isp3_delay", "")
            call_script(GENERAL_SCRIPT_DIR, "start_isp3.sh", start_isp3_routers, start_isp3_delay)

        elif 'shutdown_isp1' in request.form:
            shutdown_isp1 = request.form.get("shutdown_isp1", "")
            call_script(GENERAL_SCRIPT_DIR, "shutdown_isp1.sh", shutdown_isp1)
        elif 'shutdown_isp2' in request.form:
            shutdown_isp2 = request.form.get("shutdown_isp2", "")
            call_script(GENERAL_SCRIPT_DIR, "shutdown_isp2.sh", shutdown_isp2)
        elif 'shutdown_isp3' in request.form:
            shutdown_isp3 = request.form.get("shutdown_isp3", "")
            call_script(GENERAL_SCRIPT_DIR, "shutdown_isp3.sh", shutdown_isp3)

        elif 'destroy_isp1' in request.form:
            destroy_isp1 = request.form.get("destroy_isp1", "")
            call_script(GENERAL_SCRIPT_DIR, "destroy_isp1.sh", destroy_isp1)
        elif 'destroy_isp2' in request.form:
            destroy_isp2 = request.form.get("destroy_isp2", "")
            call_script(GENERAL_SCRIPT_DIR, "destroy_isp2.sh", destroy_isp2)
        elif 'destroy_isp3' in request.form:
            destroy_isp3 = request.form.get("destroy_isp3", "")
            call_script(GENERAL_SCRIPT_DIR, "destroy_isp3.sh", destroy_isp3)

        return redirect(url_for('general'))

    return render_template('general.html')

@app.route('/ping-test', methods=['GET', 'POST'])
def ping_test():
    if request.method == 'POST':
        provider = request.form.get("Provider", "")
        router = request.form.get("Routers", "")
        
        # Startet einen neuen Thread, um das Skript asynchron auszuführen
        threading.Thread(target=run_ping_script, args=(provider, router)).start()
        return redirect(url_for('ping_test'))
    
    return render_template('ping_test.html')

def run_ping_script(provider, router):
    # Kurze Verzögerung, damit der WebSocket-Client Zeit hat, sich zu verbinden
    time.sleep(0.3)  # Wartezeit in Sekunden
    # Startet das Skript und leitet die Ausgabe an SocketIO weiter
    with subprocess.Popen(['./ping.sh', provider, router], stdout=subprocess.PIPE, text=True) as process:
        for line in process.stdout:
            # Sende jede Zeile der Ausgabe an den Client
            socketio.emit('ping_output', {'data': line})

@app.route('/sh-conf', methods=['GET', 'POST'])
def sh_conf():
    if request.method == 'POST':
        provider = request.form.get("Provider", "")
        router = request.form.get("Router", "")
        threading.Thread(target=run_sh_conf_script, args=(provider, router)).start()
        return redirect(url_for('sh_conf'))
    
    return render_template('sh_conf.html')

def run_sh_conf_script(provider, router):
    time.sleep(0.3)
    with subprocess.Popen(['./sh_conf.sh', provider, router], stdout=subprocess.PIPE, text=True) as process:
        for line in process.stdout:
            socketio.emit('sh_conf_output', {'data': line})

