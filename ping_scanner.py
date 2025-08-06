import subprocess
import platform
import ipaddress
import time
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

# Common ports to scan
COMMON_PORTS = {
    21: 'FTP',
    22: 'SSH',
    23: 'Telnet',
    25: 'SMTP',
    53: 'DNS',
    80: 'HTTP',
    110: 'POP3',
    143: 'IMAP',
    443: 'HTTPS',
    993: 'IMAPS',
    995: 'POP3S',
    3389: 'RDP',
    5432: 'PostgreSQL',
    3306: 'MySQL',
    1433: 'MSSQL',
    27017: 'MongoDB'
}

def scan_port(ip, port, timeout=1):
    """Scan a single port on an IP address"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except socket.error:
        return False

def _is_mac_address(text):
    """Check if text looks like a MAC address"""
    import re
    if not text:
        return False
    # MAC address pattern: xx:xx:xx:xx:xx:xx or xx-xx-xx-xx-xx-xx
    mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    return bool(re.match(mac_pattern, text))

# ping function with hostname resolution and port scanning
def ping_and_resolve(ip, scan_ports=False, ports_to_scan=None):
    """Ping an IP, get its hostname, and optionally scan ports"""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = f"ping {param} 1 {ip}"
    result = subprocess.run(command, shell=True, stdout=subprocess.DEVNULL)
    
    host_info = {
        'ip': ip,
        'active': result.returncode == 0,
        'hostname': 'Unknown',
        'open_ports': []
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
                        import subprocess
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
        
        # Port scanning if requested
        if scan_ports and ports_to_scan:
            for port in ports_to_scan:
                if scan_port(ip, port, timeout=1):
                    service_name = COMMON_PORTS.get(port, f'Port {port}')
                    host_info['open_ports'].append({'port': port, 'service': service_name})
    
    return host_info

# Legacy ping function for backward compatibility
def ping(ip):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = f"ping {param} 1 {ip}"
    result = subprocess.run(command, shell=True, stdout=subprocess.DEVNULL)
    return result.returncode == 0

# Get list of IP addresses from subnet
def get_ips(subnet):
    try:
        network = ipaddress.ip_network(subnet, strict=False)
        return [str(ip) for ip in network.hosts()]
    except ValueError:
        print(f"{Colors.RED}Invalid subnet format. Use 192.168.1.0/24{Colors.END}")
        return []
    

# Scan network with multi-threading for speed and hostname resolution
def scan_network(subnet, max_workers=50, scan_ports=False, ports_to_scan=None):
    print(f"{Colors.CYAN}{Colors.BOLD}Scanning subnet: {subnet}{Colors.END}")
    ips = get_ips(subnet)
    
    if not ips:
        return []
    
    port_msg = f" and scanning ports {ports_to_scan}" if scan_ports and ports_to_scan else ""
    print(f"{Colors.BLUE}Found {len(ips)} hosts to scan using {max_workers} threads{port_msg}{Colors.END}")
    print(f"{Colors.YELLOW}Note: Hostname resolution may take extra time for active hosts{Colors.END}")
    
    active_hosts = []
    completed = 0
    
    # Progress bar function
    def update_progress():
        percent = (completed / len(ips)) * 100
        bar_length = 50
        filled_length = int(bar_length * completed // len(ips))
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        print(f"\r{Colors.CYAN}Progress: |{bar}| {percent:.1f}% ({completed}/{len(ips)}){Colors.END}", end='')
    
    # Multi-threaded ping scanning with hostname resolution and port scanning
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ip = {executor.submit(ping_and_resolve, ip, scan_ports, ports_to_scan): ip for ip in ips}
        
        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                host_info = future.result()
                if host_info['active']:
                    active_hosts.append(host_info)
                    hostname_display = host_info['hostname'] if host_info['hostname'] != 'Unknown' else 'No hostname'
                    ports_display = ""
                    if host_info['open_ports']:
                        ports_list = [f"{p['port']} ({p['service']})" for p in host_info['open_ports']]
                        ports_display = f" - Open ports: {', '.join(ports_list)}"
                    print(f"\n{Colors.GREEN}[+] Active: {host_info['ip']} ({hostname_display}){ports_display}{Colors.END}")
                
            except Exception as e:
                print(f"\n{Colors.RED}Error scanning {ip}: {e}{Colors.END}")
            
            completed += 1
            update_progress()
    
    print()  # New line after progress bar
    return active_hosts

# Export results to file with hostnames and ports
def export_results(active_hosts, filename="results.txt"):
    with open(filename, "w") as f:
        f.write(f"Network Scan Results with Hostnames and Ports - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total active hosts found: {len(active_hosts)}\n\n")
        f.write("IP Address" + " " * 8 + "Hostname" + " " * 20 + "Open Ports\n")
        f.write("-" * 80 + "\n")
        
        for host in active_hosts:
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
    print(f"{Colors.GREEN}Results saved to {filename}{Colors.END}")


# Main function to run program
if __name__ == "__main__":
    print(f"{Colors.BOLD}🚀 Fast Network Scanner with Port Scanning{Colors.END}")
    print(f"{Colors.BOLD}=" * 45 + Colors.END)
    
    subnet_input = input(f"{Colors.CYAN}Enter subnet (e.g. 192.168.1.0/24): {Colors.END}")
    
    # Ask about port scanning
    port_scan_choice = input(f"{Colors.CYAN}Enable port scanning? (y/N): {Colors.END}").lower().strip()
    scan_ports = port_scan_choice in ['y', 'yes']
    
    ports_to_scan = []
    if scan_ports:
        ports_input = input(f"{Colors.CYAN}Enter ports to scan (comma-separated, ranges like 80-85, or 'common'): {Colors.END}").strip()
        
        if ports_input.lower() == 'common':
            ports_to_scan = list(COMMON_PORTS.keys())
            print(f"{Colors.YELLOW}Using common ports: {sorted(ports_to_scan)}{Colors.END}")
        else:
            try:
                for port_str in ports_input.split(','):
                    port_str = port_str.strip()
                    if '-' in port_str:
                        start, end = map(int, port_str.split('-'))
                        ports_to_scan.extend(range(start, end + 1))
                    else:
                        ports_to_scan.append(int(port_str))
                ports_to_scan = sorted(list(set(ports_to_scan)))
                print(f"{Colors.YELLOW}Scanning ports: {ports_to_scan}{Colors.END}")
            except ValueError:
                print(f"{Colors.RED}Invalid port format. Disabling port scanning.{Colors.END}")
                scan_ports = False
                ports_to_scan = []
    
    start_time = time.time()
    hosts = scan_network(subnet_input, scan_ports=scan_ports, ports_to_scan=ports_to_scan)
    scan_time = time.time() - start_time
    
    print(f"\n{Colors.BOLD}Scan Summary:{Colors.END}")
    print(f"{Colors.GREEN}Active hosts found: {len(hosts)}{Colors.END}")
    print(f"{Colors.BLUE}Scan completed in: {scan_time:.2f} seconds{Colors.END}")
    
    if hosts:
        print(f"\n{Colors.BOLD}Active Hosts:{Colors.END}")
        if scan_ports:
            print(f"{Colors.BOLD}{'IP Address':<15} {'Hostname':<25} {'Open Ports':<30}{Colors.END}")
            print(f"{Colors.BOLD}{'-' * 70}{Colors.END}")
        else:
            print(f"{Colors.BOLD}{'IP Address':<15} {'Hostname':<30}{Colors.END}")
            print(f"{Colors.BOLD}{'-' * 50}{Colors.END}")
        
        for host in hosts:
            ip = host['ip']
            hostname = host['hostname'] if host['hostname'] != 'Unknown' else 'No hostname'
            
            if scan_ports:
                ports_display = "No open ports"
                if host.get('open_ports'):
                    ports_list = [f"{p['port']} ({p['service']})" for p in host['open_ports']]
                    ports_display = ", ".join(ports_list)
                print(f"{Colors.GREEN}{ip:<15} {hostname:<25} {ports_display}{Colors.END}")
            else:
                print(f"{Colors.GREEN}{ip:<15} {hostname:<30}{Colors.END}")
            
        export_results(hosts)
    else:
        print(f"{Colors.YELLOW}No active hosts found.{Colors.END}")