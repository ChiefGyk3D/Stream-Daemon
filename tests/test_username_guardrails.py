#!/usr/bin/env python3
"""Test username guardrails for LLM-generated messages."""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from stream_daemon.ai.generator import AIMessageGenerator


class TestUsernameGuardrails(unittest.TestCase):
    """Test cases for username tokenization and hashtag validation."""
    
    def test_tokenize_username_camelcase(self):
        """Test tokenizing CamelCase usernames."""
        tokens = AIMessageGenerator._tokenize_username("ChiefGyk3D")
        
        # Should include full username and all parts
        self.assertIn("chiefgyk3d", tokens)
        self.assertIn("chief", tokens)
        self.assertIn("gyk", tokens)
        # Note: "3d" is only 2 chars, but might be included as a special case
        
        print(f"✓ ChiefGyk3D tokens: {sorted(tokens)}")
    
    def test_tokenize_username_underscores(self):
        """Test tokenizing usernames with underscores."""
        tokens = AIMessageGenerator._tokenize_username("Chief_Gyk3D")
        
        self.assertIn("chief_gyk3d", tokens)
        self.assertIn("chief", tokens)
        self.assertIn("gyk", tokens)
        
        print(f"✓ Chief_Gyk3D tokens: {sorted(tokens)}")
    
    def test_tokenize_username_with_prefix(self):
        """Test tokenizing usernames with @ or # prefix."""
        tokens1 = AIMessageGenerator._tokenize_username("@ChiefGyk3D")
        tokens2 = AIMessageGenerator._tokenize_username("#ChiefGyk3D")
        
        # Should strip prefix and process normally
        self.assertIn("chiefgyk3d", tokens1)
        self.assertIn("chiefgyk3d", tokens2)
        self.assertIn("chief", tokens1)
        self.assertIn("chief", tokens2)
        
        print(f"✓ @ChiefGyk3D tokens: {sorted(tokens1)}")
    
    def test_tokenize_username_lowercase_prefix(self):
        """Test tokenizing usernames with lowercase prefix (e.g., iPhone, eBay)."""
        tokens = AIMessageGenerator._tokenize_username("iPhoneGamer")
        
        # Should capture 'Phone' and 'Gamer' (both >= 3 chars)
        # 'i' is only 1 char, so it won't be in the final set
        self.assertIn("iphonegamer", tokens)  # Full username
        self.assertIn("phone", tokens)
        self.assertIn("gamer", tokens)
        
        print(f"✓ iPhoneGamer tokens: {sorted(tokens)}")
    
    def test_tokenize_username_short_parts(self):
        """Test that very short parts (< 3 chars) are not included unless they're significant."""
        tokens = AIMessageGenerator._tokenize_username("AI_Bot")
        
        # Full username should be included
        self.assertIn("ai_bot", tokens)
        # "ai" is only 2 chars, might not be included to avoid false positives
        # "bot" is 3 chars, should be included
        self.assertIn("bot", tokens)
        
        print(f"✓ AI_Bot tokens: {sorted(tokens)}")
    
    def test_extract_hashtags_from_message(self):
        """Test extracting hashtags from a message."""
        message = "Going live with some Minecraft building! #Minecraft #Building #Creative"
        hashtags = AIMessageGenerator._extract_hashtags(message)
        
        self.assertEqual(len(hashtags), 3)
        self.assertIn("minecraft", hashtags)
        self.assertIn("building", hashtags)
        self.assertIn("creative", hashtags)
        
        print(f"✓ Extracted hashtags: {hashtags}")
    
    def test_remove_hashtag_from_message(self):
        """Test removing a specific hashtag from a message."""
        message = "Going live! #Minecraft #Building #Creative"
        result = AIMessageGenerator._remove_hashtag_from_message(message, "Building")
        
        self.assertNotIn("#Building", result)
        self.assertIn("#Minecraft", result)
        self.assertIn("#Creative", result)
        
        print(f"✓ After removing #Building: {result}")
    
    def test_validate_hashtags_removes_username_parts(self):
        """Test that username-derived hashtags are removed."""
        # Simulate LLM output with username-based hashtags (the problem we're fixing)
        message = "Going live with Minecraft! #Chief #Minecraft #Building"
        username = "ChiefGyk3D"
        
        result = AIMessageGenerator._validate_hashtags_against_username(message, username)
        
        # #Chief should be removed (matches username part)
        self.assertNotIn("#Chief", result)
        # #Minecraft should remain (not from username)
        self.assertIn("#Minecraft", result)
        # #Building should remain (not from username)
        self.assertIn("#Building", result)
        
        print(f"✓ Original: {message}")
        print(f"✓ Validated: {result}")
    
    def test_validate_hashtags_removes_multiple_username_parts(self):
        """Test removing multiple username-derived hashtags."""
        # Simulate LLM using multiple username parts
        message = "Stream time! #Chief #Gyk3D #Minecraft"
        username = "ChiefGyk3D"
        
        result = AIMessageGenerator._validate_hashtags_against_username(message, username)
        
        # Both #Chief and #Gyk3D should be removed
        self.assertNotIn("#Chief", result)
        self.assertNotIn("#Gyk3D", result)
        # #Minecraft should remain
        self.assertIn("#Minecraft", result)
        
        print(f"✓ Original: {message}")
        print(f"✓ Validated: {result}")
    
    def test_validate_hashtags_preserves_valid_hashtags(self):
        """Test that valid hashtags unrelated to username are preserved."""
        message = "Building in Minecraft! #Minecraft #Building #Creative"
        username = "GamerDude123"
        
        result = AIMessageGenerator._validate_hashtags_against_username(message, username)
        
        # All hashtags should be preserved (none match username)
        self.assertIn("#Minecraft", result)
        self.assertIn("#Building", result)
        self.assertIn("#Creative", result)
        
        print(f"✓ No changes needed: {result}")
    
    def test_validate_hashtags_case_insensitive(self):
        """Test that validation is case-insensitive."""
        message = "Going live! #chief #CHIEF #Chief #Minecraft"
        username = "ChiefGyk3D"
        
        result = AIMessageGenerator._validate_hashtags_against_username(message, username)
        
        # All variations of "chief" should be removed
        self.assertNotIn("#chief", result.lower())
        # #Minecraft should remain
        self.assertIn("#Minecraft", result)
        
        print(f"✓ Original: {message}")
        print(f"✓ Validated: {result}")
    
    def test_validate_hashtags_with_underscores(self):
        """Test validation with usernames containing underscores."""
        message = "Live now! #Cool #Streamer #Gaming"
        username = "Cool_Streamer_123"
        
        result = AIMessageGenerator._validate_hashtags_against_username(message, username)
        
        # #Cool and #Streamer should be removed (match username parts)
        self.assertNotIn("#Cool", result)
        self.assertNotIn("#Streamer", result)
        # #Gaming should remain
        self.assertIn("#Gaming", result)
        
        print(f"✓ Original: {message}")
        print(f"✓ Validated: {result}")


if __name__ == '__main__':
    print("=" * 80)
    print("Testing Username Guardrails for LLM-Generated Messages")
    print("=" * 80)
    print()
    
    # Run tests with verbose output
    unittest.main(verbosity=2)
