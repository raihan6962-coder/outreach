import re
import socket
import dns.resolver
from typing import Dict

DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "guerrillamail.com",
    "10minutemail.com",
    "yopmail.com",
    "trashmail.com",
    "sharklasers.com",
    "throwaway.email",
    "tempmail.com",
    "temp-mail.org",
    "getairmail.com",
    "mailnator.com",
    "mailexpire.com",
    "mailcatch.com",
    "spamgourmet.com",
    "spambox.us",
    "dispostable.com",
    "maildrop.cc",
    "emailondeck.com",
    "inboxbear.com",
    "burnermail.io",
    "mytemp.email",
    "tempinbox.com",
    "fakeinbox.com",
    "generator.email",
    "mailforspam.com",
    "mintemail.com",
    "mytrashmail.com",
    "nowmymail.com",
    "sneakemail.com",
    "spamfree24.org",
    "tempemail.co",
    "tempemail.net",
    "trash2009.com",
    "trashymail.com",
    "wegwerfmail.de",
    "wh4f.org",
    "whyspam.me",
    "boun.cr",
    "cellurl.com",
    "correotemporal.org",
    "emailias.com",
    "emailsensei.com",
    "fakemailgenerator.com",
    "filzmail.com",
    "gigaremail.com",
    "great-host.in",
    "haltospam.com",
    "icx.in",
    "inxce.com",
    "ip6.li",
    "kaskud.com",
    "mail-temp.com",
    "mail.gen.tr",
    "mailmoat.com",
    "mailmetrash.com",
    "mailline.net",
    "mailtothis.com",
    "mymailoasis.com",
    "naskuk.com",
    "nervmich.net",
    "nospamfor.us",
    "nospammail.net",
    "objectmail.com",
    "obobbo.com",
    "olypmall.ru",
    "oneoffemail.com",
    "oopi.org",
    "pastebitch.com",
    "pookmail.com",
    "proxymail.eu",
    "quickinbox.com",
    "rcpt.at",
    "recode.me",
    "recut.eu",
    "regbypass.com",
    "rockmail.ru",
    "safe-mail.net",
    "safetymail.info",
    "sogetthis.com",
    "soodonims.com",
    "spambob.com",
    "spambog.com",
    "spambog.de",
    "spambox.info",
    "spamcero.com",
    "spamday.com",
    "spamevac.com",
    "spamfighter.info",
    "spamgoes.in",
    "spamherelots.com",
    "spamjadoo.com",
    "spamkill.info",
    "spaml.com",
    "spamlot.net",
    "spamoff.xyz",
    "spamstack.net",
    "spamthis.co.uk",
    "spamtrail.com",
    "spamtrap.ro",
    "spamwc.de",
    "spamwc.xyz",
    "spamx.net",
    "speed.1s.fr",
    "superrito.com",
    "suremail.info",
    "tempail.com",
    "tempalias.com",
    "tempmail.us",
    "tempmailer.com",
    "tempomail.fr",
    "thankyou2010.com",
    "thisisnotmyrealemail.com",
    "throwawayemailaddress.com",
    "tilien.com",
    "trash2000.com",
    "trash2007.com",
    "trashdevil.com",
    "trashemail.de",
    "trashmail.at",
    "trashmail.me",
    "trashmail.net",
    "trashmail.org",
    "trashmail.ws",
    "trashmailer.com",
    "trashymail.net",
    "tyldd.com",
    "uggsrock.com",
    "weg-werf-mail.de",
    "wegwerfmail.net",
    "wegwerfmail.org",
    "whopy.com",
    "wuzup.net",
    "xagloo.com",
    "xemaps.com",
    "xents.com",
    "yep.it",
    "zepko.com",
    "zerodocs.com",
    "zippymail.info",
    "zoaxe.com",
    "zoemail.org",
}


def validate_email_syntax(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_domain(email: str) -> bool:
    domain = email.split("@")[-1] if "@" in email else ""
    if not domain:
        return False
    try:
        socket.getaddrinfo(domain, 80)
        return True
    except (socket.gaierror, OSError):
        return False


def validate_mx(email: str) -> bool:
    domain = email.split("@")[-1] if "@" in email else ""
    if not domain:
        return False
    try:
        records = dns.resolver.resolve(domain, "MX")
        return len(records) > 0
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout):
        return False


def is_disposable(email: str) -> bool:
    domain = email.split("@")[-1].lower() if "@" in email else ""
    return domain in DISPOSABLE_DOMAINS


def is_catch_all(email: str) -> bool:
    domain = email.split("@")[-1] if "@" in email else ""
    if not domain:
        return False
    test_address = f"nonexistent-{abs(hash(email))}@{domain}"
    try:
        socket.getaddrinfo(domain, 25)
        return True
    except (socket.gaierror, OSError):
        return False


def validate_email(email: str) -> Dict:
    syntax_valid = validate_email_syntax(email)
    domain_valid = validate_domain(email) if syntax_valid else False
    mx_valid = validate_mx(email) if domain_valid else False
    disposable = is_disposable(email) if syntax_valid else False
    catch_all = is_catch_all(email) if domain_valid else False

    overall_valid = all([
        syntax_valid,
        domain_valid,
        mx_valid,
        not disposable,
    ])

    return {
        "syntax_valid": syntax_valid,
        "domain_valid": domain_valid,
        "mx_valid": mx_valid,
        "disposable": disposable,
        "catch_all": catch_all,
        "overall_valid": overall_valid,
    }
