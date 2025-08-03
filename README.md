# Domain Status Checker
A comprehensive Python script to verify if domains are correctly pointing to the server for **cPanel** and **DirectAdmin**. It automatically detects **IP mismatches**, checks **domain reachability**, validates **HTTP status codes**, and provides detailed status reports with **HTML visualization**. This tool is designed to help server administrators ensure proper domain-to-server connections and troubleshoot DNS issues.

---

## Features

- **Auto-Installation**: Automatically installs required packages (supports both `uv` and `pip`)
- **Control Panel Detection**: Automatically detects cPanel or DirectAdmin installations
- **IP Verification**: Verifies if domains are pointing to the correct server IP
- **Domain Reachability**: Checks domain accessibility and resolves DNS issues  
- **HTTP Status Monitoring**: Validates HTTP response codes for all domains
- **Async Processing**: Fast concurrent domain checking using asyncio
- **Comprehensive Logging**: Detailed logs with separate error and status tracking
- **HTML Reports**: Beautiful HTML report with color-coded domain statuses
- **File Upload Testing**: Tests domain functionality by uploading test files
- **Progress Tracking**: Real-time progress bars for all operations

---

## Installation

The script automatically installs required dependencies on first run. No manual installation needed!

### Method 1: Using uv (Recommended)
```bash
uv init
uv run domain_checker.py
```

### Method 2: Using pip
```bash
python3 domain_checker.py
```

### Manual Installation (Optional)
If you prefer to install dependencies manually:

**Using uv:**
```bash
uv add beautifulsoup4 tqdm aiohttp jinja2 urllib3
```

**Using pip:**
```bash
pip install beautifulsoup4 tqdm aiohttp jinja2 urllib3
```

---

## Usage

Simply run the script - it will handle everything automatically:

```bash
python3 domain_checker.py
```

The script will:
1. 🔍 Check and install required packages
2. 🔧 Detect your control panel (cPanel/DirectAdmin)
3. 📋 Gather all domain information
4. ⚡ Check domain IPs and status codes concurrently
5. 📊 Generate comprehensive reports

---

## Output Files

The script generates comprehensive results in the `/home/transfer/` directory:

### Domain Lists
- **`direct_domains.txt`**: Domains pointing directly to the server
- **`healthy_domains.txt`**: Domains with IP mismatches but functioning correctly
- **`mismatched_domains.txt`**: Domains with IP mismatches that failed validation
- **`no_ping_domains.txt`**: Domains that could not be resolved
- **`combined_domains.txt`**: All healthy and direct domains combined

### Reports & Logs
- **`domain_report.html`**: 🎨 Beautiful HTML report with color-coded status
- **`domain_status.log`**: 📝 Main execution log with detailed information
- **`domain_errors.log`**: ❌ Error-specific log for troubleshooting
- **`domain_statuses.log`**: 🌐 HTTP status codes for each domain

---

## HTML Report Features

The generated HTML report includes:
- **Color-coded rows** for easy status identification
- **Responsive table** with domain, status, IP, and HTTP code
- **Visual indicators**:
  - 🟢 **Green**: Healthy domains
  - 🔵 **Blue**: Direct domains  
  - 🔴 **Red**: Mismatched domains
  - 🟡 **Yellow**: No ping domains

---

## Configuration

### Environment Constants
You can modify these constants in the script:

```python
CPANEL_PATH = "/usr/local/cpanel"           # cPanel installation path
DIRECTADMIN_PATH = "/usr/local/directadmin" # DirectAdmin installation path  
TRANSFER_DIR = "/home/transfer"             # Output directory
USERDATA_DOMAINS_FILE = "/etc/userdatadomains" # cPanel domains file
```

### Performance Tuning
The script automatically adjusts thread count based on CPU cores:
```python
max_workers = max(2, multiprocessing.cpu_count())
```

---

## Domain Status Categories

| Status | Description | Color |
|--------|-------------|-------|
| **Direct** | Domain points directly to server IP | 🔵 Blue |
| **Healthy** | Domain has IP mismatch but passes validation | 🟢 Green |
| **Mismatched** | Domain has IP mismatch and fails validation | 🔴 Red |
| **No Ping** | Domain cannot be resolved or reached | 🟡 Yellow |

---

## Example Output

```bash
==================================================
Domain Status Checker - Auto Installation
==================================================
🔍 Checking required packages...
✅ All required packages are already installed!

🔄 Loading modules...
✅ All modules loaded successfully!
==================================================

🚀 Starting Domain Status Checker...
✅ Found 150 domains
🖥️  Server IP: 192.168.1.100
🎛️  Control Panel: cpanel

Checking domains: 100%|███████████████| 150/150 [00:45<00:00,  3.33it/s]
Checking domain statuses: 100%|████████| 120/120 [00:30<00:00,  4.00it/s]

📊 Results Summary:
✅ Direct domains: 85
🟢 Healthy domains: 35
🔴 Mismatched domains: 15
🟡 No ping domains: 15

📁 Files saved in /home/transfer/
```

---

## Technical Details

### Supported Control Panels
- **cPanel**: Uses `whmapi1` API for domain discovery
- **DirectAdmin**: Scans `/home/*/domains/` directories

### Domain Validation Process
1. **DNS Resolution**: Resolve domain to IP address
2. **IP Comparison**: Compare with server IP
3. **File Upload Test**: Upload test file for validation
4. **HTTP Status Check**: Verify domain accessibility
5. **Report Generation**: Create comprehensive status report

### Async Architecture
- **Concurrent DNS resolution** for faster processing
- **Async HTTP requests** using aiohttp
- **Thread pool execution** for I/O operations
- **Progress tracking** with tqdm

---

## Requirements

### System Requirements
- **Python 3.7+**
- **Linux server** with cPanel or DirectAdmin
- **Root/sudo access** for control panel file access

### Python Dependencies (Auto-installed)
```python
beautifulsoup4>=4.12.0  # HTML parsing
tqdm>=4.66.0           # Progress bars  
aiohttp>=3.9.0         # Async HTTP requests
jinja2>=3.1.0          # HTML template rendering
urllib3>=2.0.0         # HTTP client
```

---

## Troubleshooting

### Common Issues

**Package Installation Fails:**
```bash
# Manually install with uv
uv add beautifulsoup4 tqdm aiohttp jinja2 urllib3

# Or with pip
pip install beautifulsoup4 tqdm aiohttp jinja2 urllib3
```

**Permission Denied:**
```bash
# Run with appropriate permissions
sudo python3 domain_checker.py
```

**No Domains Found:**
- Verify control panel installation
- Check file permissions for domain configuration files
- Review error logs in `domain_errors.log`

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## Changelog

### v2.0.0
- ✨ Added auto-installation of dependencies
- ✨ Added HTML report generation  
- ✨ Added async processing for better performance
- ✨ Added comprehensive logging system
- ✨ Added support for uv package manager
- 🔧 Improved error handling and user feedback
- 🔧 Enhanced progress tracking with tqdm
