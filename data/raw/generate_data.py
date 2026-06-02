import json
import random
from pathlib import Path

OUTPUT_FILE = Path("linux_issues.jsonl")

# Cấu trúc: domain -> list of (templates, synonyms)
# {
#   "domain": [
#       ( ["template 1 {}", "template 2 {}"], [ ["syn1", "syn2"], ["val1", "val2"] ] )
#   ]
# }

TEMPLATES = {
    "docker": [
        (
            [
                "Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock",
                "Cannot connect to the Docker daemon at {}. Is the docker daemon running?",
                "docker: Got permission denied while trying to connect to the Docker daemon",
                "Error response from daemon: No such container: {}",
                "No space left on device when writing to docker overlay2",
                "docker container {} keeps restarting with exit code {}",
                "OOM killed docker container {}",
                "docker daemon not running after reboot",
                "failed to create network {}: network already exists",
                "docker pull fails connection timeout registry",
                "docker permission denied socket group",
                "cannot start docker service failed",
                "docker image pull rate limit exceeded",
                "container exit code 1 immediately after start",
                "docker build fails no space left device",
                "Failed to start docker container {}: address already in use",
                "docker-compose up fails with error: {}",
                "Cannot mount volume {} to container",
                "Docker build fails on step {}: return code {}",
            ],
            [
                ["unix:///var/run/docker.sock", "tcp://localhost:2375"],
                ["myapp", "nginx", "db", "redis", "web", "worker"],
                ["137", "1", "255", "128"],
                ["my-network", "bridge", "frontend"],
                ["permission denied", "timeout", "no space left"],
                ["/var/lib/mysql", "/data", "/app"],
                ["3", "4", "5", "10"],
            ]
        )
    ],
    "nginx": [
        (
            [
                "nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)",
                "nginx failed to start address already in use port 80",
                "nginx configuration test failed syntax error in {}",
                "502 bad gateway nginx upstream {} connection refused",
                "nginx 403 forbidden permission denied on webroot {}",
                "nginx ssl certificate problem {} expired",
                "nginx worker process exited with fatal error",
                "nginx cannot open config file {}: no such file or directory",
                "nginx upstream timed out sending request to upstream",
                "nginx too many open files ulimit",
                "nginx proxy_pass connection refused backend",
                "nginx 504 gateway timeout upstream",
                "nginx failed to bind to port 443 ssl",
                "nginx reverse proxy returns 502 bad gateway",
                "nginx rewrite rule not working location block",
                "nginx emerg SSL_CTX_use_PrivateKey_file failed",
                "nginx connect() to {} failed (111: Connection refused)",
                "nginx no live upstreams while connecting to upstream",
            ],
            [
                ["/etc/nginx/nginx.conf", "/etc/nginx/sites-enabled/default"],
                ["backend", "127.0.0.1:8080", "php-fpm"],
                ["/var/www/html", "/usr/share/nginx/html"],
                ["cert.pem", "fullchain.pem"],
                ["127.0.0.1:3000", "backend:8000"],
            ]
        )
    ],
    "ssh": [
        (
            [
                "ssh: connect to host {} port 22: Connection refused",
                "ssh permission denied (publickey,gssapi-keyex,gssapi-with-mic)",
                "ssh connection timeout host unreachable",
                "Warning: Remote host identification has changed REMOTE HOST IDENTIFICATION CHANGED",
                "ssh too many authentication failures for {}",
                "ssh could not resolve hostname {}: no address associated",
                "sshd service not running connection refused port 22",
                "ssh key {} permission denied 0644 should be 0600",
                "ssh connection drops after few seconds timeout",
                "ssh agent forwarding not working",
                "ssh banner exchange connection timeout",
                "ssh cannot connect firewall blocking port 22",
                "ssh handshake failed no matching cipher",
                "ssh multiplexing control path too long",
                "ssh X11 forwarding not working display variable",
                "ssh Connection closed by {} port 22",
                "ssh kex_exchange_identification: read: Connection reset by peer",
            ],
            [
                ["192.168.1.10", "10.0.0.5", "example.com", "server1"],
                ["root", "admin", "ubuntu", "ec2-user"],
                ["id_rsa", "id_ed25519", "key.pem"],
                ["192.168.1.10", "remotehost"],
            ]
        )
    ],
    "git": [
        (
            [
                "fatal: repository {} not found git push rejected",
                "git push rejected non-fast-forward update",
                "git merge conflict cannot merge unrelated histories",
                "fatal: unable to access {}: SSL certificate problem",
                "git clone permission denied publickey",
                "git commit nothing to commit working tree clean",
                "git pull error your local changes to {} would be overwritten",
                "git remote origin already exists",
                "git detached HEAD state at {}",
                "git LFS file {} too large push rejected",
                "error: failed to push some refs to {}",
                "fatal: refusing to merge unrelated histories",
                "git status shows untracked files",
            ],
            [
                ["https://github.com/repo.git", "origin"],
                ["https://github.com/repo.git", "gitlab"],
                ["main.py", "config.yml", "package.json"],
                ["main", "master", "v1.0"],
                ["large_file.bin", "dataset.csv"],
                ["origin", "upstream"],
            ]
        )
    ],
    "network": [
        (
            [
                "network is unreachable no route to host {}",
                "ping: connect: Network is unreachable",
                "curl connection refused port {}",
                "netstat ss port {} already in use address bind failed",
                "iptables firewall blocking connection port {}",
                "UFW firewall deny incoming port {} blocked",
                "network interface {} down not connected",
                "ip route default gateway missing no route",
                "tcp connection reset by peer broken pipe",
                "bandwidth throttling slow network latency high",
                "DHCP lease failed cannot get IP address on {}",
                "network timeout wget curl download fails",
                "VPN connection drops tunnel interface {} down",
                "nmap port scan shows filtered firewall",
                "traceroute to {} stops at gateway",
            ],
            [
                ["1.1.1.1", "192.168.1.1", "8.8.8.8"],
                ["8080", "80", "443", "3306"],
                ["80", "443", "8080"],
                ["80", "443", "22"],
                ["22", "80", "443"],
                ["eth0", "ens33", "wlan0"],
                ["eth0", "wlan0"],
                ["tun0", "wg0"],
                ["8.8.8.8", "google.com"],
            ]
        )
    ],
    "dns": [
        (
            [
                "dig nslookup domain {} cannot be resolved",
                "DNS resolution failed Name or service not known",
                "NXDOMAIN no such name dns lookup failure for {}",
                "resolv.conf nameserver {} wrong DNS not working",
                "systemd-resolved not running DNS failure",
                "DNS timeout SERVFAIL upstream resolver",
                "hostname {} cannot be resolved dig shows no answer",
                "DNS cache poisoning stale records",
                "hosts file override DNS not working etc hosts",
                "DNS propagation delay record not updated yet",
                "ping: {}: Name or service not known",
            ],
            [
                ["google.com", "example.com", "api.service.local"],
                ["example.com", "myhost"],
                ["8.8.8.8", "1.1.1.1", "127.0.0.53"],
                ["db.local", "worker1"],
                ["unknown-host.com", "myserver"],
            ]
        )
    ],
    "disk": [
        (
            [
                "No space left on device cannot write file to {}",
                "df -h shows 100% disk usage filesystem {} full",
                "read-only file system cannot create file in {}",
                "inode exhaustion no space left but df shows free on {}",
                "disk I/O error bad blocks hardware failure {}",
                "ext4 filesystem corruption fsck errors on {}",
                "disk quota exceeded user {} quota disk",
                "cannot write to /var/log log partition full",
                "LVM volume group {} no free space extend",
                "tmpfs /tmp is full cannot create temporary files",
                "mount: {}: wrong fs type, bad option, bad superblock",
            ],
            [
                ["/var/log", "/tmp", "/home"],
                ["/", "/var", "/data"],
                ["/", "/etc", "/boot"],
                ["/", "/var"],
                ["/dev/sda", "/dev/nvme0n1"],
                ["/dev/sda1", "/dev/mapper/vg-root"],
                ["www-data", "root", "user1"],
                ["vg0", "ubuntu-vg"],
                ["/dev/sdb1", "/mnt/data"],
            ]
        )
    ],
    "permission": [
        (
            [
                "permission denied cannot read file {} access denied",
                "chown chmod cannot change file {} ownership permission",
                "sudo operation not permitted user {} not in sudoers",
                "SELinux AVC denial permission denied context {}",
                "AppArmor blocking process {} access denied",
                "file {} is read-only cannot write permission denied",
                "setuid setgid bit missing permission escalation on {}",
                "umask wrong file created with wrong permissions",
                "bash: {}: Permission denied",
                "Cannot open {}: Permission denied",
            ],
            [
                ["/etc/shadow", "/var/log/syslog", "secret.key"],
                ["/var/www/html", "/home/user/.ssh"],
                ["ntbankey", "user1", "developer"],
                ["httpd_t", "mysqld_t"],
                ["/usr/sbin/mysqld", "/usr/sbin/nginx"],
                ["/etc/hosts", "/etc/fstab"],
                ["/usr/bin/passwd", "/usr/bin/sudo"],
                ["/root/script.sh", "./run.sh"],
                ["/var/run/docker.sock", "/var/log/auth.log"],
            ]
        )
    ],
    "memory": [
        (
            [
                "OOM killer killed process {} out of memory",
                "cannot allocate memory malloc failed",
                "swap space exhausted system thrashing",
                "free -h shows memory usage 99 percent",
                "memory leak process {} consuming too much RAM",
                "kernel out of memory oom score adj",
                "Out of memory: Killed process {} ({})",
                "Cannot fork: Cannot allocate memory",
                "java.lang.OutOfMemoryError: Java heap space",
            ],
            [
                ["java", "python", "mysql", "node"],
                ["chrome", "electron", "redis"],
                ["1234", "5678", "9999"],
                ["java", "mysqld", "php-fpm"],
            ]
        )
    ],
    "cpu": [
        (
            [
                "load average too high CPU overloaded {} {} {}",
                "process {} consuming 100 percent CPU top shows high usage",
                "CPU throttling thermal limit temperature high",
                "system too slow high load average",
                "htop shows all cores at 100 percent",
                "zombie process {} cannot kill defunct state",
                "CPU stuck for {}s! process {}",
                "Task {} blocked for more than 120 seconds",
            ],
            [
                ["10.5", "5.2"], ["8.1", "4.0"], ["15.2", "2.1"],
                ["ffmpeg", "crypto-miner", "python"],
                ["defunct-proc", "zombie-app"],
                ["22", "60"], ["worker-thread", "kworker"],
                ["mysqld", "docker"],
            ]
        )
    ],
    "systemd": [
        (
            [
                "systemctl start {} failed to start unit",
                "systemd service {} masked cannot enable",
                "unit file {} not found service does not exist",
                "systemd timeout starting service {} start timeout",
                "journalctl shows service {} crashed signal 11",
                "ExecStart failed permission denied binary {} not found",
                "Failed to restart {}: Unit not found",
                "Job for {} failed because the control process exited with error code.",
            ],
            [
                ["nginx.service", "docker.service", "sshd.service"],
                ["firewalld", "ufw"],
                ["mysqld.service", "custom.service"],
                ["mysql", "redis", "node-app"],
                ["nginx", "python-app"],
                ["/usr/local/bin/app", "/opt/start.sh"],
                ["apache2", "postgresql"],
                ["nginx.service", "docker.service"],
            ]
        )
    ],
    "package": [
        (
            [
                "apt get install {} package not found unable to locate",
                "dpkg dependency problems broken packages {}",
                "yum dnf repo error cannot find package {}",
                "pip install fails no matching distribution found for {}",
                "apt update failed could not resolve archive ubuntu",
                "package signature verification failed GPG error {}",
                "E: Unable to locate package {}",
                "npm ERR! code E404 not found {}",
            ],
            [
                ["nginx", "docker-ce", "htop"],
                ["libc6", "libssl1.1"],
                ["epel-release", "nginx"],
                ["tensorflow", "requests", "django"],
                ["NO_PUBKEY 12345678", "invalid signature"],
                ["python3-pip", "curl"],
                ["express", "react"],
            ]
        )
    ],
}

def generate_samples(num_per_class=100):
    dataset = []
    
    for label, variations in TEMPLATES.items():
        for templates, fillers_lists in variations:
            count = 0
            while count < num_per_class:
                tmpl = random.choice(templates)
                num_blanks = tmpl.count("{}")
                
                # Pick random fillers if template has {}
                chosen_fillers = []
                for i in range(num_blanks):
                    if i < len(fillers_lists):
                        chosen_fillers.append(random.choice(fillers_lists[i]))
                    else:
                        chosen_fillers.append(random.choice(fillers_lists[0]))
                
                filled_tmpl = tmpl.format(*chosen_fillers)
                dataset.append({"text": filled_tmpl, "label": label})
                count += 1
                
    return dataset

if __name__ == "__main__":
    random.seed(42)
    # Tăng lên 500 samples mỗi category (12 class x 500 = 6000 samples)
    samples = generate_samples(500) 
    
    with open(OUTPUT_FILE, "w") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")
            
    print(f"Generated {len(samples)} samples to {OUTPUT_FILE}")
