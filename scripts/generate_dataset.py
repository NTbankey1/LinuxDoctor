"""
Linux Doctor — Synthetic Dataset Generator

Generates 7000+ labeled training samples across all 12 domains.
Uses KB templates + paraphrasing + combinatorial expansion.

Output: data/raw/linux_issues.jsonl (append mode, deduplicated)
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path

DATA_PATH = Path("data/raw/linux_issues.jsonl")
SEED = 42
random.seed(SEED)

# ================================================================
# DOMAIN VOCABULARY — one entry per domain
# ================================================================

DomainConfig = dict

DOMAINS: dict[str, DomainConfig] = {
    "docker": {
        "intents": ["service_failure", "permission_denied", "resource_exhaustion",
                     "connection_failure", "build_failure", "config_error"],
        "symptoms": ["SYM_DOCKER_DAEMON_DOWN", "SYM_DOCKER_PERMISSION_ERROR",
                     "SYM_DOCKER_OOM", "SYM_DOCKER_DISK_FULL",
                     "SYM_DOCKER_CONTAINER_EXIT"],
        "templates": [
            # Daemon / connection
            "Cannot connect to the Docker daemon at {socket}. Is the docker daemon running?",
            "docker: Cannot connect to the Docker daemon. Is the docker daemon running on this host?",
            "Got permission denied while trying to connect to the Docker daemon socket at {socket}",
            "docker: permission denied while connecting to {socket}",
            "Error response from daemon: No such container: {container}",
            "Error response from daemon: container {container} not found",
            "Error response from daemon: No such image: {image}",
            "Error response from daemon: conflict: unable to delete {name} (cannot be forced)",
            # Disk / storage
            "No space left on device when writing to {docker_dir}",
            "write {docker_dir}/overlay2/{hash}: no space left on device",
            "docker build failed: no space left on device on {path}",
            "docker: failed to register layer: no space left on device",
            "docker run failed: insufficient storage space in {docker_dir}",
            # OOM / memory
            "docker container {container} exited with code 137 (OOM killed)",
            "container {container} OOM killed: memory limit {limit} exceeded",
            "docker: container {container} was killed by OOM killer",
            "docker run failed: memory max limit {limit} reached for container {container}",
            # Restart / crash
            "docker container {container} keeps restarting with exit code {code}",
            "container {container} crashed immediately after start with exit code {code}",
            "docker: container {container} in crash loop backoff restarting",
            "container {container} restarting ({count} seconds) - Kubernetes CrashLoopBackOff",
            # Permission
            "docker: Got permission denied while trying to connect to {socket}",
            "docker: dial unix {socket}: connect: permission denied",
            "WARNING: Error loading config file: {file} - stat {file}: permission denied",
            # Network
            "failed to create network {net}: bridge already exists with the same name",
            "docker network create failed: network {net} already exists",
            "docker: Error response from daemon: network {net} not found",
            "docker pull failed: connection timeout to registry {registry}",
            "docker push failed: unauthorized: authentication required",
            "docker: request canceled while waiting for connection (Client.Timeout)",
            # Build / images
            "docker build failed: unable to prepare context: path {path} not found",
            "docker build: COPY failed: file not found in build context",
            "docker build: failed to fetch metadata: error getting credentials",
            "docker: image {image} not found locally, pull failed",
            # General
            "docker daemon not running after reboot: systemctl status docker shows inactive",
            "docker: failed to start docker.service: unit docker.service not found",
            "docker service failed to start: {error_output}",
            "docker info shows error: cannot connect to the Docker daemon",
            "docker ps -a shows no containers but they should exist",
            "docker logs {container} shows nothing: container has no logs",
            # Short query patterns (handles "docker err", "docker fail")
            "docker error: cannot connect to {socket}",
            "docker error: container {container} exited with code {code}",
            "docker error: {docker_dir} is out of space",
            "docker error: daemon not responding on {socket}",
            "docker fail: cannot pull image {image} from {registry}",
        ],
        "slots": {
            "socket": ["unix:///var/run/docker.sock", "/var/run/docker.sock", "/run/docker.sock"],
            "container": ["myapp", "webapp", "api-server", "db", "redis", "worker", "nginx-proxy", "postgresql", "mysql", "rabbitmq", "elasticsearch", "my_container", "app-1"],
            "image": ["ubuntu:latest", "alpine:3.19", "python:3.12", "node:22", "nginx:alpine", "postgres:16", "redis:7"],
            "name": ["mycontainer", "test_image", "web_container", "old_container"],
            "docker_dir": ["/var/lib/docker", "/mnt/docker", "/data/docker"],
            "hash": ["abc123def456", "deadbeef", "facefeed", "cafebabe"],
            "path": ["/var/lib/docker", "/tmp/build", "/home/user/project", "/app"],
            "limit": ["512m", "256m", "1g", "128m", "64m"],
            "code": ["1", "127", "137", "139", "143"],
            "count": ["5", "10", "20", "50", "100", "3"],
            "net": ["bridge", "my-network", "app_network", "backend-net", "frontend-net"],
            "registry": ["docker.io", "ghcr.io", "registry.gitlab.com", "my-registry.com:5000", "ecr.amazonaws.com"],
            "file": ["~/.docker/config.json", "/etc/docker/daemon.json", "Dockerfile"],
            "error_output": ["Process exited with code 1", "Failed to start daemon", "Timeout was reached", "Journal reported: failed to start"],
        },
    },

    "nginx": {
        "intents": ["service_failure", "config_error", "permission_denied",
                     "upstream_error", "ssl_error", "resource_exhaustion"],
        "symptoms": ["SYM_NGINX_START_FAILURE", "SYM_NGINX_BIND_FAILURE",
                     "SYM_NGINX_CONFIG_ERROR", "SYM_NGINX_PERMISSION_ERROR",
                     "SYM_NGINX_UPSTREAM_ERROR"],
        "templates": [
            # Bind / port
            "nginx: [emerg] bind() to 0.0.0.0:{port} failed ({errno}: {bind_error})",
            "nginx failed to start: address already in use on port {port}",
            "nginx: bind() to [::]:{port} failed ({errno}: Address already in use)",
            "nginx cannot bind to port {port}: port is already in use by {process}",
            # Config
            "nginx: [emerg] unknown directive \"{directive}\" in {config_file}:{line}",
            "nginx configuration test failed: syntax error in {config_file} line {line}",
            "nginx -t shows test failed: unexpected end of file in {config_file}",
            "nginx: configuration file {config_file} test failed",
            "nginx: [emerg] \"{directive}\" directive is not allowed here in {config_file}",
            # Permission
            "nginx: [emerg] open() \"{log_path}\" failed ({errno}: Permission denied)",
            "nginx 403 forbidden: directory index of \"{webroot}\" is forbidden",
            "nginx: cannot access webroot {webroot}: permission denied",
            "nginx: stat() {webroot} failed ({errno}: Permission denied)",
            # Upstream / 502
            "nginx 502 bad gateway: upstream {upstream} returned no response",
            "nginx: upstream {upstream} failed (111: Connection refused)",
            "nginx 504 gateway timeout: upstream {upstream} timed out after {timeout}s",
            "nginx: no live upstreams while connecting to upstream {upstream}",
            "nginx upstream sent no valid HTTP response while reading upstream",
            # SSL
            "nginx: [emerg] SSL_CTX_use_PrivateKey_file(\"{cert_path}\") failed",
            "nginx: ssl certificate {cert_path} has expired",
            "nginx: cannot load certificate {cert_path}: BIO_new_file() failed",
            # General
            "nginx worker process exited with signal {signal}",
            "nginx: too many open files (ulimit) cannot accept connections",
            "nginx: open file limit {limit} reached",
            "nginx failed to reload: configuration file {config_file} test failed",
            "nginx rewrite rule not working in {config_file} location block",
            "nginx try_files directive not working properly",
            # Extra failure patterns (boost nginx signal against systemd overlap)
            "nginx failed to start: service not responding",
            "nginx start failure: {process} is already listening on port {port}",
            "nginx startup error: nginx cannot bind to port {port}",
            "nginx failing to start after config change: {config_file} has errors",
            "nginx error: failed to start service, see journalctl for details",
            "nginx crashes on start: {log_path} shows bind() error on port {port}",
            "nginx start error: could not open configuration file {config_file}",
            "nginx keeps failing: unable to start because port {port} is in use",
            "nginx startup problem: cannot access {webroot} permission error",
            "nginx not running: service failed to start after reboot",
            "nginx error log: connection to {upstream} failed upstream timeout",
            "nginx crash: worker process died with signal {signal}",
            # Nginx not installed patterns (must NOT trigger "package" domain)
            "nginx is not installed: nginx command not found on this system",
            "nginx binary not found: which nginx returns nothing on this server",
            "nginx not found: the nginx web server binary is missing",
            "the nginx service does not exist: no unit file found for nginx",
            "nginx cannot be started: nginx is not installed on this machine",
            "i tried to start nginx but it is not installed: command not found",
            "nginx missing: the nginx package was not found on this system",
            "nginx binary missing: /usr/sbin/nginx does not exist",
        ],
        "slots": {
            "port": ["80", "443", "8080", "3000", "8443"],
            "errno": ["98", "13", "99", "22"],
            "bind_error": ["Address already in use", "Cannot assign requested address", "Permission denied"],
            "process": ["apache2", "httpd", "caddy", "another nginx", "node server", "python app"],
            "directive": ["root", "proxy_pass", "fastcgi_pass", "server_name", "location", "add_header", "return", "rewrite"],
            "config_file": ["/etc/nginx/nginx.conf", "/etc/nginx/conf.d/default.conf", "/etc/nginx/sites-enabled/default", "/etc/nginx/sites-available/app.conf", "/usr/local/nginx/conf/nginx.conf"],
            "line": ["12", "23", "45", "67", "89", "112", "3", "7", "15"],
            "webroot": ["/var/www/html", "/usr/share/nginx/html", "/var/www/app/public", "/home/user/public_html", "/srv/http"],
            "log_path": ["/var/log/nginx/error.log", "/var/log/nginx/access.log", "/var/log/nginx/error.log.1"],
            "cert_path": ["/etc/ssl/certs/nginx.crt", "/etc/letsencrypt/live/domain/fullchain.pem", "/etc/pki/tls/certs/nginx.crt"],
            "upstream": ["http://backend:8080", "http://127.0.0.1:3000", "unix:/tmp/uwsgi.sock", "http://app-server:9000", "http://api:4000"],
            "timeout": ["30", "60", "120", "300", "10"],
            "signal": ["SIGSEGV", "SIGKILL", "SIGTERM", "SIGABRT", "6", "11", "9"],
            "limit": ["1024", "4096", "65536", "10240", "512"],
        },
    },

    "ssh": {
        "intents": ["connection_failure", "authentication_failure", "config_error",
                     "timeout", "host_key_mismatch"],
        "symptoms": ["SYM_SSH_CONNECTION_REFUSED", "SYM_SSH_PERMISSION_DENIED",
                     "SYM_SSH_HOST_KEY_MISMATCH", "SYM_SSH_TIMEOUT"],
        "templates": [
            "ssh: connect to host {host} port {port}: Connection refused",
            "ssh: connect to host {host} port {port}: No route to host",
            "ssh: Could not resolve hostname {host}: Name or service not known",
            "ssh: connect to host {host} port {port}: Network is unreachable",
            "ssh permission denied (publickey,password)",
            "ssh: Permission denied (publickey,gssapi-with-mic,password)",
            "ssh authentication failed: public key not authorized on {host}",
            "ssh: too many authentication failures for user {user}",
            "@@@@@@@@@@@@@@@@@@@@@ WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED! @@@@@@@@@@@@@@@@@@@",
            "ssh: WARNING: Remote host identification has changed for host {host}",
            "ssh: host key verification failed for {host}",
            "ssh connection to {host} timed out after {timeout} seconds",
            "ssh: connect to host {host} port {port}: Connection timed out",
            "sshd: service not running: connection refused on port {port}",
            "ssh: bad permissions: ~/.ssh/config has bad permissions",
            "ssh: key_load_public: invalid format for key {key_path}",
            "ssh: Permission denied (publickey). Could not authenticate with key {key_path}",
            "ssh-agent has no identities: ssh-add -l shows empty",
            "ssh: connect to host {host} port {port}: Broken pipe",
            "ssh: connection closed by remote host after {timeout}s idle",
            "ssh port 22 blocked by {firewall}: connection refused",
            "ssh: Could not request forwarding on port {port}",
            "ssh X11 forwarding: connection refused by remote server",
            "ssh banner exchange: connection to {host} timed out",
        ],
        "slots": {
            "host": ["192.168.1.10", "10.0.0.5", "example.com", "gitlab.com", "github.com", "server.example.org", "172.16.0.100", "ec2-54-123-45-67.compute-1.amazonaws.com"],
            "port": ["22", "2222", "222", "22222", "8022"],
            "timeout": ["10", "30", "60", "120", "15"],
            "user": ["root", "ubuntu", "admin", "deploy", "git", "ec2-user", "centos", "ntbankey"],
            "key_path": ["~/.ssh/id_rsa", "~/.ssh/id_ed25519", "~/.ssh/id_ecdsa", "/home/user/.ssh/id_rsa"],
            "firewall": ["UFW", "iptables", "firewalld", "nftables", "AWS security group"],
        },
    },

    "disk": {
        "intents": ["resource_exhaustion", "io_error", "mount_failure", "filesystem_corruption"],
        "symptoms": ["SYM_DISK_FULL", "SYM_DISK_INODE_FULL", "SYM_DISK_READ_ERROR", "SYM_DISK_MOUNT_FAIL", "SYM_DISK_RO_REMOUNT"],
        "templates": [
            "No space left on device: cannot write to {path}",
            "df -h shows {pct}% full on {mount}: {used}/{size} used",
            "write failed: {path}: no space left on device (ENOSPC)",
            "Filesystem {mount} is {pct}% full, {avail} remaining",
            "Disk quota exceeded: user {user} cannot write to {path}",
            "read-only file system: cannot create file {path}",
            "Filesystem {device} has been remounted read-only: I/O error detected",
            "ext4-fs error: unable to read superblock on {device}",
            "fsck returned errors on {device}: filesystem corruption detected",
            "EXT4-fs error: {device}: journal has aborted",
            "mount: {device} not mounted: mount point {mount} does not exist",
            "mount: wrong fs type, bad option, bad superblock on {device}",
            "mount: {device} cannot be mounted: device not found",
            "inode exhaustion: df -h shows free space but df -i shows {pct_i}% inodes used",
            "No space left on device but df shows {pct}% usage: inodes full",
            "disk I/O error: Buffer I/O error on device {device}",
            "smartctl shows disk {device} health FAILED: {sectors} reallocated sectors",
            "I/O error reading {path}: Input/output error",
            "LVM: Volume group {vg} has insufficient free space ({free} remaining)",
            "Cannot extend logical volume {lv}: no free space in volume group {vg}",
            "tmpfs {mount} is full: cannot create temporary files in {path}",
        ],
        "slots": {
            "path": ["/var/log", "/tmp", "/var/lib/docker", "/home", "/var/log/syslog", "/var/cache/apt", "/data/db", "/opt/app/logs"],
            "mount": ["/", "/var", "/home", "/data", "/var/log", "/boot", "/opt", "/mnt/storage"],
            "device": ["/dev/sda1", "/dev/sdb1", "/dev/nvme0n1p2", "/dev/mapper/vg-root", "/dev/sdc", "/dev/xvda1"],
            "pct": ["95", "97", "99", "100", "92", "88"],
            "pct_i": ["95", "98", "100", "99", "93"],
            "used": ["500G", "1.5T", "890G", "2.3T", "45G"],
            "size": ["512G", "1.6T", "900G", "2.5T", "50G"],
            "avail": ["12G", "8.5G", "100M", "0", "5G"],
            "user": ["www-data", "postgres", "mysql", "nobody", "root", "ubuntu"],
            "sectors": ["45", "128", "512", "1024", "2048", "5"],
            "vg": ["vg_main", "vg_data", "vg_root", "vg_opt", "VolGroup00"],
            "lv": ["lv_root", "lv_var", "lv_home", "lv_docker", "lv_log", "lv_data"],
            "free": ["0", "100M", "1G", "500M", "10G"],
        },
    },

    "memory": {
        "intents": ["oom_kill", "resource_exhaustion", "memory_pressure", "swap_exhaustion"],
        "symptoms": ["SYM_MEM_OOM", "SYM_MEM_HIGH", "SYM_MEM_SWAP_EXHAUST", "SYM_MEM_LEAK"],
        "templates": [
            "Out of memory: Killed process {pid} ({process}) total-vm:{vm}kB",
            "oom-killer: gfp_mask=0x{gfp}, order={order}, oom_score_adj={score}",
            "killed process {pid} ({process}) due to out of memory",
            "Process {process} (PID {pid}) was killed by OOM killer",
            "free -m shows {avail}MB available out of {total}MB total: memory exhausted",
            "swap space exhausted: {used_swap}MB used of {total_swap}MB total swap",
            "cannot allocate memory: malloc failed in {process} at line {line}",
            "mmap failed: Cannot allocate memory for {process}",
            "memory cgroup out of memory: killed process {process} in cgroup {cgroup}",
            "Memory usage at {pct}%: {used}GB used out of {total}GB RAM",
            "Process {process} using {rss}MB RSS: possible memory leak",
            "ps aux shows {process} using {pct_mem}% memory: abnormal memory usage",
            "vmstat shows active page scanning: swap in/out heavy at {si}/{so} blocks",
            "kernel: page allocation failure: order:{order}, mode:0x{mode}",
            "zone {zone} low on memory: pages {free_pages} free, min {min_pages}",
            "failed to allocate {size} bytes: out of memory in {process}",
        ],
        "slots": {
            "pid": ["1234", "5678", "9012", "3456", "7890", "1111", "2222", "3333"],
            "process": ["nginx", "docker", "python3", "node", "java", "mysql", "postgres", "chrome", "firefox", "gunicorn", "celery", "ruby", "php-fpm", "java"],
            "vm": ["12345678", "87654321", "45678901", "23456789", "98765432"],
            "gfp": ["0x100cca", "0x24200ca", "0x400dc0"],
            "order": ["0", "4", "2", "1", "3"],
            "score": ["0", "200", "500", "800", "1000"],
            "total": ["16", "32", "64", "8", "128", "48"],
            "avail": ["128", "512", "256", "64", "0", "1024"],
            "used_swap": ["8", "16", "32", "0", "4"],
            "total_swap": ["8", "16", "32", "2", "4"],
            "line": ["1024", "256", "512", "128"],
            "cgroup": ["/docker/abc123", "/system.slice/docker.service", "/kubepods/besteffort"],
            "rss": ["2048", "4096", "8192", "12000", "1536", "512"],
            "pct": ["89", "95", "97", "99", "92", "87"],
            "used_gb": ["14", "30", "60", "7", "120"],
            "total_gb": ["16", "32", "64", "8", "128"],
            "pct_mem": ["45", "60", "75", "90", "99", "30"],
            "si": ["1024", "2048", "512", "4096"],
            "so": ["2048", "4096", "1024", "8192"],
            "mode": ["0x80000000", "0x14000a", "0x24000c0"],
            "zone": ["DMA", "Normal", "DMA32", "Movable"],
            "free_pages": ["4", "10", "20", "0", "50"],
            "min_pages": ["30", "50", "100", "25", "75"],
            "size": ["4096", "8192", "16384", "32768", "65536"],
        },
    },

    "cpu": {
        "intents": ["high_usage", "runaway_process", "zombie_process", "resource_exhaustion"],
        "symptoms": ["SYM_CPU_HIGH_LOAD", "SYM_CPU_RUNAWAY", "SYM_CPU_ZOMBIE", "SYM_CPU_STEAL"],
        "templates": [
            "Process {process} (PID {pid}) using {pct}% CPU: possible runaway process",
            "top shows {process} at {pct}% CPU usage: load average {load_1} {load_5} {load_15}",
            "CPU usage at {pct}% across {cores} cores: system overloaded",
            "load average: {load_1}, {load_5}, {load_15} — system load exceeds core count ({cores})",
            "{count} zombie processes detected: zombie accumulation",
            "zombie process {pid} ({process}) cannot be killed: defunct state",
            "cpu steal time at {steal}%: hypervisor overcommit detected",
            "MPSTAT shows {steal}% steal time: VM competing for CPU resources",
            "high context switching: {ctx_sec} context switches per second",
            "interrupt storm: {int_sec} interrupts per second on CPU {cpu}",
            "process {process} stuck in D state (uninterruptible sleep) for {time}s",
            "{count} processes in D state: IO wait causing CPU starvation",
            "CPU throttling: thermal limit reached, frequency reduced to {freq}MHz",
            "htop shows all {cores} cores at {pct}% usage",
            "CPU temperature {temp}°C: thermal throttling activated",
        ],
        "slots": {
            "process": ["chrome", "firefox", "python3", "node", "java", "gunicorn", "celery", "dd", "tar", "gzip", "cryptominer", "mysql", "php-fpm", "ruby"],
            "pid": ["1234", "5678", "9012", "3456", "7890"],
            "pct": ["99", "100", "95", "85", "75", "50", "45"],
            "load_1": ["12.5", "8.3", "15.7", "22.1", "6.2", "4.5"],
            "load_5": ["10.2", "7.1", "12.4", "18.5", "5.8", "3.2"],
            "load_15": ["8.1", "5.6", "9.2", "14.3", "4.2", "2.8"],
            "cores": ["2", "4", "8", "16", "32", "1"],
            "count": ["5", "12", "20", "50", "100", "3"],
            "steal": ["15", "25", "40", "10", "30", "50"],
            "ctx_sec": ["50000", "100000", "250000", "500000", "1000000"],
            "int_sec": ["10000", "25000", "50000", "100000", "200000"],
            "cpu": ["0", "1", "2", "3", "all"],
            "time": ["30", "60", "120", "300", "600", "15"],
            "freq": ["800", "1200", "1500", "2000", "400"],
            "temp": ["85", "90", "95", "100", "105", "110"],
        },
    },

    "network": {
        "intents": ["connection_failure", "firewall_block", "interface_down", "dns_failure", "latency"],
        "symptoms": ["SYM_NET_NO_CONNECT", "SYM_NET_DNS_FAIL", "SYM_NET_FIREWALL",
                     "SYM_NET_INTERFACE_DOWN", "SYM_NET_PORT_CLOSED"],
        "templates": [
            "connect: Network is unreachable to {host}:{port}",
            "ping: connect: Network is unreachable to {host}",
            "curl: (7) Failed to connect to {host} port {port}: Connection refused",
            "curl: (28) Connection timed out after {timeout}ms to {host}:{port}",
            "wget: unable to resolve host address '{host}'",
            "ss -tulpn shows port {port} not listening: service may be down",
            "netstat: address already in use on port {port} by {process}",
            "iptables -L shows DROP policy on INPUT: firewall blocking traffic",
            "UFW: deny incoming on port {port} from {subnet}",
            "firewall-cmd: port {port} not open: connection blocked",
            "ip link show {iface}: state DOWN, carrier {carrier}",
            "interface {iface} is DOWN: no link detected",
            "ip route: no default gateway configured: routing table empty",
            "route -n shows default gateway {gateway} is unreachable",
            "TCP connection reset by peer on port {port} to {host}",
            "connection to {host}:{port} broken pipe: write failed",
            "high packet loss ({loss}%) to {host}: network congestion detected",
            "latency {latency}ms to {host}: unusually high response time",
            "DHCP lease renewal failed: could not obtain IP address on {iface}",
            "ethtool {iface}: Link detected: no, cable disconnected",
        ],
        "slots": {
            "host": ["google.com", "8.8.8.8", "api.example.com", "db.internal", "github.com", "registry.npmjs.org", "pypi.org", "192.168.1.1", "10.0.0.1"],
            "port": ["80", "443", "8080", "3306", "5432", "6379", "27017", "25", "53", "22"],
            "timeout": ["30000", "10000", "60000", "120000", "5000"],
            "process": ["apache2", "nginx", "python", "java", "docker-proxy"],
            "subnet": ["192.168.1.0/24", "10.0.0.0/8", "172.16.0.0/12"],
            "iface": ["eth0", "ens33", "enp0s3", "wlp2s0", "bond0", "docker0", "tun0"],
            "carrier": ["0", "1", "down"],
            "gateway": ["192.168.1.1", "10.0.0.1", "172.16.0.1"],
            "loss": ["10", "25", "50", "75", "5", "2", "1"],
            "latency": ["200", "500", "1000", "3000", "5000", "150"],
        },
    },

    "dns": {
        "intents": ["resolution_failure", "server_timeout", "config_error", "dnssec_failure"],
        "symptoms": ["SYM_DNS_RESOLVE_FAIL", "SYM_DNS_TIMEOUT", "SYM_DNS_MISCONFIG"],
        "templates": [
            "Name or service not known: cannot resolve {host}",
            "Temporary failure in name resolution for {host}",
            "nslookup {host}: server can't find {host}: NXDOMAIN",
            "dig {host} shows status: NXDOMAIN, no such name",
            "resolve: DNS resolution failed for host {host}: timeout",
            "Could not resolve host: {host}; Name or service not known",
            "DNS server {dns_server} not responding: connection timed out",
            "nameserver {dns_server} is unreachable from /etc/resolv.conf",
            "cat /etc/resolv.conf shows invalid nameserver {dns_server}",
            "systemd-resolved is not running: DNS resolution broken",
            "resolvectl status shows no DNS servers configured",
            "DNS query to {dns_server} for {host} returned SERVFAIL",
            "dig +dnssec {host} shows validation failure: DNSSEC error",
            "DNS cache needs flushing: resolvectl flush-caches still stale",
            "hosts file entry for {host} points to wrong IP {wrong_ip}",
            "getent hosts {host} returns 127.0.0.1: /etc/hosts overriding DNS",
            "nsswitch.conf order wrong: files before dns causing resolution issues",
            "DNS over HTTPS not connecting to {dns_server}: TLS handshake failed",
        ],
        "slots": {
            "host": ["google.com", "github.com", "api.example.com", "mail.company.org", "registry.npmjs.org", "pypi.org", "myapp.internal", "docker.io"],
            "dns_server": ["8.8.8.8", "1.1.1.1", "9.9.9.9", "208.67.222.222", "192.168.1.1", "10.0.0.53", "127.0.0.53"],
            "wrong_ip": ["127.0.0.1", "0.0.0.0", "192.168.1.5", "10.0.0.2"],
        },
    },

    "git": {
        "intents": ["push_failure", "auth_failure", "merge_conflict", "repository_corruption", "config_error"],
        "symptoms": ["SYM_GIT_PUSH_FAIL", "SYM_GIT_MERGE_CONFLICT", "SYM_GIT_AUTH_FAIL", "SYM_GIT_REPO_CORRUPT"],
        "templates": [
            "! [rejected] {branch} -> {branch} (non-fast-forward)",
            "git push rejected: failed to push some refs to {remote}",
            "hint: Updates were rejected because the remote contains work that you do not have locally",
            "fatal: unable to access '{remote}': Could not resolve host: {host}",
            "fatal: unable to access '{remote}': SSL certificate problem: self-signed certificate",
            "git: Permission denied (publickey) to {host}",
            "git@github.com: Permission denied (publickey). Authentication failed",
            "fatal: Authentication failed for '{remote}'",
            "Auto-merging {file}: CONFLICT (content): Merge conflict in {file}",
            "Merge conflict in {file}: automatic merge failed; fix conflicts and commit",
            "fatal: repository '{remote}' not found",
            "fatal: Could not read from remote repository: please check access rights",
            "error: object {sha} is a blob, not a commit: git fsck found corruption",
            "fatal: bad object {sha}: git repository corruption detected",
            "fatal: not a git repository (or any parent): .git missing",
            "Your branch is ahead of '{remote}/{branch}' by {n} commits: fast-forward push needed",
            "git: There is no tracking information for the current branch: no upstream configured",
            "error: failed to push some refs to '{remote}': remote hook rejected",
            "remote: error: GH006: Protected branch update failed for {branch}",
            "fatal: refusing to merge unrelated histories: merge aborted",
            "git LFS: {file} exceeds GitHub file size limit of {limit} MB",
            "detached HEAD: You are in 'detached HEAD' state: no branch checked out",
        ],
        "slots": {
            "branch": ["main", "master", "develop", "feature/new-ui", "fix/login-bug", "release/v2.0", "hotfix/security-patch"],
            "remote": ["https://github.com/user/repo.git", "git@github.com:user/repo.git", "https://gitlab.com/user/repo.git", "git@gitlab.com:user/project.git"],
            "host": ["github.com", "gitlab.com", "bitbucket.org", "git.internal.company.com"],
            "file": ["package.json", "main.py", "config.yaml", "docker-compose.yml", "README.md", "src/app.js", "src/main.rs", "Cargo.toml"],
            "sha": ["abc123def456", "deadbeef", "cafebabe", "feedface", "0123456789abcdef"],
            "n": ["1", "3", "5", "10", "25", "2"],
            "limit": ["50", "100", "25", "10"],
        },
    },

    "package": {
        "intents": ["installation_failure", "dependency_error", "lock_conflict", "repo_error", "update_failure"],
        "symptoms": ["SYM_PKG_LOCK", "SYM_PKG_DEPENDENCY", "SYM_PKG_NOT_FOUND", "SYM_PKG_CORRUPT"],
        "templates": [
            "E: Could not get lock /var/lib/dpkg/lock: resource temporarily unavailable",
            "E: Unable to lock the administration directory (/var/lib/dpkg/): another process using it",
            "E: dpkg was interrupted: you must manually run 'dpkg --configure -a'",
            "E: Unable to locate package {pkg}: package not found",
            "Reading package lists... Error! E: Encountered a section with no Package: header",
            "E: Package {pkg} has unmet dependencies: {dep} but it is not going to be installed",
            "The following packages have unmet dependencies: {pkg} depends on {dep} but it is not installed",
            "E: Package {pkg} is not available, but is referred to by another package",
            "apt-get install -y {pkg}: E: Sub-process /usr/bin/dpkg returned an error code (1)",
            "dpkg: error processing package {pkg} (--configure): dependency problems",
            "W: GPG error: {repo} InRelease: The following signatures couldn't be verified because the public key is not available",
            "W: The repository '{repo}' does not have a Release file: 404 Not Found",
            "E: Failed to fetch {url} 404 Not Found [IP: {ip} {port}]",
            "W: Failed to fetch {url}: Hash Sum mismatch",
            "E: Some index files failed to download: 404 Not Found",
            "yum install {pkg}: Error: Package: {pkg}-{version} requires: {dep} but none of the providers can be installed",
            "dnf update: transaction check error: file {path} conflicts between {pkg1} and {pkg2}",
            "dnf makecache: failure: repodata/repomd.xml from {repo}: [Errno 256] No more mirrors to try",
            "pip install {pkg}: ERROR: No matching distribution found for {pkg}",
            "pip install failed: Could not find a version that satisfies the requirement {pkg}",
            "snap install {pkg}: error: cannot install \"{pkg}\": snap not found",
            "rpm -ivh {file}: error: Failed dependencies: {dep} is needed by {pkg}",
        ],
        "slots": {
            "pkg": ["nginx", "docker-ce", "python3-pip", "nodejs", "postgresql", "libssl-dev", "build-essential", "curl", "wget", "git", "vim", "htop", "net-tools", "docker-compose"],
            "pkg1": ["nginx-core", "docker-ce", "python3", "httpd"],
            "pkg2": ["nginx-common", "docker-ce-cli", "python3.11", "apache2"],
            "dep": ["libssl3", "python3 >= 3.10", "systemd", "glibc >= 2.35", "libc6 >= 2.38"],
            "version": ["1.24.0", "24.0.7", "3.12.1", "20.11.1", "16.2"],
            "repo": ["http://archive.ubuntu.com/ubuntu", "https://deb.debian.org/debian", "https://download.docker.com/linux/ubuntu", "http://mirror.centos.org/centos"],
            "url": ["http://archive.ubuntu.com/ubuntu/dists/jammy/InRelease", "http://security.debian.org/debian-security/dists/bookworm-security/InRelease"],
            "ip": ["91.189.91.38", "151.101.130.132", "140.211.166.134"],
            "port": ["80", "443", "8080"],
            "path": ["/usr/bin/docker", "/usr/sbin/nginx", "/etc/apt/sources.list", "/etc/yum.repos.d/epel.repo"],
            "file": ["package.rpm", "package.deb", "app.snap", "package.flatpak"],
        },
    },

    "systemd": {
        "intents": ["service_failure", "dependency_error", "timeout", "config_error", "journal_error"],
        "symptoms": ["SYM_SD_SERVICE_FAIL", "SYM_SD_DEPENDENCY", "SYM_SD_TIMEOUT", "SYM_SD_MASKED", "SYM_SD_CGROUP"],
        "templates": [
            "systemctl start {service}: Job for {service}.service failed because the control process exited with error code",
            "systemctl status {service}: Active: failed (Result: exit-code) since {date}",
            "systemctl status {service}: Active: inactive (dead)",
            "systemctl: Unit {service}.service is masked, ignoring: cannot start",
            "systemctl unmask {service}: unit is currently masked, preventing startup",
            "systemctl: Failed to start {service}.service: Unit not found",
            "systemctl list-dependencies {service}: dependency failed for {dependency}",
            "Job for {service}.service failed because a configured dependency failed",
            "systemctl start {service}: Job for {service}.service timed out",
            "Timed out waiting for {service} to start: start operation timed out",
            "systemctl: start-limit-hit: {service}.service start request repeated too quickly",
            "systemctl reset-failed {service}: exceeded start limit",
            "journalctl -u {service}: {process} crashed with signal {signal} (core dumped)",
            "journalctl -xe: Unit {service}.service has failed: {error_desc}",
            "systemd-analyze verify: {unit}: syntax error at line {line}",
            "systemctl edit {service}: failed to create drop-in file: permission denied",
            "systemctl show {service}: TasksMax={limit} exceeded, process killed by cgroup",
            "cgroup: memory limit {limit} reached for {service}: OOM killed by systemd",
            "systemctl daemon-reload: failed to reload daemon: {error}",
            "systemctl enable {service}: failed to create symlink: permission denied",
            "systemd journal: journal file corrupted, rotating and cleaning required",
            "journalctl --verify: FAIL: journal file {path} has corruption errors",
        ],
        "slots": {
            "service": ["nginx", "docker", "sshd", "postgresql", "mysql", "redis", "httpd", "network", "ufw", "cron", "fail2ban", "prometheus", "grafana", "gitlab-runner"],
            "dependency": ["network.target", "multi-user.target", "postgresql.service", "docker.service", "local-fs.target", "remote-fs.target"],
            "date": ["Mon 2026-06-01 10:23:45 UTC", "Sun 2026-05-31 22:15:30 UTC", "Tue 2026-06-02 08:00:00 UTC"],
            "process": ["nginx", "docker-containerd", "sshd", "postmaster", "mysqld", "redis-server"],
            "signal": ["SIGSEGV", "SIGKILL", "SIGTERM", "SIGABRT", "SIGBUS", "6", "11", "9"],
            "error_desc": ["exit code 1", "segfault at 0x0", "process was killed by SIGKILL", "timeout reached"],
            "unit": ["/etc/systemd/system/{service}.service", "/lib/systemd/system/{service}.service"],
            "line": ["5", "12", "23", "45", "67"],
            "limit": ["100", "500", "1024", "4096", "50", "200"],
            "error": ["Invalid argument", "File exists", "No such file or directory"],
            "path": ["/var/log/journal", "/run/log/journal", "/var/log/journal/abc123"],
        },
    },

    "permission": {
        "intents": ["file_access_denied", "execution_denied", "ownership_error", "selinux_block", "ssh_key_perms"],
        "symptoms": ["SYM_PERM_FILE_DENIED", "SYM_PERM_EXEC_DENIED", "SYM_PERM_OWNERSHIP", "SYM_PERM_SELINUX"],
        "templates": [
            "Permission denied: cannot open file {path} for reading",
            "cat {path}: Permission denied",
            "ls -la {path}: Permission denied on directory",
            "bash: {path}: Permission denied: cannot execute binary",
            "cannot execute binary at {path}: Permission denied",
            "exec format error: {path}: cannot execute binary",
            "chown: changing ownership of {path}: Operation not permitted",
            "chmod: changing permissions of {path}: Operation not permitted",
            "File {path} has wrong owner {owner}: expected {expected_owner}",
            "File {path} has wrong permissions {perms}: expected {expected_perms}",
            "SELinux: AVC denial for {process} accessing {path}",
            "SELinux is preventing {process} from {action} access on {path}",
            "ausearch -m avc shows denial for {process} to {path}: context mismatch",
            "getenforce shows Enforcing: SELinux blocking {process}",
            "sudo: unable to execute {command}: Permission denied",
            "sudo: {user} is not in the sudoers file. This incident will be reported.",
            "umask set too restrictive: file {path} created with incorrect permissions {perms}",
            "AppArmor: DENIED {action} of {process} for {path}",
            "setuid bit missing on {path}: cannot escalate to root permissions",
            "ACL check failed: user {user} does not have {action} permission on {path}",
            "autofs: permission denied on automount point {path}",
            "nfs mount: access denied by server while mounting {path}",
            "filesystem mounted with noexec: cannot execute binaries on {mount}",
            "/tmp mounted with noexec flag: scripts cannot run from {path}",
        ],
        "slots": {
            "path": ["/var/log/syslog", "/etc/shadow", "/etc/ssl/private/key.pem", "/root/.ssh/authorized_keys", "/var/www/html/index.html", "/etc/nginx/nginx.conf", "/var/lib/docker", "/proc/1/environ", "/home/user/private.key"],
            "owner": ["root", "nobody", "www-data", "bin", "1000"],
            "expected_owner": ["www-data", "nginx", "postgres", "mysql", "docker"],
            "perms": ["0777", "0644", "000", "777", "666", "rwx------", "rw-rw-rw-", "----------"],
            "expected_perms": ["0755", "0644", "0600", "0700", "rwxr-xr-x", "rw-r--r--", "rw-------"],
            "process": ["nginx", "httpd", "sshd", "docker", "postgres", "mysql", "apache2"],
            "action": ["read", "write", "execute", "connect", "bind", "name_connect"],
            "command": ["systemctl start nginx", "docker compose up", "ssh user@host", "apt-get update"],
            "user": ["ntbankey", "ubuntu", "admin", "root", "www-data", "nobody", "deploy"],
            "mount": ["/tmp", "/var/tmp", "/dev/shm", "/home"],
        },
    },
}


def generate_samples() -> list[dict]:
    """Generate all samples from templates for all domains."""
    samples = []
    seen_hashes = set()

    for domain, config in DOMAINS.items():
        templates = config["templates"]
        slots = config["slots"]
        intents = config["intents"]

        for template in templates:
            # Extract slot names from template
            found_slots = re.findall(r"\{(\w+)\}", template)
            if not found_slots:
                # Static template with no slots
                text = template
                h = hashlib.md5(text.encode()).hexdigest()
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    intent = random.choice(intents)
                    samples.append({
                        "text": text,
                        "label": domain,
                        "intent": intent,
                    })
                continue

            # Generate up to 60-100 variations per template
            max_variations = min(100, max(60, 8000 // len(templates) + 20))

            for _ in range(max_variations):
                filled = template
                for slot in found_slots:
                    if slot in slots:
                        filled = filled.replace(f"{{{slot}}}", random.choice(slots[slot]), 1)

                h = hashlib.md5(filled.encode()).hexdigest()
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    intent = random.choice(intents)
                    samples.append({
                        "text": filled,
                        "label": domain,
                        "intent": intent,
                    })

        # Add paraphrased variants
        extra_variants = {
            "docker": [
                "docker daemon is unreachable on {socket}",
                "cannot run docker containers: {socket} access denied",
                "docker storage at {docker_dir} is full: cleanup needed",
                "container {container} uses too much memory: OOM risk",
            ],
            "nginx": [
                "{config_file} line {line} has invalid directive: nginx fails to reload",
                "there is a problem with the nginx upstream {upstream} on port {port}",
                "please check nginx configuration: syntax error detected",
            ],
            "ssh": [
                "i cannot ssh into {host} on port {port}: connection is refused",
                "ssh to {host} failed: authentication rejected for user {user}",
                "the ssh server at {host} is not reachable: network seems down",
            ],
            "disk": [
                "my disk is full on {mount}: {pct}% used cannot write files",
                "filesystem {device} is broken: fsck reports errors",
                "please check disk space at {path}: running out of storage",
            ],
            "memory": [
                "the system is running out of memory: process {process} was killed",
                "swap is full: memory pressure on server with {total_gb}GB RAM",
                "application {process} has memory leak: RSS is {rss}MB and growing",
            ],
            "cpu": [
                "server is very slow: load average {load_1} is too high on {cores} cores",
                "a process is stuck at {pct}% CPU and needs to be killed",
                "there are too many zombies ({count}) on this system",
            ],
            "network": [
                "cannot reach the internet from this server: network may be down",
                "i am getting connection refused to {host} on port {port}",
                "the network interface {iface} is down or unplugged",
            ],
            "dns": [
                "cannot resolve domain names: DNS is broken on this server",
                "dns resolver at {dns_server} is not responding: name resolution fails",
                "nslookup fails for all hosts: DNS configuration seems wrong",
            ],
            "git": [
                "cannot push code to {remote}: branch is behind remote by {n} commits",
                "git merge failed: there are conflicts in {file} that need resolution",
                "unable to clone repository {remote}: authentication failed",
            ],
            "package": [
                "cannot install package {pkg}: dpkg lock is held by another process",
                "apt update fails: repository {repo} returns 404 not found",
                "there are broken dependencies: package {pkg} requires {dep} but is not installed",
            ],
            "systemd": [
                "service {service} is not running: systemctl shows failed state",
                "cannot start {service}: the unit file has syntax errors",
                "systemctl daemon-reload fails: configuration files contain errors",
            ],
            "permission": [
                "access is denied to {path}: file permissions are too restrictive",
                "SELinux is blocking {process} from reading files in {path}",
                "i cannot chmod or chown files in {path}: operation not permitted",
            ],
        }

        for text in extra_variants.get(domain, []):
            found_slots = re.findall(r"\{(\w+)\}", text)
            for _ in range(3):
                filled = text
                for slot in found_slots:
                    if slot in slots:
                        filled = filled.replace(f"{{{slot}}}", random.choice(slots[slot]), 1)
                h = hashlib.md5(filled.encode()).hexdigest()
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    intent = random.choice(intents)
                    samples.append({
                        "text": filled,
                        "label": domain,
                        "intent": intent,
                    })

    return samples


def main():
    print("╔══════════════════════════════════════════════════╗")
    print("║  LINUX DOCTOR — SYNTHETIC DATASET GENERATOR     ║")
    print("╚══════════════════════════════════════════════════╝")

    samples = generate_samples()
    random.shuffle(samples)

    # Count per domain
    from collections import Counter
    counts = Counter(s["label"] for s in samples)

    print(f"\nGenerated {len(samples)} unique samples\n")
    for domain, count in sorted(counts.items()):
        bar = "█" * (count // 20)
        print(f"  {domain:15s} {count:5d}  {bar}")
    print(f"  {'─'*15} {'─'*5}  ")
    print(f"  {'TOTAL':15s} {len(samples):5d}")

    # Write to file (append mode)
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing_count = 0
    if DATA_PATH.exists():
        with open(DATA_PATH) as f:
            existing_count = sum(1 for _ in f)

    with open(DATA_PATH, "w") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")

    print(f"\n✓ Wrote {len(samples)} samples to {DATA_PATH}")
    print(f"  (was {existing_count} before)")
    print(f"  Total: {existing_count + len(samples)}")


if __name__ == "__main__":
    main()
