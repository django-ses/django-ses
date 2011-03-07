from django.contrib.auth.models import AnonymousUser


class FakeSuperuserMiddleware(object):

    def process_request(self, request):
        request.user = AnonymousUser()
        request.user.is_superuser = True

