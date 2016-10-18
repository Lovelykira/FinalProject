import uuid


def add_uuid_to_sessions_middleware(get_response):
    # One-time configuration and initialization.

    def middleware(request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        if 'uuid' not in request.session.keys():
            # make a random UUID
            request.session['uuid'] = str(uuid.uuid4())

        response = get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    return middleware