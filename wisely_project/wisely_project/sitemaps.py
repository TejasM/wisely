from django.contrib import sitemaps


class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['/index', '/about', '/faq']

    def location(self, item):
        return item