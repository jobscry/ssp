class ActiveTabView:
    active_tab = "home"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_tab"] = self.active_tab
        return context
