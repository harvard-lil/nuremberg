from django.shortcuts import render

def render_error(request, status, title, friendly_message, friendly_description):
    response = render(request, 'error.html', {'title':title, 'friendly_message': friendly_message, 'friendly_description': friendly_description})
    response.status_code = status
    return response


def handler404(request, exception):
    return render_error(request,
        404,
        'Page Not Found',
        "We can't find the page you're looking for.",
        """
        The page you're trying to access doesn't seem to exist on our site.
        Double check the address to make sure it's correct.
        If you followed a link to this page, you may have to ask the owners
        of that page to update it.
        """
    )

def handler400(request, exception):
    return render_error(request,
        400,
        'Request Error',
        "There's a problem with your request.",
        """
        Your web browser sent us a request that we don't know how to process.
        Make sure your software is up-to-date and try again.
        """
    )
def handler403(request, exception):
    return render_error(request,
        403,
        'Permission Denied',
        "You're not allowed to access that page.",
        """
        The page you're trying to access requires authorization to access.
        If you are authorized, please double-check your login information.
        """
    )

def handler500(request):
    return render_error(request,
        500,
        'Server Error',
        "We had a problem handling your request.",
        """
        Our server encountered an error while finding the page you asked for,
        and had to stop. Sorry about that! We've been notified of the
        error, and we'll see if we can prevent it in the future.
        """
    )
