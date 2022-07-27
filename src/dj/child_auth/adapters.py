from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    # def pre_social_login(self, request, sociallogin):
    #     assert False, (request, sociallogin.__dict__)

    def authentication_error(
        self,
        request,
        provider_id,
        error=None,
        exception=None,
        extra_context=None,
    ):
        assert False, error
