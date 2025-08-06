from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import platform
import ipaddress
import time
import socket
import threading
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

app = Flask(__name__)

# Global variables for scan state
scan_state = {
    'scanning': False,
    'progress': 0,
    'total_hosts': 0,
    'completed': 0,
    'active_hosts': [],
    'scan_id': None,
    'status_message': 'Ready to scan'
}



def _is_mac_address(text):
    """Check if text looks like a MAC address"""
    import re
    if not text:
        return False
    # MAC address pattern: xx:xx:xx:xx:xx:xx or xx-xx-xx-xx-xx-xx
    mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    return bool(re.match(mac_pattern, text))

def ping_and_resolve(ip):
    """Ping an IP and get its hostname"""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = f"ping {param} 1 {ip}"
    result = subprocess.run(command, shell=True, stdout=subprocess.DEVNULL)
    
    host_info = {
        'ip': ip,
        'active': result.returncode == 0,
        'hostname': 'Unknown',
        'timestamp': datetime.now().isoformat()
    }
    
    # If ping successful, try to get hostname and scan ports
    if host_info['active']:
        try:
            # Set timeout for hostname resolution
            socket.setdefaulttimeout(3.0)  # Increased timeout
            hostname = socket.gethostbyaddr(ip)[0]
            
            # Filter out MAC addresses and unhelpful names
            if hostname and hostname != ip and not _is_mac_address(hostname) and not hostname.startswith('_'):
                host_info['hostname'] = hostname
            else:
                raise socket.gaierror("Not a valid hostname")
                
        except (socket.herror, socket.gaierror, socket.timeout):
            # If hostname resolution fails, try alternative methods
            try:
                hostname = socket.getfqdn(ip)
                if hostname and hostname != ip and not _is_mac_address(hostname) and '.' in hostname:
                    host_info['hostname'] = hostname
                else:
                    # Try reverse DNS with different approach
                    try:
                        result = subprocess.run(['nslookup', ip], capture_output=True, text=True, timeout=2)
                        if result.returncode == 0 and 'name =' in result.stdout:
                            name_line = [line for line in result.stdout.split('\n') if 'name =' in line]
                            if name_line:
                                extracted_name = name_line[0].split('name =')[1].strip().rstrip('.')
                                if extracted_name and not _is_mac_address(extracted_name):
                                    host_info['hostname'] = extracted_name
                    except:
                        pass
            except:
                pass
        finally:
            socket.setdefaulttimeout(None)  # Reset timeout
    
    return host_info

def get_ips(subnet):
    """Get list of IP addresses from subnet"""
    try:
        network = ipaddress.ip_network(subnet, strict=False)
        return [str(ip) for ip in network.hosts()]
    except ValueError as e:
        return []

def scan_network_thread(subnet, max_workers):
    """Scan network in a separate thread"""
    global scan_state
    
    ips = get_ips(subnet)
    if not ips:
        scan_state['scanning'] = False
        scan_state['status_message'] = 'Invalid subnet format'
        return
    
    scan_state['total_hosts'] = len(ips)
    scan_state['completed'] = 0
    scan_state['active_hosts'] = []
    
    scan_state['status_message'] = f'Scanning {len(ips)} hosts...'
    
    # Multi-threaded ping scanning with hostname resolution
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        if not scan_state['scanning']:
            return
            
        future_to_ip = {executor.submit(ping_and_resolve, ip): ip for ip in ips}
        
        for future in as_completed(future_to_ip):
            if not scan_state['scanning']:
                executor.shutdown(wait=False)
                break
                
            ip = future_to_ip[future]
            try:
                host_info = future.result()
                if host_info['active']:
                    scan_state['active_hosts'].append(host_info)
                
            except Exception as e:
                print(f"Error scanning {ip}: {e}")
            
            scan_state['completed'] += 1
            scan_state['progress'] = (scan_state['completed'] / scan_state['total_hosts']) * 100
    
    scan_state['scanning'] = False
    scan_state['status_message'] = f'Scan completed. Found {len(scan_state["active_hosts"])} active hosts.'

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def start_scan():
    """Start network scan"""
    global scan_state
    
    if scan_state['scanning']:
        return jsonify({'error': 'Scan already in progress'}), 400
    
    data = request.get_json()
    subnet = data.get('subnet', '').strip()
    max_workers = int(data.get('threads', 50))
    
    if not subnet:
        return jsonify({'error': 'Please enter a subnet'}), 400
    
    # Validate subnet
    try:
        ipaddress.ip_network(subnet, strict=False)
    except ValueError:
        return jsonify({'error': 'Invalid subnet format'}), 400
    
    # Reset scan state
    scan_state['scanning'] = True
    scan_state['progress'] = 0
    scan_state['completed'] = 0
    scan_state['active_hosts'] = []
    scan_state['scan_id'] = str(int(time.time()))
    
    # Start scan in background thread
    scan_thread = threading.Thread(target=scan_network_thread, args=(subnet, max_workers))
    scan_thread.daemon = True
    scan_thread.start()
    
    return jsonify({'message': 'Scan started', 'scan_id': scan_state['scan_id']})

@app.route('/stop', methods=['POST'])
def stop_scan():
    """Stop current scan"""
    global scan_state
    scan_state['scanning'] = False
    scan_state['status_message'] = 'Scan stopped by user'
    return jsonify({'message': 'Scan stopped'})

@app.route('/status')
def get_status():
    """Get current scan status"""
    return jsonify({
        'scanning': scan_state['scanning'],
        'progress': scan_state['progress'],
        'completed': scan_state['completed'],
        'total_hosts': scan_state['total_hosts'],
        'active_hosts_count': len(scan_state['active_hosts']),
        'status_message': scan_state['status_message']
    })

@app.route('/results')
def get_results():
    """Get scan results"""
    return jsonify({
        'active_hosts': scan_state['active_hosts'],
        'total_found': len(scan_state['active_hosts'])
    })

@app.route('/export')
def export_results():
    """Export results to file"""
    if not scan_state['active_hosts']:
        return jsonify({'error': 'No results to export'}), 400
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"network_scan_results_{timestamp}.txt"
    
    with open(filename, "w") as f:
        f.write(f"Network Scan Results with Hostnames and Ports - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total active hosts: {len(scan_state['active_hosts'])}\n\n")
        f.write("IP Address" + " " * 8 + "Hostname" + " " * 20 + "Open Ports\n")
        f.write("-" * 80 + "\n")
        
        for host in scan_state['active_hosts']:
            ip = host['ip']
            hostname = host['hostname'] if host['hostname'] != 'Unknown' else 'No hostname'
            ports_info = ""
            if host.get('open_ports'):
                ports_list = [f"{p['port']} ({p['service']})" for p in host['open_ports']]
                ports_info = ", ".join(ports_list)
            else:
                ports_info = "No open ports detected"
            
            f.write(f"{ip:<15} {hostname:<25} {ports_info}\n")
            
        f.write("\n" + "=" * 80 + "\n")
    
    return send_file(filename, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("Starting PingScanner Web Interface...")
    print("Open your browser and go to: http://localhost:5001")
    print("Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
