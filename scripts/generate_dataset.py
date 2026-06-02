"""
Linux Doctor — Synthetic Dataset Generator (Enhanced)

Generates 100k+ high-quality labeled training samples across all 12 domains.
Features multi-language support (English + Vietnamese), natural language queries,
combinatorial template expansion, and balanced class distribution.

Output: data/raw/linux_issues.jsonl (deduplicated)
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path
from collections import Counter

DATA_PATH = Path("data/raw/linux_issues.jsonl")
SEED = 42
random.seed(SEED)

DomainConfig = dict


def _expand_slots(slots: dict[str, list[str]], target: int = 25) -> dict[str, list[str]]:
    """Expand slot value lists to ensure enough combinatorial diversity."""
    expanded = {}
    for key, values in slots.items():
        if len(values) >= target:
            expanded[key] = values
            continue

        if key in ("host", "dns_server", "ip", "gateway", "registry"):
            patterns = ["server", "host", "node", "worker", "master", "proxy", "internal", "prod", "staging", "dev"]
            base = values[:]
            for p in patterns:
                if len(base) >= target:
                    break
                extended = [f"{v}-{p}" for v in values[:3] for p in patterns[:3]]
                base.extend(extended)
            expanded[key] = base[:target]

        elif key in ("port",):
            expanded[key] = values + [str(p) for p in range(3000, 3100) if str(p) not in values][:target-len(values)]

        elif key in ("pid", "timeout", "line"):
            expanded[key] = values[:]
            start = max([int(v) for v in values if v.isdigit()] or [100]) + 1
            for i in range(target - len(values)):
                expanded[key].append(str(start + i * 7))

        elif key in ("pct", "pct_i", "pct_mem"):
            expanded[key] = values + [str(v) for v in range(50, 100) if str(v) not in values][:target-len(values)]

        elif key in ("file", "config_file", "cert_path", "log_path", "webroot"):
            expanded[key] = values[:]
            suffixes = [".backup", ".new", ".old", ".1", ".2", "test", "dev"]
            for v in list(expanded[key]):
                for s in suffixes:
                    if len(expanded[key]) >= target:
                        break
                    expanded[key].append(f"{v}{s}")

        else:
            expanded[key] = values[:]
            if len(values) >= 5:
                prefixes = ["alt", "extra", "new", "sec", "tmp", "old", "backup", "v2", "v3", "v4"]
                for v in list(values):
                    for p in prefixes:
                        if len(expanded[key]) >= target:
                            break
                        expanded[key].append(f"{p}-{v}")
            else:
                expanded[key] = values + [f"value_{i}" for i in range(target)][:target]

        while len(expanded[key]) < target:
            expanded[key].append(values[0])

    return expanded

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
            # Natural language
            "docker container keeps dying with exit code {code} what should I check",
            "why does docker say permission denied on {socket} after install",
            "my docker build fails saying no space left on {docker_dir}",
            "docker container {container} exits immediately what is wrong",
            "how to fix docker daemon not starting after reboot on ubuntu",
            "docker pull very slow from {registry} connection keeps timing out",
            "docker volume mount fails with permission denied to {path}",
            # Vietnamese
            "docker bi loi khong ket noi duoc den socket {socket}",
            "docker container {container} bi kill voi exit code {code}",
            "docker build bi loi: khong du dung luong o {docker_dir}",
            "docker bi tu choi quyen truy cap {socket}",
            "khong the khoi dong docker duoc: socket {socket} loi",
            "docker container {container} lien tuc restart khong hieu tai sao",
            "docker pull {image} tu {registry} bi timeout",
            "loi docker: khong the tao network {net}",
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
            # Natural language
            "nginx returning 502 bad gateway for all requests to {upstream}",
            "my nginx server returns 502 bad gateway for requests to {upstream}",
            "why does nginx fail to start with bind error on port {port}",
            "how to fix nginx 403 forbidden on webroot {webroot}",
            "nginx configuration file {config_file} has a syntax error after edit",
            "after reboot nginx is not running and fails to start",
            "how do I check why nginx returns 502 for the backend {upstream}",
            "nginx is running but returns empty response from {upstream}",
            # Vietnamese
            "nginx bi loi 502: upstream {upstream} tu choi ket noi",
            "nginx tra ve 403 forbidden cho static file tai {webroot}",
            "tai sao nginx bao SSL certificate {cert_path} khong hop le",
            "nginx configuration {config_file} bi loi syntax sau khi sua",
            "nginx khong the start vi port {port} da duoc su dung",
            "nginx bi timeout khi goi len {upstream}: check lai backend",
            "lam sao de fix loi nginx 504 gateway timeout",
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
            # Natural language
            "cannot ssh into {host} on port {port} connection refused what is wrong",
            "why am i getting permission denied when trying to ssh to {host}",
            "ssh connection to {host} keeps timing out after {timeout} seconds",
            "how to fix ssh host key verification failed for {host}",
            "ssh to {host} works but disconnects after {timeout} seconds",
            "my ssh key {key_path} is not working authentication failed for user {user}",
            "how do i fix ssh too many authentication failures error on {host}",
            "ssh into {host} is very slow: long delay before password prompt",
            # Vietnamese
            "ssh vao {host} bi loi connection refused port {port}",
            "ssh bi tu choi dang nhap: permission denied voi key {key_path}",
            "ssh den {host} bi timeout sau {timeout} giay",
            "loi ssh: host key cua {host} da bi thay doi warnings",
            "khong the ssh duoc vao {host}: network khong the ket noi",
            "tai sao ssh bi bao permission denied khi dung key {key_path}",
            "ssh connection bi ngat sau vai phut ket noi voi {host}",
            "lam sao de fix loi ssh connection refused port {port}",
        ],
        "slots": {
            "host": ["192.168.1.10", "10.0.0.5", "example.com", "gitlab.com", "github.com", "server.example.org", "172.16.0.100", "ec2-54-123-45-67.compute-1.amazonaws.com", "10.10.1.50", "192.168.100.200"],
            "port": ["22", "2222", "222", "22222", "8022", "22222"],
            "timeout": ["10", "30", "60", "120", "15", "5", "45"],
            "user": ["root", "ubuntu", "admin", "deploy", "git", "ec2-user", "centos", "ntbankey", "developer", "ansible"],
            "key_path": ["~/.ssh/id_rsa", "~/.ssh/id_ed25519", "~/.ssh/id_ecdsa", "/home/user/.ssh/id_rsa", "/home/user/.ssh/authorized_keys"],
            "firewall": ["UFW", "iptables", "firewalld", "nftables", "AWS security group"],
            "cipher": ["aes256-cbc", "aes128-ctr", "3des-cbc", "chacha20-poly1305"],
            "home": ["/home/ubuntu", "/root", "/home/user"],
            "perms": ["0644", "0777", "0755", "0666"],
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
            # Natural language
            "my disk is full on {mount}: cannot write any more files",
            "why is my disk showing {pct}% usage what is taking up space",
            "how to free up disk space on {mount} partition",
            "disk keeps running out of space even after cleaning files",
            "i get no space left on device error when writing to {path}",
            "how to check what is filling up disk on {mount}",
            "drive {device} has too many bad sectors should I replace it",
            "partition {mount} is almost full at {pct}% what should I do",
            # Vietnamese
            "o dia {mount} bi day: khong the ghi them file nao",
            "o dia {device} bi loi I/O: khong the doc duoc du lieu",
            "phan vung {mount} da dung {pct}% can gian phong",
            "khong the mount {device}: filesystem bi loi hoac superblock hong",
            "tai sao o dia lai bi day ma van con trong luong: inode het",
            "o cung {device} bi loi SMART: can thay the on cung moi",
            "khong con dung luong trong o dia de ghi file tai {path}",
            "lam sao de giai phong dung luong o dia {mount} tren linux",

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
            # Natural language
            "system keeps running out of memory and killing processes",
            "why does my server run out of memory after running for {time} hours",
            "how to check memory usage and see what process is using RAM",
            "my application {process} keeps getting killed by OOM killer what to do",
            "server memory usage at {pct}% what is normal and how to reduce",
            "swap usage is very high at {used_swap}MB is this normal",
            "how to diagnose memory leak in {process} on production server",
            "why is memory usage not going down after stopping {process}",
            # Vietnamese
            "he thong het bo nho: tien trinh {process} bi OOM kill",
            "RAM da dung {pct}% tren tong {total_gb}GB: can kiem tra lai",
            "swap da day: {used_swap}MB da dung tren {total_swap}MB",
            "tai sao may chu lien tuc het bo nho khi chay {process}",
            "tien trinh {process} dung {rss}MB bo nho: co the bi memory leak",
            "khong the cap phat them bo nho: malloc failed cho {process}",
            "lam sao de kiem tra bo nho va tim process dung nhieu RAM nhat",
            "loi out of memory: {process} bi kill vi vuot qua gioi han",

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
            # Natural language
            "server is very slow: load average {load_1} is too high on {cores} cores",
            "a process is stuck at {pct}% CPU and needs to be killed",
            "there are too many zombies ({count}) on this system",
            "why is my CPU usage at 100% all the time what process is causing it",
            "how to reduce CPU load on server with {cores} cores",
            "process {process} using too much CPU after recent update what to do",
            "system load is {load_1} which is very high for this machine",
            "how to find and kill runaway process on linux server",
            # Vietnamese
            "CPU dang dung {pct}% tren {cores} core: may rat cham",
            "tien trinh {process} dung {pct}% CPU co the bi runaway",
            "tai sao CPU load lai cao {load_1} khi may chi co {cores} core",
            "co {count} tien trinh zombie trong he thong can cleanup",
            "CPU bi throttle vi nhiet do {temp}C qua cao",
            "lam sao de tim process dung nhieu CPU nhat tren he thong",
            "server bi cham vi CPU load {load_1} qua cao",
            "tien trinh {process} bi stuck o trang thai D khong kill duoc",

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
            # Natural language
            "cannot reach the internet from this server: network may be down",
            "i am getting connection refused to {host} on port {port}",
            "the network interface {iface} is down or unplugged",
            "how to check why i cannot connect to {host} on port {port}",
            "network is slow to {host}: latency {latency}ms is too high",
            "why is my server losing {loss}% packets to {host}",
            "check network connectivity: cannot ping {host}",
            "how to open port {port} on ufw or iptables",
            # Vietnamese
            "khong the ket noi toi {host} port {port}: connection refused",
            "mang bi mat ket noi: interface {iface} down khong co carrier",
            "ping toi {host} bi timeout: kiem tra lai firewall",
            "tai sao may chu khong the ket noi internet duoc",
            "port {port} dang bi chan boi UFW hoac iptables",
            "ket noi mang den {host} bi cham: ping {latency}ms",
            "mat {loss}% packet khi ping den {host}",
            "lam sao de mo port {port} tren iptables hoac ufw",

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
            # Extra DNS templates
            "DNS server {dns_server} not resolving {host}: query refused",
            "dig @{dns_server} {host}: connection timed out",
            "nslookup: can't resolve {host}: server failure",
            "host {host} not found: authoritive answer not found",
            "DNS query for {host} returned no answers from {dns_server}",
            "Unable to resolve {host}: all DNS servers failed",
            "resolvconf: /etc/resolv.conf contains invalid entry {dns_server}",
            "NetworkManager DNS: failed to update resolv.conf for {dns_server}",
            "systemd-resolved query failed for {host}: DNSSEC validation failed",
            "DNS resolution for {host} slow: {dns_server} took 5s to respond",
            "wget {host}: Resolving {host} failed: temporary failure",
            "curl --dns-servers {dns_server} {host}: no such host",
            "Python urllib: Name or service not known for {host}",
            "Node.js dns.lookup({host}): getaddrinfo ENOTFOUND",
            "Java UnknownHostException: {host}: name resolution failed",
            "apt update fails: Could not resolve 'archive.ubuntu.com' for repository",
            "pip install fails: Could not find a version that satisfies from {host}",
            "docker pull {host}/image: unable to resolve repository name",
            "how to flush dns cache on systemd-resolved ubuntu 22.04",
            "DNS broken after installing vpn: /etc/resolv.conf points to wrong dns",
            "Cannot resolve internal hostnames {host} on corporate network",
            "After updating /etc/resolv.conf DNS still fails for {host}",
            "DNS query redirected: {host} resolves to wrong IP {wrong_ip}",
            "Checking DNS: ping {host} returns unknown host intermittently",
            "Kubernetes pod DNS failure: cannot resolve service name {host}",
            "kubectl exec fails: unable to resolve cluster internal DNS for {host}",
            # Natural language
            "cannot resolve domain names: DNS is broken on this server",
            "dns resolver at {dns_server} is not responding: name resolution fails",
            "nslookup fails for all hosts: DNS configuration seems wrong",
            "why is my server not resolving dns for {host}",
            "how to fix temporary failure in name resolution on ubuntu",
            "DNS not working after changing /etc/resolv.conf to {dns_server}",
            "intermittent DNS failures for {host} only some requests work",
            "check DNS configuration: dig shows NXDOMAIN for valid host {host}",
            # Vietnamese
            "DNS khong phan giai duoc hostname {host}",
            "DNS server {dns_server} khong tra loi: mat ket noi",
            "khong the phan giai ten mien: /etc/resolv.conf bi sai",
            "taisao khong vao duoc {host}: DNS co van de",
            "systemd-resolved khong chay: DNS bi loi",
            "dig {host} bao NXDOMAIN: domain khong ton tai hoac DNS sai",
            "lam sao de fix loi DNS temporary failure in name resolution",
            "sau khi thay doi DNS sang {dns_server} thi khong vao duoc mang",

        ],
        "slots": {
            "host": ["google.com", "github.com", "api.example.com", "mail.company.org", "registry.npmjs.org", "pypi.org", "myapp.internal", "docker.io", "storage.googleapis.com", "auth.example.com", "cdn.cloudflare.com"],
            "dns_server": ["8.8.8.8", "1.1.1.1", "9.9.9.9", "208.67.222.222", "192.168.1.1", "10.0.0.53", "127.0.0.53", "8.8.4.4"],
            "wrong_ip": ["127.0.0.1", "0.0.0.0", "192.168.1.5", "10.0.0.2", "::1"],
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
            # Natural language
            "cannot push code to {remote}: branch is behind remote by {n} commits",
            "git merge failed: there are conflicts in {file} that need resolution",
            "unable to clone repository {remote}: authentication failed",
            "how to fix git merge conflict in {file} when two people edited it",
            "why am i getting permission denied when pushing to {remote}",
            "how to recover from detached head state in git",
            "git push rejected not fast forward how to fix",
            "how to resolve conflicts in {file} during git rebase",
            "git authentication failed for {remote} after changing password",
            # Vietnamese
            "khong the push code len {remote}: branch bi tu choi non-fast-forward",
            "git merge bi conflict o file {file}: can giai quyet conflict",
            "khong the clone {remote}: bi loi authentication",
            "khong the pull code tu {remote}: co xung dot trong {file}",
            "git bi loi permission denied khi push to {host}",
            "lam sao de fix loi merge conflict trong git",
            "git push bi tu choi: can pull truoc khi push",
            "git bi loi fatal: repository {remote} khong tim thay",

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
            # Natural language
            "cannot install package {pkg}: dpkg lock is held by another process",
            "apt update fails: repository {repo} returns 404 not found",
            "there are broken dependencies: package {pkg} requires {dep} but is not installed",
            "how to fix dpkg interrupted error during package installation",
            "why does pip say no matching distribution for {pkg}",
            "gpg key error when running apt update for {repo}",
            "cannot install {pkg} via yum: dependency resolution failed",
            "how to fix broken packages in ubuntu when installing {pkg}",
            "yum install {pkg}: GPG key import failed for repository {repo}",
            # Vietnamese
            "khong the cai dat goi {pkg}: dpkg lock dang bi giu boi tien trinh khac",
            "apt update bi loi: repository {repo} tra ve 404",
            "goi {pkg} khong the cai dat vi thieu dependency {dep}",
            "loi GPG key khi apt update tu {repo}",
            "pip install {pkg} bi loi khong tim thay phien ban phu hop",
            "lam sao de fix loi broken packages tren ubuntu",
            "dnf update that bai: co conflict file giua {pkg1} va {pkg2}",
            "tai sao khong the cai dat {pkg}: package not found",

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
            # Natural language
            "service {service} is not running: systemctl shows failed state",
            "cannot start {service}: the unit file has syntax errors",
            "systemctl daemon-reload fails: configuration files contain errors",
            "why does {service} keep failing to start after boot",
            "how to enable and start {service} on boot in linux",
            "systemd service {service} times out when trying to start",
            "check why {service} failed: journalctl shows exit code {code}",
            "systemctl status shows {service} in failed state how to debug",
            # Vietnamese
            "service {service} khong chay: systemctl status bao failed",
            "khong the start {service}: unit file {unit} bi loi syntax",
            "tai sao {service} lien tuc failed khi reboot",
            "lam sao de enable {service} de chay khi boot",
            "{service} bi timeout khi start: can tang TimeoutStartSec",
            "journalctl cho {service} thay tien trinh bi crash voi signal {signal}",
            "systemd: khong the reload daemon vi loi cau hinh",
            "service {service} bi masked khong the start duoc",

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
            # Natural language
            "access is denied to {path}: file permissions are too restrictive",
            "SELinux is blocking {process} from reading files in {path}",
            "i cannot chmod or chown files in {path}: operation not permitted",
            "why am i getting permission denied when accessing {path}",
            "how to fix selinux blocking {process} from writing to {path}",
            "sudo not working: user is not in sudoers file",
            "how to change permissions on {path} to {expected_perms}",
            "apparmor is blocking {process} from executing files in {mount}",
            # Vietnamese
            "bi tu choi quyen truy cap file {path}: permission denied",
            "khong the doc file {path}: permission denied can kiem tra lai",
            "SELinux dang chan {process} truy cap {path}",
            "khong the chmod file {path}: operation not permitted",
            "sudo khong hoat dong: user {user} khong co trong sudoers",
            "tai sao bi permission denied khi truy cap {path}",
            "lam sao de fix SELinux blocking process doc file",
            "file {path} co permission {perms} sai can chinh ve {expected_perms}",

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


def _infer_intent(text: str, domain: str) -> str | None:
    t = text.lower()
    R = re.IGNORECASE

    # ── docker ──────────────────────────────────────────────
    if domain == "docker":
        if "permission" in t:
            return "permission_denied"
        if re.search(r"no space|insufficient.*(space|storage)|out of space|docker_dir|storage", t):
            return "resource_exhaustion"
        if re.search(r"OOM|out of memory|memory.*limit|memory max|allocate.*mem|code 137|killed", t, R):
            return "resource_exhaustion"
        if re.search(r"restart|crash|exit.*code|CrashLoop|keep.*dying|not running|failed to start|daemon not running", t):
            return "service_failure"
        if re.search(r"build.*fail|COPY failed|not found locally", t, R):
            return "build_failure"
        if re.search(r"network.*(fail|exist|not found)|bridge|connection timeout|port.*allocated|unauthorized|request canceled", t):
            return "network_error"
        if re.search(r"(cannot )?connect|cannot pull|daemon.*(not )?(responding|running)|no such (container|image)|not found|no containers", t):
            return "connection_failure"
        return "config_error"

    # ── nginx ───────────────────────────────────────────────
    if domain == "nginx":
        if re.search(r"SSL|certificate", t, R):
            return "ssl_error"
        if "permission denied" in t or "forbidden" in t or "cannot access" in t:
            return "permission_denied"
        if re.search(r"upstream|502|504|bad gateway|gateway timeout|no live upstreams", t):
            return "upstream_error"
        if re.search(r"too many open|open file limit|ulimit|shmtx|no space", t):
            return "resource_exhaustion"
        if re.search(r"bind|address already in use|port.*in use", t):
            return "service_failure"
        if re.search(r"not (installed|found)|binary missing|command not found|package.*not found|no unit file", t):
            return "service_failure"
        if re.search(r"(fail|crash|not running|signal|worker.*exit|cannot start|startup|start.*fail|start.*error)", t):
            return "service_failure"
        if re.search(r"syntax error|directive|configuration.*test|test failed|reload.*fail|duplicate|conflicting|rewrite|try_files|invalid number|unexpected end", t):
            return "config_error"
        if re.search(r"location.*404|client.*too large|invalid value", t):
            return "config_error"
        return "config_error"

    # ── ssh ─────────────────────────────────────────────────
    if domain == "ssh":
        if "host key" in t and ("verification" in t or "changed" in t or "fail" in t):
            return "host_key_mismatch"
        if re.search(r"permission denied|publickey|authentication fail|not authorized|too many authentication", t):
            return "authentication_failure"
        if re.search(r"timed out|timeout", t):
            return "timeout"
        if "blocked by firewall" in t or "firewall" in t:
            return "firewall_block"
        if re.search(r"bad permissions|invalid format|load_public|bad configuration|no matching", t):
            return "config_error"
        if re.search(r"Connection refused|No route|Could not resolve|Network is unreachable|not running|Broken pipe|closed by remote|Connection reset|banner exchange", t, R):
            return "connection_failure"
        return "connection_failure"

    # ── disk ────────────────────────────────────────────────
    if domain == "disk":
        if re.search(r"I/O error|Input/output|Buffer I/O|smartctl.*(FAIL|health)|bad sectors|bi loi I/O", t, R):
            return "io_error"
        if re.search(r"superblock|fsck|corruption|corrupt|journal.*abort|xfs_repair|BTRFS.*error|DEGRADED|FAULTED|remounted read-only", t, R):
            return "filesystem_corruption"
        if re.search(r"mount.*not mounted|wrong fs type|cannot be mounted|mount point.*not exist|cannot mount|device not found", t):
            return "mount_failure"
        if re.search(r"No space|full|quota|inode.*(exhaust|full)|running out|ENOSPC|LVM.*free|no free space|tmpfs.*full|out of space", t, R):
            return "resource_exhaustion"
        if re.search(r"read-only.*(cannot|create|write)|read-only file", t):
            return "io_error"
        return "resource_exhaustion"

    # ── memory ──────────────────────────────────────────────
    if domain == "memory":
        if re.search(r"OOM.*kill|Killed process|oom-killer|exit code 137|killed.*OOM|cgroup.*OOM|was killed by OOM", t, R):
            return "oom_kill"
        if "swap" in t:
            return "swap_exhaustion"
        if re.search(r"(memory|mem).*leak|possible leak|RSS.*leak|abnormal.*memory", t, R):
            return "memory_leak"
        if re.search(r"cannot allocate|malloc failed|mmap failed|failed to allocate|out of memory in|Java heap|heap out of memory|out of memory for query|signal 6|got signal.*6|het bo nho", t):
            return "resource_exhaustion"
        if re.search(r"memory.*(usage|pressure|available|used)|page allocation|zone.*low|memory exhausted|available out of|usage at.*%|free -m shows", t, R):
            return "memory_pressure"
        return "resource_exhaustion"

    # ── cpu ─────────────────────────────────────────────────
    if domain == "cpu":
        if "zombie" in t or "defunct" in t:
            return "zombie_process"
        if "runaway" in t or "stuck at" in t or "infinite loop" in t:
            return "runaway_process"
        if "steal" in t:
            return "cpu_steal"
        if re.search(r"D state|uninterruptible sleep|hung task|IO wait|CPU starvation|throttled", t, R):
            return "resource_exhaustion"
        if re.search(r"load average|overloaded|(context|interrupt).*(switch|storm)|thermal|CPU temperature|htop shows|frequency reduced", t, R):
            return "high_usage"
        return "high_usage"

    # ── network ─────────────────────────────────────────────
    if domain == "network":
        if re.search(r"DOWN|no carrier|no link|Link detected.*no|cable disconnected|unplugged|no default gateway|DHCP|STP blocking|no packets|interface.*down", t, R):
            return "interface_down"
        if re.search(r"iptables|DROP policy|UFW.*deny|port not open|firewall.*block", t, R):
            return "firewall_block"
        if "dns" in t or "resolve host" in t:
            return "dns_failure"
        if "latency" in t or "packet loss" in t or "bandwidth" in t:
            return "latency"
        if "address already in use" in t:
            return "port_conflict"
        if re.search(r"unreachable|Connection refused|Failed to connect|Connection timed out|timed out|broken pipe|Connection reset|gateway.*unreachable|ARP|cannot (ping|reach)", t, R):
            return "connection_failure"
        return "connection_failure"

    # ── dns ─────────────────────────────────────────────────
    if domain == "dns":
        if "DNSSEC" in t or "dnssec" in t:
            return "dnssec_failure"
        if re.search(r"connection timed out|not responding|SERVFAIL|query refused|server failure|took.*5s|connection timed out", t):
            return "server_timeout"
        if re.search(r"resolv\.conf|resolvectl|nsswitch|invalid nameserver|no DNS server|systemd-resolved.*not run|wrong IP|stale (entry|cache)|TLS handshake|hosts file entry|getent hosts|cache.*flush|cache.*stale", t, R):
            return "config_error"
        if re.search(r"NXDOMAIN|Name or service|Temporary failure|cannot resolve|Could not resolve|no such name|no answers|unable to resolve|intermittent|UnknownHostException|ENOTFOUND|getaddrinfo|curl.*Could not resolve", t, R):
            return "resolution_failure"
        if "ping.*fail" in t or "dig.*fail" in t or "nslookup.*fail" in t:
            return "resolution_failure"
        return "resolution_failure"

    # ── git ─────────────────────────────────────────────────
    if domain == "git":
        if "LFS" in t or "too large" in t:
            return "lfs_error"
        if re.search(r"conflict|CONFLICT|unrelated histories|diverged|cherry-pick.*conflict|conflicts in", t):
            return "merge_conflict"
        if re.search(r"rejected|non-fast-forward|failed to push|protected branch|updates were rejected|behind.*commit", t):
            return "push_failure"
        if re.search(r"Permission denied|Authentication fail|Could not read from remote|access rights|not authorized", t, R):
            return "auth_failure"
        if re.search(r"not found|bad object|corruption|corrupt|sha1 mismatch|fsck.*corruption|is a blob|repository.*not found", t):
            return "repository_corruption"
        if "not a git repository" in t or "detached HEAD" in t or "no tracking" in t or "no upstream" in t:
            return "config_error"
        return "push_failure"

    # ── package ─────────────────────────────────────────────
    if domain == "package":
        if re.search(r"lock.*dpkg|Unable to lock|dpkg.*interrupted", t, R):
            return "lock_conflict"
        if "gpg" in t or "signature" in t or "public key" in t:
            return "gpg_error"
        if re.search(r"unmet depend|depends on|requires.*but|not.*install|dependency problem|failed dependenc", t):
            return "dependency_error"
        if re.search(r"404.*not found|failed to fetch|hash sum mismatch|no release file|no more mirrors|failed to download", t):
            return "repo_error"
        if re.search(r"transaction check|conflicting files|conflicts between|file.*conflict", t):
            return "update_failure"
        if re.search(r"unable to locate|not available|error code.*dpkg|sub-process|snap not found|no matching distribution|could not find.*version|cannot install|package not found|error processing", t):
            return "installation_failure"
        return "installation_failure"

    # ── systemd ─────────────────────────────────────────────
    if domain == "systemd":
        if "masked" in t:
            return "masked_service"
        if "dependency" in t and "fail" in t:
            return "dependency_error"
        if "timed out" in t or "timeout" in t:
            return "timeout"
        if "syntax error" in t or "reload daemon" in t or "Invalid argument" in t or "File exists" in t:
            return "config_error"
        if "journal" in t and ("corrupt" in t or "error" in t or "FAIL" in t or "rotating" in t):
            return "journal_error"
        if re.search(r"failed.*exit-code|failed state|control process|inactive \(dead\)|crash.*signal|Unit not found|start-limit|exceed.*limit|OOM killed|create (drop-in|symlink)|not running|khong chay|bi timeout|enter.*failed", t):
            return "service_failure"
        return "service_failure"

    # ── permission ──────────────────────────────────────────
    if domain == "permission":
        if re.search(r"SELinux|AVC denial|ausearch.*avc|getenforce.*Enforcing|AppArmor", t, R):
            return "selinux_block"
        if "cannot execute" in t or "exec format" in t or "noexec" in t:
            return "execution_denied"
        if re.search(r"chown|changing ownership|wrong owner|chmod.*perm|setuid.*missing|Operation not permitted", t):
            return "ownership_error"
        if "sudo" in t:
            return "sudo_error"
        if "key permissions" in t or "publickey" in t:
            return "ssh_key_perms"
        if "cannot open" in t or "permission denied" in t or "acl check" in t:
            return "file_access_denied"
        return "file_access_denied"

    return None


def _paraphrase(text: str) -> list[str]:
    """Generate natural paraphrased variants of a diagnostic message."""
    variants = [text]
    lower = text.lower()

    if len(text) < 80 and not text.startswith("Why") and not text.startswith("How"):
        if lower.startswith("cannot") or lower.startswith("no space") or lower.startswith("failed"):
            variants.append(f"How to fix: {text}")

    if not text.startswith("Error:") and not text.startswith("ERROR:"):
        if "error" not in lower and "failed" not in lower:
            variants.append(f"Error: {text}")

    if len(text) < 80:
        variants.append(f"Need help: {text[0].lower() + text[1:]}")
    if not text.startswith("Why") and not text.startswith("How") and len(text) > 20:
        variants.append(f"Help me fix: {text}")

    return list(set(variants))


def generate_samples(target_per_class: int = 8500) -> list[dict]:
    """Generate high-quality samples using combinatorial template expansion."""
    samples = []
    seen_hashes = set()
    max_attempts_per_domain = target_per_class * 10

    for domain, config in DOMAINS.items():
        templates = config["templates"]
        slots = _expand_slots(config["slots"])
        intents = config["intents"]
        generated = 0
        attempts = 0

        # Phase 1: generate from templates with slot filling
        while generated < target_per_class and attempts < max_attempts_per_domain:
            template = random.choice(templates)
            found_slots = re.findall(r"\{(\w+)\}", template)

            if not found_slots:
                h = hashlib.md5(template.encode()).hexdigest()
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    samples.append({
                        "text": template,
                        "label": domain,
                        "intent": _infer_intent(template, domain) or random.choice(intents),
                    })
                    generated += 1
                attempts += 1
                continue

            filled = template
            skip = False
            for slot in found_slots:
                if slot in slots:
                    filled = filled.replace(f"{{{slot}}}", random.choice(slots[slot]), 1)
                else:
                    skip = True
                    break

            if skip:
                attempts += 1
                continue

            h = hashlib.md5(filled.encode()).hexdigest()
            if h not in seen_hashes:
                seen_hashes.add(h)
                samples.append({
                    "text": filled,
                    "label": domain,
                    "intent": _infer_intent(filled, domain) or random.choice(intents),
                })
                generated += 1

                # Generate paraphrased variants (max 2 per filled template)
                if generated < target_per_class * 0.9:
                    for pv in _paraphrase(filled)[:2]:
                        ph = hashlib.md5(pv.encode()).hexdigest()
                        if ph not in seen_hashes:
                            seen_hashes.add(ph)
                            samples.append({
                                "text": pv,
                                "label": domain,
                                "intent": _infer_intent(pv, domain) or random.choice(intents),
                            })
                            generated += 1
                            if generated >= target_per_class:
                                break
            attempts += 1

        print(f"  {domain:15s} {generated:5d} samples")

    return samples


def main():
    print("╔══════════════════════════════════════════════════╗")
    print("║  LINUX DOCTOR — 100K DATASET GENERATOR          ║")
    print("╚══════════════════════════════════════════════════╝")

    print(f"\nGenerating ~100,000 samples (balanced across {len(DOMAINS)} domains)...\n")

    samples = generate_samples(target_per_class=8500)
    random.shuffle(samples)

    counts = Counter(s["label"] for s in samples)
    total = len(samples)

    print(f"\n{'─'*50}")
    print(f"{'Domain':15s} {'Count':>8s} {'%':>6s} {'Distribution'}")
    print(f"{'─'*50}")
    for domain in sorted(counts):
        pct = counts[domain] / total * 100
        bar_len = max(1, int(counts[domain] / (total / 50)))
        bar = "█" * bar_len
        print(f"  {domain:15s} {counts[domain]:>6d} {pct:>5.1f}% {bar}")
    print(f"{'─'*50}")
    print(f"  {'TOTAL':15s} {total:>6d} {'100%':>6s}")

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(DATA_PATH, "w") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"\n✓ Wrote {total} samples to {DATA_PATH}")
    print(f"  File size: {DATA_PATH.stat().st_size / 1024 / 1024:.1f} MB")

    min_count = min(counts.values())
    max_count = max(counts.values())
    imbalance = max_count - min_count
    print(f"  Min class: {min_count} | Max class: {max_count} | Spread: {imbalance}")
    print(f"  Imbalance ratio: {max_count/min_count:.2f}x")


if __name__ == "__main__":
    main()
