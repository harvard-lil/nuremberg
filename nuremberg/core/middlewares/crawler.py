from django.http import HttpResponseForbidden
bots = ["Baiduspider"]


class BlockCrawlerMiddleware:
    def process_request(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', None)
        request.is_crawler = False

        if user_agent:
            for bot in bots:
                if bot in user_agent:
                    request.is_crawler = True

        if request.is_crawler and request.path.startswith("/search/"):
            return HttpResponseForbidden('This address is removed from crawling. Check robots.txt')

        return None
