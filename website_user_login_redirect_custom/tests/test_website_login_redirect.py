# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestWebsiteLoginRedirect(common.TransactionCase):
    """Test website login redirect functionality"""

    def setUp(self):
        super().setUp()
        self.config_parameter = self.env["ir.config_parameter"].sudo()
        # Reset to default state before each test
        self.config_parameter.set_param(
            "website_user_login_redirect_custom.enabled", "0"
        )
        self.config_parameter.set_param("website_user_login_redirect_custom.url", "/")

    def test_redirect_disabled_after_setup(self):
        """Test that redirect is disabled by default"""
        enabled = self.config_parameter.get_param(
            "website_user_login_redirect_custom.enabled"
        )
        self.assertEqual(enabled, "0")

    def test_enable_redirect_feature(self):
        """Test enabling redirect feature through settings"""
        settings = self.env["res.config.settings"].create({})
        settings.website_login_redirect_enabled = True
        settings.website_login_redirect_url = "/shop"
        self.env.flush_all()
        settings.execute()

        self.assertEqual(
            self.config_parameter.get_param(
                "website_user_login_redirect_custom.enabled"
            ),
            "1",
        )
        self.assertEqual(
            self.config_parameter.get_param("website_user_login_redirect_custom.url"),
            "/shop",
        )

    def test_url_validation_accepts_valid_urls(self):
        """Test that URL validation accepts valid relative URLs"""
        settings = self.env["res.config.settings"].create({})
        valid_urls = ["/", "/shop", "/web#home", "/my/custom/path", "/page?param=value"]
        for url in valid_urls:
            self.assertTrue(settings.is_valid_redirect_url(url))

    def test_url_validation_rejects_invalid_urls(self):
        """Test that URL validation rejects invalid URLs"""
        settings = self.env["res.config.settings"].create({})
        invalid_urls = [
            "shop",
            "http://evil.com",
            "https://test.com",
            "//phish.com",
            "javascript:alert(1)",
            "data:text/html;base64,xxx",
            "vbscript:msgbox(1)",
        ]
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValidationError):
                    settings.website_login_redirect_url = url
                    settings._check_url_format()

    def test_settings_view_exists(self):
        """Test that settings view is properly extended"""
        view = self.env.ref(
            "website_user_login_redirect_custom.view_website_login_redirect_settings"
        )
        self.assertTrue(view)
        self.assertEqual(view.model, "res.config.settings")

    def test_default_parameters(self):
        """Test that default parameters are set correctly"""
        self.assertEqual(
            self.config_parameter.get_param("website_user_login_redirect_custom.url"),
            "/",
        )
        self.assertEqual(
            self.config_parameter.get_param(
                "website_user_login_redirect_custom.enabled"
            ),
            "0",
        )

    def test_settings_roundtrip(self):
        """Test saving and loading settings"""
        settings = self.env["res.config.settings"].create({})
        settings.website_login_redirect_enabled = True
        settings.website_login_redirect_url = "/thank-you"
        self.env.flush_all()
        settings.execute()

        new_settings = self.env["res.config.settings"].create({})
        self.assertTrue(new_settings.website_login_redirect_enabled)
        self.assertEqual(new_settings.website_login_redirect_url, "/thank-you")

    def test_empty_url_validation(self):
        """Test validation with empty URL when enabled"""
        settings = self.env["res.config.settings"].create({})
        settings.website_login_redirect_enabled = True

        # Should allow empty URL (will use default)
        settings.website_login_redirect_url = False
        settings._check_url_format()  # Should not raise

        # Should allow None
        settings.website_login_redirect_url = None
        settings._check_url_format()  # Should not raise

    def test_boolean_field_behavior(self):
        """Test that Boolean field correctly handles True/False values"""
        settings = self.env["res.config.settings"].create({})

        # Test initial state (should load from config parameter which is "0")
        self.assertFalse(settings.website_login_redirect_enabled)

        # Test setting to True
        settings.website_login_redirect_enabled = True
        settings.execute()

        # Verify parameter was saved as "1"
        enabled_param = self.config_parameter.get_param(
            "website_user_login_redirect_custom.enabled"
        )
        self.assertEqual(enabled_param, "1")

        # Create new settings instance and verify it loads the True value correctly
        new_settings = self.env["res.config.settings"].create({})
        self.assertTrue(new_settings.website_login_redirect_enabled)

        # Test setting back to False
        new_settings.website_login_redirect_enabled = False
        new_settings.execute()

        # Verify parameter was saved as "0"
        enabled_param = self.config_parameter.get_param(
            "website_user_login_redirect_custom.enabled"
        )
        self.assertEqual(enabled_param, "0")

        # Create another settings instance and verify it loads the False value
        final_settings = self.env["res.config.settings"].create({})
        self.assertFalse(final_settings.website_login_redirect_enabled)
