#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${BOLD}${CYAN}  🐧 Linux Doctor — Test Suite${NC}"
echo -e "${BOLD}${CYAN}  12 domains · 12 queries${NC}"
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════${NC}"
echo ""

TESTS=(
    "docker:docker container failed to start"
    "nginx:nginx 502 bad gateway"
    "ssh:ssh connection refused"
    "disk:disk space full on /var log"
    "memory:out of memory oom killer"
    "cpu:cpu load too high system slow"
    "network:network unreachable cannot ping gateway"
    "dns:dns resolution failed nslookup"
    "git:git push rejected merge conflict"
    "systemd:systemd service failed to start unit"
    "permission:permission denied cannot access file"
    "package:apt update failed dependency broken"
)

PASS=0
FAIL=0
TOTAL=${#TESTS[@]}

for i in "${!TESTS[@]}"; do
    IFS=':' read -r domain query <<< "${TESTS[$i]}"
    n=$((i + 1))

    echo -e "${BOLD}[${n}/${TOTAL}] ${YELLOW}${domain}${NC}"
    echo -e "${DIM}  Query: ${query}${NC}"

    if output=$(uv run python -m linux_doctor.cli.app "${query}" 2>&1); then
        echo -e "${GREEN}  ✅ OK${NC}"

        # Check if it identified the right domain
        if echo "$output" | grep -qi "Domain:.*${domain}"; then
            echo -e "${GREEN}  ✓ Correct domain detected${NC}"
        else
            echo -e "${YELLOW}  ⚠ Domain might differ${NC}"
        fi

        # Check if it found a root cause
        if echo "$output" | grep -qi "root cause"; then
            echo -e "${GREEN}  ✓ Root cause found${NC}"
        else
            echo -e "${RED}  ✗ No root cause${NC}"
        fi

        PASS=$((PASS + 1))
    else
        echo -e "${RED}  ❌ FAILED (exit code: $?)${NC}"
        FAIL=$((FAIL + 1))
    fi

    echo ""
done

echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${BOLD}Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}, ${TOTAL} total"
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════${NC}"
