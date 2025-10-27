"""
Test the Matrix domain validation fix for CVE-2024-XXXXX
Tests for incomplete URL substring sanitization vulnerability
"""

import pytest
from stream_daemon.platforms.social.matrix import _is_url_for_domain


class TestMatrixDomainValidation:
    """Test suite for Matrix URL domain validation security fix."""
    
    def test_exact_domain_match(self):
        """Valid: Exact domain matches should work."""
        assert _is_url_for_domain('https://twitch.tv/channel', 'twitch.tv') is True
        assert _is_url_for_domain('https://kick.com/channel', 'kick.com') is True
        assert _is_url_for_domain('https://youtube.com/watch', 'youtube.com') is True
    
    def test_subdomain_match(self):
        """Valid: Proper subdomains should match."""
        assert _is_url_for_domain('https://www.twitch.tv/channel', 'twitch.tv') is True
        assert _is_url_for_domain('https://www.kick.com/channel', 'kick.com') is True
        assert _is_url_for_domain('https://m.youtube.com/watch', 'youtube.com') is True
        assert _is_url_for_domain('https://studio.youtube.com/watch', 'youtube.com') is True
    
    def test_malicious_prefix_attack(self):
        """Security: Malicious domains with target as suffix should NOT match."""
        # These are the vulnerability cases - should all be False
        assert _is_url_for_domain('https://eviltwitch.tv/phishing', 'twitch.tv') is False
        assert _is_url_for_domain('https://fakekick.com/malware', 'kick.com') is False
        assert _is_url_for_domain('https://notyoutube.com/fake', 'youtube.com') is False
        assert _is_url_for_domain('https://malicious-twitch.tv/scam', 'twitch.tv') is False
    
    def test_malicious_suffix_attack(self):
        """Security: Domains with target as prefix should NOT match."""
        assert _is_url_for_domain('https://twitch.tv.evil.com/phishing', 'twitch.tv') is False
        assert _is_url_for_domain('https://kick.com.malware.net/scam', 'kick.com') is False
    
    def test_different_domains(self):
        """Valid: Different domains should not match."""
        assert _is_url_for_domain('https://youtube.com/channel', 'twitch.tv') is False
        assert _is_url_for_domain('https://facebook.com/page', 'kick.com') is False
        assert _is_url_for_domain('https://twitter.com/user', 'youtube.com') is False
    
    def test_case_insensitive(self):
        """Valid: Domain matching should be case-insensitive."""
        assert _is_url_for_domain('https://Twitch.TV/channel', 'twitch.tv') is True
        assert _is_url_for_domain('https://KICK.COM/channel', 'kick.com') is True
        assert _is_url_for_domain('https://YouTube.Com/watch', 'youtube.com') is True
        assert _is_url_for_domain('https://WWW.TWITCH.TV/channel', 'twitch.tv') is True
    
    def test_invalid_urls(self):
        """Edge cases: Invalid URLs should return False."""
        assert _is_url_for_domain('', 'twitch.tv') is False
        assert _is_url_for_domain('not-a-url', 'twitch.tv') is False
        assert _is_url_for_domain('//no-scheme', 'twitch.tv') is False
    
    def test_missing_hostname(self):
        """Edge cases: URLs without hostname should return False."""
        assert _is_url_for_domain('file:///local/path', 'twitch.tv') is False
        assert _is_url_for_domain('javascript:alert(1)', 'twitch.tv') is False
    
    def test_port_numbers(self):
        """Valid: URLs with ports should still match correctly."""
        assert _is_url_for_domain('https://twitch.tv:443/channel', 'twitch.tv') is True
        assert _is_url_for_domain('https://www.kick.com:8080/channel', 'kick.com') is True
    
    def test_paths_and_params(self):
        """Valid: URLs with complex paths and params should match on domain only."""
        assert _is_url_for_domain(
            'https://twitch.tv/channel?param=value#anchor', 
            'twitch.tv'
        ) is True
        assert _is_url_for_domain(
            'https://www.youtube.com/watch?v=abc123&t=30s',
            'youtube.com'
        ) is True
    
    def test_ip_addresses(self):
        """Edge cases: IP addresses should not match domain strings."""
        assert _is_url_for_domain('https://192.168.1.1/page', 'twitch.tv') is False
        assert _is_url_for_domain('https://127.0.0.1:8080/', 'kick.com') is False
    
    def test_punycode_domains(self):
        """Edge cases: International domains (punycode) should work."""
        # xn--twitch-gf8h.tv is not a real twitch domain
        assert _is_url_for_domain('https://xn--fake-domain.tv/page', 'twitch.tv') is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
