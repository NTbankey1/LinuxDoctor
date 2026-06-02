"""Text preprocessing pipeline for Linux issue classification."""

import re

# English stopwords (minimal set relevant to Linux troubleshooting)
STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "through", "during", "before", "after", "above", "below",
    "it", "its", "this", "that", "these", "those", "i", "my", "your",
    "when", "while", "although", "though", "if", "then", "because",
    "and", "or", "but", "so", "yet", "nor", "not",
})

# Linux-specific technical terms to always preserve (never strip)
PRESERVE_TERMS: frozenset[str] = frozenset({
    "permission", "denied", "refused", "failed", "error", "warning",
    "docker", "nginx", "ssh", "git", "systemd", "systemctl", "journalctl",
    "apt", "yum", "dnf", "pip", "disk", "memory", "cpu", "network",
    "dns", "oom", "timeout", "socket", "daemon", "service", "port",
    "bind", "address", "connection", "firewall", "iptables", "ufw",
    "ssl", "tls", "certificate", "key", "publickey", "group",
    "space", "inode", "filesystem", "mount", "kernel", "process",
    "swap", "ram", "load", "average", "zombie", "defunct",
})


def clean_text(text: str) -> str:
    """
    Clean and normalize raw Linux error text.

    Steps:
    1. Lowercase
    2. Remove IP addresses (they vary per system)
    3. Remove file paths (keep filename only)
    4. Remove punctuation (keep hyphens in compound words)
    5. Collapse whitespace
    """
    text = text.lower()

    # Remove IP addresses (192.168.x.x, ::1, etc.)
    text = re.sub(r'\b\d{1,3}(?:\.\d{1,3}){3}\b', 'IPADDR', text)

    # Remove port numbers after colon (e.g., :8080, :22)
    text = re.sub(r':\d{2,5}\b', '', text)

    # Simplify file paths — keep only the last component
    text = re.sub(r'(?:/[\w.-]+)+', lambda m: m.group(0).split('/')[-1], text)

    # Remove hex codes (e.g., 0x7f3b)
    text = re.sub(r'0x[0-9a-fA-F]+', '', text)

    # Replace non-alphanumeric (except spaces and hyphens) with space
    text = re.sub(r'[^a-z0-9\s\-]', ' ', text)

    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def tokenize(text: str) -> list[str]:
    """Split cleaned text into tokens."""
    return text.split()


def remove_stopwords(tokens: list[str]) -> list[str]:
    """
    Remove stopwords, but always preserve Linux technical terms.

    Args:
        tokens: List of lowercase word tokens.

    Returns:
        Filtered token list.
    """
    return [
        token for token in tokens
        if token in PRESERVE_TERMS or token not in STOPWORDS
    ]


def preprocess(text: str) -> str:
    """
    Full preprocessing pipeline: clean → tokenize → remove stopwords → join.

    Args:
        text: Raw user input or log message.

    Returns:
        A cleaned string ready for TF-IDF vectorization.
    """
    cleaned = clean_text(text)
    tokens = tokenize(cleaned)
    filtered = remove_stopwords(tokens)
    return " ".join(filtered)
