class FoursquareLoginHandler(LoginHandler, FoursquareMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument(“code”, False):
            self.get_authenticated_user(
                redirect_uri=’/auth/foursquare/connect’,
                client_id=self.settings[“foursquare_client_id”],
                client_secret=self.settings[“foursquare_client_secret”],
                code=self.get_argument(“code”),
                callback=self.async_callback(self._on_login)
            )
            return

        self.authorize_redirect(
            redirect_uri=’/auth/foursquare/connect’,
            client_id=self.settings[“foursquare_api_key”]
        )

    def _on_login(self, user):
        # Do something interesting with user here. See: user[“access_token”]
        self.finish()
