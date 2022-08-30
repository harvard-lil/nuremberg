from django.views.generic import TemplateView

class ContentView(TemplateView):
    context = {}
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.context)
        return context
