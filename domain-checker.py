#!/usr/bin/env python3
"""
Domain Status Checker with Auto Package Installation
"""

import subprocess
import sys
import importlib.util

def install_required_packages():
    """Auto-install required packages with uv support"""
    
    required_packages = {
        'beautifulsoup4': 'bs4',
        'tqdm': 'tqdm', 
        'aiohttp': 'aiohttp',
        'jinja2': 'jinja2',
        'urllib3': 'urllib3'
    }
    
    missing_packages = []
    
    print("🔍 Checking required packages...")
    for pip_name, import_name in required_packages.items():
        if importlib.util.find_spec(import_name) is None:
            missing_packages.append(pip_name)
            print(f"❌ {pip_name} is not installed")
        else:
            print(f"✅ {pip_name} is already installed")
    
    if missing_packages:
        print(f"\n🔄 Installing {len(missing_packages)} missing packages...")
        
        # Detect package manager type
        package_manager = detect_package_manager()
        print(f"📦 Using package manager: {package_manager}")
        
        for package in missing_packages:
            try:
                print(f"Installing {package}...")
                
                if package_manager == "uv":
                    # Use uv add first
                    result = subprocess.run(["uv", "add", package], 
                                          capture_output=True, text=True)
                    if result.returncode != 0:
                        # If uv add fails, try uv pip
                        result = subprocess.run(["uv", "pip", "install", package], 
                                              capture_output=True, text=True)
                elif package_manager == "pip":
                    # Use regular pip
                    result = subprocess.run([sys.executable, "-m", "pip", "install", package, "--quiet"], 
                                          capture_output=True, text=True)
                else:
                    # Fallback to pip
                    result = subprocess.run([sys.executable, "-m", "pip", "install", package, "--quiet"], 
                                          capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ {package} installed successfully")
                else:
                    print(f"❌ Failed to install {package}: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"❌ Failed to install {package}: {e}")
                return False
                
        print("🎉 All packages installed successfully!")
    else:
        print("🎉 All required packages are already installed!")
    
    return True

def detect_package_manager():
    """Detect available package manager"""
    try:
        # Check for uv
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            return "uv"
    except FileNotFoundError:
        pass
    
    try:
        # Check for pip
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            return "pip"
    except FileNotFoundError:
        pass
    
    return "unknown"

# Auto-install packages before importing
print("=" * 50)
print("Domain Status Checker - Auto Installation")
print("=" * 50)

if not install_required_packages():
    print("❌ Failed to install required packages. Exiting...")
    sys.exit(1)

print("\n🔄 Loading modules...")

# Now import the modules
import os
import socket
import json
import logging
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from typing import List, Tuple, Optional
from jinja2 import Environment, FileSystemLoader
import urllib3

print("✅ All modules loaded successfully!")
print("=" * 50)

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
CPANEL_PATH = "/usr/local/cpanel"
DIRECTADMIN_PATH = "/usr/local/directadmin"
TRANSFER_DIR = "/home/transfer"
USERDATA_DOMAINS_FILE = "/etc/userdatadomains"

# Logging setup
logging.basicConfig(
    filename='domain_status.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

error_logger = logging.getLogger('error_logger')
error_handler = logging.FileHandler('domain_errors.log')
error_handler.setLevel(logging.ERROR)
error_format = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
error_handler.setFormatter(error_format)
error_logger.addHandler(error_handler)
error_logger.propagate = False

status_logger = logging.getLogger('status_logger')
status_handler = logging.FileHandler('domain_statuses.log')
status_handler.setLevel(logging.INFO)
status_format = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
status_handler.setFormatter(status_format)
status_logger.addHandler(status_handler)
status_logger.propagate = False

# Jinja2 setup for HTML report
env = Environment(loader=FileSystemLoader('.'))
template = env.from_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Domain Status Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .healthy { background-color: #d4edda; }
        .mismatched { background-color: #f8d7da; }
        .direct { background-color: #d1ecf1; }
        .no-ping { background-color: #fff3cd; }
    </style>
</head>
<body>
    <h1>Domain Status Report</h1>
    <table>
        <tr>
            <th>Domain</th>
            <th>Status</th>
            <th>IP</th>
            <th>HTTP Status</th>
        </tr>
        {% for domain, status, ip, http_status in domains %}
        <tr class="{{ status|lower|replace(' ', '-') }}">
            <td>{{ domain }}</td>
            <td>{{ status }}</td>
            <td>{{ ip or 'N/A' }}</td>
            <td>{{ http_status or 'N/A' }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
""")

class DomainManager:
    def __init__(self):
        self.transfer_dir = self.create_transfer_directory()
        self.server_ip = self.get_server_ip()
        self.panel_type = self.check_control_panel()
        self.domains = []
        self.domain_paths = self.get_domains()

    def check_control_panel(self) -> str:
        if os.path.exists(CPANEL_PATH):
            return "cpanel"
        elif os.path.exists(DIRECTADMIN_PATH):
            return "directadmin"
        else:
            return "unknown"

    def create_transfer_directory(self) -> str:
        if not os.path.exists(TRANSFER_DIR):
            try:
                os.makedirs(TRANSFER_DIR)
                logging.info(f"Directory {TRANSFER_DIR} created successfully.")
            except Exception as e:
                error_logger.error(f"Error creating directory {TRANSFER_DIR}: {e}")
        else:
            logging.info(f"Directory {TRANSFER_DIR} already exists.")
        return TRANSFER_DIR

    def get_server_ip(self) -> str:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

    def get_domains(self) -> List[Tuple[str, Optional[str]]]:
        if self.panel_type == "cpanel":
            return self.get_cpanel_domains()
        elif self.panel_type == "directadmin":
            return self.get_directadmin_domains()
        else:
            error_logger.error("Unknown control panel.")
            return []

    def get_cpanel_domains(self) -> List[Tuple[str, Optional[str]]]:
        try:
            command = ["whmapi1", "--output=jsonpretty", "get_domain_info"]
            result = subprocess.run(command, stdout=subprocess.PIPE, universal_newlines=True, check=True)
            output_json = json.loads(result.stdout)
            self.domains = [entry["domain"] for entry in output_json["data"]["domains"] if "domain" in entry]
            return [(domain, self.get_cpanel_domain_path(domain)) for domain in self.domains]
        except subprocess.CalledProcessError as e:
            error_logger.error(f"Error running WHM API command: {e}")
            return []
        except Exception as e:
            error_logger.error(f"Error extracting domains from cPanel: {e}")
            return []

    def get_cpanel_domain_path(self, domain: str) -> Optional[str]:
        try:
            with open(USERDATA_DOMAINS_FILE, "r") as file:
                lines = file.readlines()
            for line in lines:
                if line.startswith(domain):
                    parts = line.split("==")
                    if len(parts) > 4:
                        return parts[4].strip()
            return None
        except FileNotFoundError:
            error_logger.error(f"{USERDATA_DOMAINS_FILE} file not found.")
            return None
        except Exception as e:
            error_logger.error(f"Error finding path for {domain} in cPanel: {e}")
            return None

    def get_directadmin_domains(self) -> List[Tuple[str, str]]:
        domain_paths = []
        try:
            for user_dir in os.listdir("/home"):
                domain_root = f"/home/{user_dir}/domains"
                if os.path.exists(domain_root):
                    for domain in os.listdir(domain_root):
                        if domain not in ["sharedip", "suspended", "default"]:
                            domain_paths.append((domain, os.path.join(domain_root, domain, "public_html")))
                            self.domains.append(domain)
            return domain_paths
        except Exception as e:
            error_logger.error(f"Error extracting domains and paths from DirectAdmin: {e}")
            return []

    def get_domain_path(self, domain: str) -> Optional[str]:
        for d, path in self.domain_paths:
            if d == domain:
                return path
        return None

    def get_domain_ip(self, domain: str) -> Optional[str]:
        try:
            return socket.gethostbyname(domain)
        except socket.gaierror:
            error_logger.error(f"Error resolving domain {domain}")
            return None

    async def check_status(self, domain: str, session: aiohttp.ClientSession) -> Optional[str]:
        try:
            url = f"http://{domain}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with session.get(url, headers=headers, timeout=15, ssl=False) as response:
                if response.status == 200:
                    text = await response.text()
                    soup = BeautifulSoup(text, 'html.parser')
                    for link in soup.find_all('link', href=True):
                        if 'autoindex.css' in link['href']:
                            return "index of"
                    return str(response.status)
                else:
                    return str(response.status)
        except Exception as e:
            error_logger.error(f"Error checking status for {domain}: {e}")
            return None

    def save_domains_to_file(self, domains: List[str], file_path: str):
        try:
            with open(file_path, "w") as file:
                file.writelines(f"{domain}\n" for domain in domains)
            logging.info(f"Domains successfully saved to {file_path}.")
        except Exception as e:
            error_logger.error(f"Error saving domains to file {file_path}: {e}")

class DomainStatusChecker:
    def __init__(self, domain_manager: DomainManager):
        self.domain_manager = domain_manager
        self.mismatched_domains = []
        self.healthy_domains = []
        self.direct_domains = []
        self.no_ping_domains = []
        self.domain_statuses = []

    def check_domains(self):
        max_workers = max(2, multiprocessing.cpu_count())  # Dynamic thread count
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.check_single_domain, domain): domain
                for domain in self.domain_manager.domains
            }
            for future in tqdm(futures, desc="Checking domains"):
                domain = futures[future]
                try:
                    future.result()
                except Exception as e:
                    error_logger.error(f"Error checking domain {domain}: {e}")

    def check_single_domain(self, domain: str):
        domain_ip = self.domain_manager.get_domain_ip(domain)
        if domain_ip:
            logging.info(f"Domain: {domain}, Domain IP: {domain_ip}")
            if domain_ip == self.domain_manager.server_ip:
                logging.info(f"Domain {domain} is directly on the server.")
                self.direct_domains.append(domain)
                self.domain_statuses.append((domain, "Direct", domain_ip, None))
            else:
                logging.info(f"IP mismatch for {domain}.")
                domain_path = self.domain_manager.get_domain_path(domain)
                if self.save_file_and_upload(domain, domain_path):
                    self.healthy_domains.append(domain)
                    self.domain_statuses.append((domain, "Healthy", domain_ip, None))
                else:
                    self.mismatched_domains.append(domain)
                    self.domain_statuses.append((domain, "Mismatched", domain_ip, None))
        else:
            logging.info(f"Domain {domain} cannot be pinged.")
            self.no_ping_domains.append(domain)
            self.domain_statuses.append((domain, "No Ping", None, None))

    def save_file_and_upload(self, domain: str, domain_path: Optional[str]) -> bool:
        if domain_path and os.path.exists(domain_path):
            file_path = os.path.join(domain_path, "mismatch.txt")
            try:
                with open(file_path, "w") as file:
                    file.write(f"IP mismatch for {domain}\n")
                logging.info(f"File mismatch.txt created in {domain_path} for {domain}.")

                curl_command = ["curl", "-T", file_path, f"http://{domain}/mismatch.txt"]
                result = subprocess.run(curl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    logging.info(f"File mismatch.txt successfully uploaded for {domain}.")
                    os.remove(file_path)
                    return True
                else:
                    error_logger.error(f"Failed to upload mismatch.txt via curl for {domain}.")
                    os.remove(file_path)
                    return False
            except Exception as e:
                error_logger.error(f"Error creating or uploading file for {domain}: {e}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                return False
        else:
            error_logger.error(f"Domain path for {domain} not found or doesn't exist.")
            return False

    async def check_domain_statuses(self):
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.domain_manager.check_status(domain, session)
                for domain in self.direct_domains + self.healthy_domains
            ]
            results = []
            for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Checking domain statuses"):
                result = await future
                results.append(result)
            for domain, status in zip(self.direct_domains + self.healthy_domains, results):
                for i, (d, s, ip, _) in enumerate(self.domain_statuses):
                    if d == domain:
                        self.domain_statuses[i] = (d, s, ip, status)
                        status_logger.info(f"Status for {domain}: {status}")

    def save_results(self):
        transfer_dir = self.domain_manager.transfer_dir
        self.domain_manager.save_domains_to_file(self.mismatched_domains, os.path.join(transfer_dir, "mismatched_domains.txt"))
        self.domain_manager.save_domains_to_file(self.healthy_domains, os.path.join(transfer_dir, "healthy_domains.txt"))
        self.domain_manager.save_domains_to_file(self.direct_domains, os.path.join(transfer_dir, "direct_domains.txt"))
        self.domain_manager.save_domains_to_file(self.no_ping_domains, os.path.join(transfer_dir, "no_ping_domains.txt"))

        combined_domains = self.direct_domains + self.healthy_domains
        combined_file_path = os.path.join(transfer_dir, "combined_domains.txt")
        self.domain_manager.save_domains_to_file(combined_domains, combined_file_path)

        # Generate HTML report
        try:
            html_content = template.render(domains=self.domain_statuses)
            report_path = os.path.join(transfer_dir, "domain_report.html")
            with open(report_path, "w") as f:
                f.write(html_content)
            logging.info(f"HTML report saved to {report_path}.")
        except Exception as e:
            error_logger.error(f"Error generating HTML report: {e}")

async def main():
    print("\n🚀 Starting Domain Status Checker...")
    domain_manager = DomainManager()
    if not domain_manager.domain_paths:
        error_logger.error("No domains were found.")
        print("❌ No domains were found.")
        return

    print(f"✅ Found {len(domain_manager.domains)} domains")
    print(f"🖥️  Server IP: {domain_manager.server_ip}")
    print(f"🎛️  Control Panel: {domain_manager.panel_type}")

    status_checker = DomainStatusChecker(domain_manager)
    status_checker.check_domains()
    await status_checker.check_domain_statuses()
    status_checker.save_results()

    print("\n📊 Results Summary:")
    print(f"✅ Direct domains: {len(status_checker.direct_domains)}")
    print(f"🟢 Healthy domains: {len(status_checker.healthy_domains)}")
    print(f"🔴 Mismatched domains: {len(status_checker.mismatched_domains)}")
    print(f"🟡 No ping domains: {len(status_checker.no_ping_domains)}")

    print("\n📁 Files saved in /home/transfer/:")
    print("   - domain_status.log (main log)")
    print("   - domain_errors.log (errors)")
    print("   - domain_statuses.log (status checks)")
    print("   - domain_report.html (HTML report)")
    print("   - mismatched_domains.txt")
    print("   - healthy_domains.txt")
    print("   - direct_domains.txt")
    print("   - no_ping_domains.txt")
    print("   - combined_domains.txt")

if __name__ == "__main__":
    asyncio.run(main())
