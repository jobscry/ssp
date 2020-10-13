from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from ssp.controls.models import Control
from ssp.utils.views import ActiveTabView

from .models import Approval, Detail, Entry, Plan
from .forms import NewPlanForm


class BasePlanView(LoginRequiredMixin, ActiveTabView):
    active_tab = "plans"


class BasePlanRestrictedView(BaseException, UserPassesTestMixin):
    def test_func(self):
        if self.request.user.has_perm("plans.change_plan"):
            return True


class PlanListView(BasePlanView, ListView):
    model = Plan


class PlanCreateView(BasePlanRestrictedView, CreateView):
    model = Plan
    form_class = NewPlanForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.save()
        messages.success(self.request, "Plan created.", fail_silently=True)
        return redirect(self.get_success_url())


class PlanDetailView(BasePlanView, DetailView):
    model = Plan
    queryset = Plan.objects.select_related()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if (control_slug := self.kwargs.get("control_slug", None)) is not None:
            context["control"] = get_object_or_404(Control, slug=control_slug)
            context["control_list"] = context["control"].get_descendants()
        else:
            context["control_list"] = Control.objects.filter(
                parent=self.object.root_control
            ).all()
            context["pending_approval"] = Detail.objects.select_related().filter(
                plan=self.object,
                status=Detail.PENDING_APPROVAL,
                entry__approvers=self.request.user,
            )
            context["pending_approval_count"] = context["pending_approval"].count()
            context["collaborating"] = Detail.objects.select_related().filter(
                plan=self.object,
                status=Detail.DRAFT,
                entry__collaborators=self.request.user,
            )
            context["observing"] = Detail.objects.select_related().filter(
                plan=self.object,
                status=Detail.DRAFT,
                entry__observers=self.request.user,
            )
            context["approved"] = list(
                Approval.objects.filter(plan=self.object, user=self.request.user)
                .select_related()
                .values_list("detail__pk", flat=True)
            )
        return context


class PlanUpdateView(BasePlanRestrictedView, SuccessMessageMixin, UpdateView):
    model = Plan
    fields = ("title", "description")
    success_message = "Plan updated."


class PlanDeleteView(BasePlanRestrictedView, DeleteView):
    model = Plan
    success_url = reverse_lazy("plans:list")
    active_tab = "plans"


@login_required
def plan_control_entry(request, plan_pk, control_slug):
    plan = get_object_or_404(Plan, pk=plan_pk)
    control = get_object_or_404(Control, slug=control_slug, is_placeholder=False)

    try:
        entry = Entry.objects.filter(plan=plan, control=control).prefetch_related(
            "approvers", "collaborators", "observers"
        )[0]
    except IndexError:
        entry = Entry.objects.create(plan=plan, control=control)

    try:
        detail = Detail.objects.get(entry=entry, status=Detail.DRAFT)
    except Detail.DoesNotExist:
        try:
            detail = Detail.objects.get(entry=entry, status=Detail.PENDING_APPROVAL)
        except Detail.DoesNotExist:
            detail = entry.latest_published_detail()

    if detail.status != detail.PUBLISHED:
        can_approve = entry.user_can_approve(request.user)
        can_collaborate = entry.user_can_collaborate(request.user)

        try:
            approval = Approval.objects.get(detail=detail, user=request.user)
        except Approval.DoesNotExist:
            approval = None
    else:
        can_approve = False
        can_collaborate = False
        approval = None

    approval_list = (
        Approval.objects.select_related("user")
        .filter(detail=detail)
        .order_by("user__name")
    )

    approval_pk_list = list(approval_list.values_list("user__pk", flat=True))

    return render(
        request,
        "plans/plan_control_entry.html",
        {
            "plan": plan,
            "control": control,
            "entry": entry,
            "detail": detail,
            "can_approve": can_approve,
            "can_collaborate": can_collaborate,
            "approval": approval,
            "approval_list": approval_list,
            "approval_pk_list": approval_pk_list,
            "active_tab": "plans",
        },
    )


class EntryUpdateView(BasePlanRestrictedView, SuccessMessageMixin, UpdateView):
    model = Entry
    fields = ("approvers", "collaborators", "observers")
    success_message = "Entry updated."
    queryset = Entry.objects.select_related()

    def get_success_url(self):
        return reverse_lazy(
            "plans:plan-control-entry",
            args=[self.object.plan.pk, self.object.control.slug],
        )


@login_required
@permission_required("plans.change_plan")
def create_detail(request, entry_pk):
    entry = get_object_or_404(Entry.objects.select_related(), pk=entry_pk)

    if Detail.objects.filter(
        entry=entry, status__in=[Detail.DRAFT, Detail.PENDING_APPROVAL]
    ).exists():
        raise PermissionDenied
    else:
        prev_detail = entry.latest_published_detail()
        detail = Detail.objects.create(
            entry=entry, plan=entry.plan, text=prev_detail.text
        )
        return redirect("plans:update-detail", pk=detail.pk)


@login_required
def toggle_detail_approval(request, pk):
    detail = get_object_or_404(
        Detail.objects.select_related(), status=Detail.PENDING_APPROVAL,
    )

    entry = detail.entry

    if not (
        request.user.has_perm("plans.change_plan")
        or entry.user_can_approve(request.user)
    ):
        raise PermissionDenied

    approval, created = Approval.objects.get_or_create(
        detail=detail, user=request.user, defaults={"plan": detail.entry.plan}
    )
    if not created:
        approval.delete()
        messages.success(request, "Approval removed.")
    else:
        messages.success(request, "Approval added.")

    return redirect(
        reverse_lazy(
            "plans:plan-control-entry", args=[entry.plan.pk, entry.control.slug],
        )
    )


class DetailUpdateView(BasePlanView, SuccessMessageMixin, UpdateView):
    model = Detail
    fields = ("status", "text")
    success_message = "Entry updated."
    queryset = Detail.objects.exclude(status=Detail.PUBLISHED).select_related(
        "entry", "entry__plan", "entry__control"
    )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=None)
        if not (
            self.request.user.has_perms("plans.change_plan")
            or obj.entry.collaborators.filter(pk=self.request.user.pk).exists()
        ):
            raise PermissionDenied
        return obj

    def get_success_url(self):
        if self.object.status == Detail.PUBLISHED:
            return reverse_lazy(
                "plans:plan-control-entry",
                args=[self.object.entry.plan.pk, self.object.entry.control.slug],
            )
        return reverse_lazy("plans:update-detail", args=[self.object.pk])


class DetailDeleteView(BasePlanRestrictedView, DeleteView):
    model = Plan
    success_url = reverse_lazy("plans:list")
    queryset = Detail.objects.exclude(status=Detail.PUBLISHED).select_related(
        "entry", "entry__plan", "entry__control"
    )

    def get_success_url(self):
        return reverse_lazy(
            "plans:plan-control-entry",
            args=[self.object.entry.plan.pk, self.object.entry.control.slug],
        )
