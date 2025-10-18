# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.main import Home


class WebsiteRedirectCustom(Home):
    """
    Inherit from Home to override login behavior
    This works even without auth_signup module
    """

    def _should_redirect_custom(self):
        """Check if we should perform custom redirect"""
        if not request.session.uid:
            return False

        # Do not redirect backend/internal users
        if request.env.user.has_group("base.group_user"):
            return False

        enabled = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("website_user_login_redirect_custom.enabled", "0")
        )
        return enabled == "1"

    def _get_custom_redirect_url(self):
        """Get custom redirect URL or False if not set/valid"""
        url = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("website_user_login_redirect_custom.url", "/")
        )
        if not url:
            return False
        url = url.strip()
        if request.env["res.config.settings"].is_valid_redirect_url(url):
            return url

        return False

    @http.route("/web/login", type="http", auth="public", website=True, sitemap=False)
    def web_login(self, redirect=None, **kw):
        """Override standard login route to apply a custom redirect after login."""
        response = super().web_login(redirect=redirect, **kw)

        # Only redirect if:
        # 1. User is logged in and is portal/website user
        # 2. Feature is enabled
        # 3. We have a valid redirect response
        # 4. Custom URL is valid and safe
        if (
            self._should_redirect_custom()
            and hasattr(response, "status_code")
            and response.status_code in (303, 302)
        ):
            custom_url = self._get_custom_redirect_url()
            if custom_url:
                return request.redirect(custom_url)

        return response
