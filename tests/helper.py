import email.header


def decode_email_header(header: str) -> str:
    """Decode an rfc2047 encoded header to its Unicode string."""
    return " ".join(
        (
            part[0].decode(part[1] or "utf-8").strip() if isinstance(part[0], bytes) else part[0].strip()
            for part in email.header.decode_header(header)
        )
    )
