# Domain Checker

A Python script to verify if domains are correctly pointing to the server for **cPanel** and **DirectAdmin**. It detects **CDN usage**, checks **SSL validation**, and provides a comprehensive status report of all connected domains. This tool is designed to help server administrators ensure proper domain-to-server connections.

---

## Features

- Detects control panel type (cPanel or DirectAdmin).
- Verifies if domains are pointing to the correct server IP.
- Checks domain reachability and resolves DNS issues.
- Detects CDN usage and validates SSL certificates.
- Provides detailed logs and status reports for all domains.

---

## Installation

To use the `domain_checker` script, ensure you have Python installed on your system. Then, install the required dependencies:

```bash
pip install tqdm beautifulsoup4 requests
```

---

## Usage

Run the script using Python:

```bash
python domain_checker.py
```

### Output Files
The script generates the following result files in the transfer directory:
- **`mismatched_domains.txt`**: Domains with IP mismatches.
- **`healthy_domains.txt`**: Domains functioning correctly.
- **`direct_domains.txt`**: Domains directly hosted on the server.
- **`no_ping_domains.txt`**: Domains that could not be resolved or pinged.
- **`combined_domains.txt`**: A consolidated list of healthy and direct domains.
- **`domain_statuses.log`**: Logs HTTP status codes for each domain.
- **`domain_status.log`**: Detailed execution logs for debugging.

---

## Configuration

### Constants
You can modify the following constants in the script to suit your environment:
- **`CPANEL_PATH`**: Path to the cPanel installation directory.
- **`DIRECTADMIN_PATH`**: Path to the DirectAdmin installation directory.
- **`TRANSFER_DIR`**: Directory where result files will be saved.
- **`USERDATA_DOMAINS_FILE`**: Path to the cPanel user data domains file.

---

## Example

1. Run the script:
   ```bash
   python domain_checker.py
   ```

2. Check the generated result files in the transfer directory:
   - Open `mismatched_domains.txt` to see domains with IP mismatches.
   - Open `healthy_domains.txt` to verify domains that are working correctly.

3. Review the logs for detailed information:
   - `domain_status.log` for execution details.
   - `domain_statuses.log` for HTTP status codes.

---

## Dependencies

The script requires the following Python libraries:
- `tqdm`: For progress bars.
- `beautifulsoup4`: For HTML parsing.
- `requests`: For making HTTP requests.

Install them using:
```bash
pip install tqdm beautifulsoup4 requests
```

---

## Notes

- Ensure the script has the necessary permissions to access control panel files and directories.
- For DirectAdmin, the script scans `/home` for user directories and domain configurations.
- For cPanel, the script uses the `whmapi1` command to fetch domain information.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.