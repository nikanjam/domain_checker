import os
import subprocess
import socket
import json
import requests
import urllib3
import logging
from bs4 import BeautifulSoup
from tqdm import tqdm  # package for loading

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Logging setup for saving to domain_status.log
logging.basicConfig(
    filename='domain_status.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Logging setup for saving domain statuses to domain_statuses.log
status_logger = logging.getLogger('status_logger')
status_handler = logging.FileHandler('domain_statuses.log')
status_handler.setLevel(logging.INFO)
status_format = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
status_handler.setFormatter(status_format)
status_logger.addHandler(status_handler)
status_logger.propagate = False

class DomainManager:
    def __init__(self):
        self.transfer_dir = self.create_transfer_directory()
        self.server_ip = self.get_server_ip()
        self.panel_type = self.check_control_panel()
        self.domains = []  # Domains List
        self.domain_paths = self.get_domains()  # Array for domain path in DA or cPanel

    def check_control_panel(self):
        if os.path.exists("/usr/local/cpanel"):
            return "cpanel"
        elif os.path.exists("/usr/local/directadmin"):
            return "directadmin"
        else:
            return "unknown"

    def create_transfer_directory(self):
        transfer_dir = "/home/transfer"
        if not os.path.exists(transfer_dir):
            try:
                os.makedirs(transfer_dir)
                logging.info(f"Directory {transfer_dir} created successfully.")
            except Exception as e:
                logging.error(f"Error creating directory {transfer_dir}: {e}")
        else:
            logging.info(f"Directory {transfer_dir} already exists.")
        return transfer_dir

    def get_server_ip(self):
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

    def get_domains(self):
        if self.panel_type == "cpanel":
            return self.get_cpanel_domains()
        elif self.panel_type == "directadmin":
            return self.get_directadmin_domains()
        else:
            logging.error("Unknown control panel.")
            return []

    def get_cpanel_domains(self):
        try:
            command = ["whmapi1", "--output=jsonpretty", "get_domain_info"]
            result = subprocess.run(command, stdout=subprocess.PIPE, universal_newlines=True)

            output_json = json.loads(result.stdout)
            self.domains = [entry["domain"] for entry in output_json["data"]["domains"] if "domain" in entry]
            return [(domain, self.get_cpanel_domain_path(domain)) for domain in self.domains]
        except Exception as e:
            logging.error(f"Error extracting domains from cPanel: {e}")
            return []

    def get_cpanel_domain_path(self, domain):
        try:
            with open("/etc/userdatadomains", "r") as file:
                for line in file:
                    if line.startswith(domain):
                        parts = line.split("==")
                        if len(parts) > 4:
                            return parts[4].strip()
            return None
        except Exception as e:
            logging.error(f"Error finding path for {domain} in cPanel: {e}")
            return None

    def get_directadmin_domains(self):
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
            logging.error(f"Error extracting domains and paths from DirectAdmin: {e}")
            return []

    def get_domain_path(self, domain):
        for d, path in self.domain_paths:
            if d == domain:
                return path
        return None

    def get_domain_ip(self, domain):
        try:
            return socket.gethostbyname(domain)
        except socket.gaierror:
            logging.error(f"Error resolving domain {domain}")
            return None

    def check_status(self, domain):
        try:
            url = f"http://{domain}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(
                url,
                headers=headers,
                timeout=15,
                allow_redirects=True,
                verify=False
            )

            # Check if status is 200 and look for autoindex.css
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                for link in soup.find_all('link', href=True):
                    if 'autoindex.css' in link['href']:
                        return "index of"  # Change status to "index of" if autoindex.css is found
                return response.status_code
            else:
                return response.status_code
        except requests.exceptions.RequestException as e:
            logging.error(f"Error checking status for {domain}: {e}")
            return None

    def save_domains_to_file(self, domains, file_path):
        try:
            with open(file_path, "w") as file:
                file.writelines(f"{domain}\n" for domain in domains)
            logging.info(f"Domains successfully saved to {file_path}.")
        except Exception as e:
            logging.error(f"Error saving domains to file {file_path}: {e}")

class DomainStatusChecker:
    def __init__(self, domain_manager):
        self.domain_manager = domain_manager
        self.mismatched_domains = []
        self.healthy_domains = []
        self.direct_domains = []
        self.no_ping_domains = []

    def check_domains(self):
        total_domains = len(self.domain_manager.domains)
        for index, domain in enumerate(self.domain_manager.domains, start=1):
            print(f"Checking domain {index}/{total_domains}: {domain}...", end="\r")

            domain_ip = self.domain_manager.get_domain_ip(domain)
            if domain_ip:
                logging.info(f"Domain: {domain}, Domain IP: {domain_ip}")
                if domain_ip == self.domain_manager.server_ip:
                    logging.info(f"Domain {domain} is directly on the server.")
                    self.direct_domains.append(domain)
                else:
                    logging.info(f"IP mismatch for {domain}.")
                    domain_path = self.domain_manager.get_domain_path(domain)
                    if self.save_file_and_upload(domain, domain_path):
                        self.healthy_domains.append(domain)
                    else:
                        self.mismatched_domains.append(domain)
            else:
                logging.info(f"Domain {domain} cannot be pinged.")
                self.no_ping_domains.append(domain)

    def save_file_and_upload(self, domain, domain_path):
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
                    logging.error(f"Failed to upload mismatch.txt via curl for {domain}.")
                    os.remove(file_path)
                    return False
            except Exception as e:
                logging.error(f"Error creating or uploading file for {domain}: {e}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                return False
        else:
            logging.error(f"Domain path for {domain} not found or doesn't exist.")
            return False

    def save_results(self):
        transfer_dir = self.domain_manager.transfer_dir
        self.domain_manager.save_domains_to_file(self.mismatched_domains, os.path.join(transfer_dir, "mismatched_domains.txt"))
        self.domain_manager.save_domains_to_file(self.healthy_domains, os.path.join(transfer_dir, "healthy_domains.txt"))
        self.domain_manager.save_domains_to_file(self.direct_domains, os.path.join(transfer_dir, "direct_domains.txt"))
        self.domain_manager.save_domains_to_file(self.no_ping_domains, os.path.join(transfer_dir, "no_ping_domains.txt"))

        combined_domains = self.direct_domains + self.healthy_domains
        combined_file_path = os.path.join(transfer_dir, "combined_domains.txt")
        self.domain_manager.save_domains_to_file(combined_domains, combined_file_path)

        for domain in tqdm(combined_domains, desc="Checking domain statuses"):
            status_code = self.domain_manager.check_status(domain)
            if status_code:
                status_logger.info(f"Status for {domain}: {status_code}")
            else:
                status_logger.error(f"Failed to get status for {domain}")

        print("\nStatus check completed.")

def main():
    domain_manager = DomainManager()
    if not domain_manager.domain_paths:
        logging.error("No domains were found.")
        return

    status_checker = DomainStatusChecker(domain_manager)
    status_checker.check_domains()
    status_checker.save_results()

    print("\nThe log has been saved in 'domain_status.log' and the domain statuses have been saved in 'domain_statuses.log'.")

if __name__ == "__main__":
    main()
