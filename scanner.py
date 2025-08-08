
from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import platform
import ipaddress
import time
from datetime import datetime

app = Flask(__name__)

# Global scan state
scan_state = {
    'scanning': False,
    'progress': 0,
    'total_hosts': 0,
    'completed': 0,
    'active_hosts': [],
    'status_message': 'Ready to scan'
}

# if network is private (safe to scan)
def is_private_network(subnet):
    try:
        network = ipaddress.ip_network(subnet, strict=False)
        private_ranges = [
            ipaddress.ip_network('192.168.0.0/16'),
            ipaddress.ip_network('10.0.0.0/8'),
            ipaddress.ip_network('172.16.0.0/12'),
        ]
        return any(network.subnet_of(range_) for range_ in private_ranges)
    except:
        return False

# Read ARP table to find active devices
def get_arp_table():
    arp_devices = {}
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return arp_devices

        is_windows = platform.system().lower() == "windows"
        
        for line in result.stdout.splitlines():
            line = line.strip()
            if is_windows:
                parts = line.split()
                if len(parts) >= 2 and '.' in parts[0]:
                    ip, mac = parts[0], parts[1]
                    if '-' in mac or ':' in mac:
                        arp_devices[ip] = mac.replace('-', ':').lower()
            else:
                if '(incomplete)' in line or 'at' not in line:
                    continue
                try:
                    ip = line.split('(')[1].split(')')[0]
                    mac = line.split(' at ')[1].split()[0]
                    arp_devices[ip] = mac.lower()
                except IndexError:
                    continue
    except Exception as e:
        print(f"ARP table error: {e}")
    
    return arp_devices

# Get hostname for IP address
def get_hostname(ip):
    try:
        socket.setdefaulttimeout(2.0)
        return socket.gethostbyaddr(ip)[0]
    except:
        return 'Unknown'
    finally:
        socket.setdefaulttimeout(None)

# Scan individual IP address
def scan_ip(ip, arp_table=None):
    host_info = {
        'ip': ip,
        'active': False,
        'hostname': 'Unknown',
        'detection_method': 'None'
    }
    
    # Method 1: ICMP ping
    param = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        result = subprocess.run(f"ping {param} 1 {ip}", shell=True, 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        if result.returncode == 0:
            host_info['active'] = True
            host_info['detection_method'] = 'ICMP Ping'
    except:
        pass
    
    # Method 2: Check ARP table
    if not host_info['active'] and arp_table and ip in arp_table:
        mac = arp_table[ip]
        if mac and len(mac.replace(':', '')) == 12:
            host_info['active'] = True
            host_info['detection_method'] = 'ARP Table'
    
    # Get hostname if active
    if host_info['active']:
        hostname = get_hostname(ip)
        if hostname != 'Unknown' and hostname != ip:
            host_info['hostname'] = hostname
    
    return host_info

# Get IP addresses from subnet
def get_ips(subnet):
    if not is_private_network(subnet):
        return []
    
    try:
        network = ipaddress.ip_network(subnet, strict=False)
        host_list = list(network.hosts())
        # Limit to 254 hosts for performance
        if len(host_list) > 254:
            host_list = host_list[:254]
        return [str(ip) for ip in host_list]
    except:
        return []

# Main scanning function
def scan_network(subnet):
    global scan_state
    
    # Validate private network
    if not is_private_network(subnet):
        scan_state['scanning'] = False
        scan_state['status_message'] = 'Only private networks allowed'
        return
    
    ips = get_ips(subnet)
    if not ips:
        scan_state['scanning'] = False
        scan_state['status_message'] = 'Invalid subnet'
        return
    
    scan_state['total_hosts'] = len(ips)
    scan_state['completed'] = 0
    scan_state['active_hosts'] = []
    scan_state['status_message'] = f'Scanning {len(ips)} hosts...'
    
    # Get ARP table for passive detection
    arp_table = get_arp_table()
    
    # Scan with limited threads
    with ThreadPoolExecutor(max_workers=50) as executor:
        if not scan_state['scanning']:
            return
            
        future_to_ip = {executor.submit(scan_ip, ip, arp_table): ip for ip in ips}
        
        for future in as_completed(future_to_ip):
            if not scan_state['scanning']:
                break
                
            try:
                host_info = future.result()
                if host_info['active']:
                    scan_state['active_hosts'].append(host_info)
                    print(f"Found: {host_info['ip']} ({host_info['hostname']}) - {host_info['detection_method']}")
                
                scan_state['completed'] += 1
                scan_state['progress'] = (scan_state['completed'] / scan_state['total_hosts']) * 100
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"Scan error: {e}")
    
    scan_state['scanning'] = False
    scan_state['status_message'] = f'Found {len(scan_state["active_hosts"])} devices'

# Web routes
@app.route('/')
def index():
    return render_template('scanner.html')

@app.route('/scan', methods=['POST'])
def start_scan():
    global scan_state
    
    if scan_state['scanning']:
        return jsonify({'error': 'Scan in progress'}), 400
    
    data = request.get_json()
    subnet = data.get('subnet', '').strip()
    
    if not subnet:
        return jsonify({'error': 'Enter a subnet'}), 400
    
    if not is_private_network(subnet):
        return jsonify({'error': 'Only private networks allowed'}), 400
    
    # Start scanning
    scan_state['scanning'] = True
    scan_state['progress'] = 0
    scan_state['active_hosts'] = []
    
    scan_thread = threading.Thread(target=scan_network, args=(subnet,))
    scan_thread.daemon = True
    scan_thread.start()
    
    return jsonify({'message': 'Scan started'})

@app.route('/status')
def get_status():
    return jsonify({
        'scanning': scan_state['scanning'],
        'progress': scan_state['progress'],
        'completed': scan_state['completed'],
        'total_hosts': scan_state['total_hosts'],
        'status_message': scan_state['status_message']
    })

@app.route('/results')
def get_results():
    return jsonify({
        'active_hosts': scan_state['active_hosts'],
        'total_active': len(scan_state['active_hosts'])
    })

@app.route('/export')
def export_results():
    if not scan_state['active_hosts']:
        return jsonify({'error': 'No results to export'}), 400
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"network_scan_{timestamp}.txt"
    
    with open(filename, "w") as f:
        f.write(f"Network Scan Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n")
        f.write(f"Total devices: {len(scan_state['active_hosts'])}\n\n")
        f.write("IP Address       Hostname           Method\n")
        f.write("-" * 50 + "\n")
        
        for host in scan_state['active_hosts']:
            ip = host['ip']
            hostname = host.get('hostname', 'Unknown')
            method = host['detection_method']
            f.write(f"{ip:<15} {hostname:<18} {method}\n")
    
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    print("Network Scanner - http://localhost:5003")
    app.run(debug=True, host='0.0.0.0', port=5003)
