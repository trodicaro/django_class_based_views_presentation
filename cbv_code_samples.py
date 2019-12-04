# a basic formview:
class EmployeeInfo(FormView): # can combine with other custom mixins
    # eg: a mixin to extract the common form validation/saving behaviors
    # right-most is the top-most ancestor in the mixin composition 
    form_class = EmployeeInfoForm
    template_name = 'employee_info.html'
    success_url = reverse_lazy('form_review')

    def form_valid(self, form):
        current_record = form.save()
        return super().form_valid(form) # redirects & renders success_url


# custom actions if form_valid:
class EmployeeInfo(FormView):
    ...

    def form_valid(self, form):
        # save form data in an obj, don't post to DB yet
        current_record = form.save(commit=False) 
        current_record.last_update_by = request.user
        current_record.save()
        # other possible action: carry a submission id in session & retrieve it
        submission = get_submission(self.request) 
        submission.submission_type = form.cleaned_data['submission_type'] # update w user input
        submission.last_update_by = self.request.user # auto update aka userstamp
        submission.save()

        # another possibile action: connect record from current form with submission
        current_record.submission = submission

        return super().form_valid(form)


def get_submission(request):
    if 'submission_id' in request.session:
        submission_id = request.session['submission_id']
        submission = Submission.objects.get(id=submission_id)
    else:
        try:
           submission = Submission.objects.filter(user_id=current_user.id) 
        except Submission.DoesNotExist:
            submission = Submission(
                create_by=current_user,
                last_update_by=current_user,
            )

    request.session['submission_id'] = submission.id
    return submission


# pass additional info to template via context
class EmployeeInfo(FormView):
    ...

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submission = get_submission(self.request)
        context['submission'] = submission
        return context


# skip this view upon condition
class EmployeeInfo(FormView):
    ...

    def get(self, request):
        submission = get_submission(request)

        if not submission:
            return redirect(self.success_url)


# dynamic success_url based on user choice
class EnrollmentMenu(FormView):
    ...

    def get_success_url(self, request):
        choices = {
            "New Enrollment": "employee_info"
            "Change Enrollment": "change_menu"
        }

        user_choice = self.request.POST['choice']
        return reverse_lazy(choices[user_choice])

# I used it with a hidden form like so:
class EnrollmentMenu(forms.Form):
    choice = forms.CharField(widget=forms.HiddenInput())


# pass a custom form keyword argument => can use for custom form validation
class EnrollmentMenu(FormView):
    ...

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        # argument below is set to a global constant
        # but can be custom dictated by the enrolling company settings
        form_kwargs['employee_max_HSA'] = MAX_HSA
        return form_kwargs

        # this kwarg needs to be popped out during the init of the EmployeeInfoForm:
        # def __init__(self, *args, **kwargs):
        #     self.employee_max_HSA = kwargs.pop('employee_max_HSA', False)
        #     super().__init__(*args, **kwargs)


# retrieve a particular instance and fill form
# note: there is a SingleObjectMixin, but it's opinionated and adds overhead
# https://docs.djangoproject.com/en/2.2/ref/class-based-views/mixins-single-object/
class EmployeeInfo(FormView):
    ...
    model_class = EmployeeEnrollment

    def get_instance(self):
        try:
            self.instance = self.model_class.objects.get(submission=submission)
        except self.model_class.DoesNotExist:
            self.instance = self.model_class(create_by=self.request.user)

    def get_form(self, form_class=None):
        form_class = form_class or self.get_form_class()
        self.get_instance() 
        return form_class(instance=self.instance, **self.get_form_kwargs())

# or set a queryset for a formset
class EmployeesInfo(FormView):
    ...
    formset_class = EmployeeInfoFormSet

    def get_queryset(self):
        submission = get_submission(self.request)
        if not hasattr(self, 'queryset'):
            self.queryset = self.model_class.objects.filter(submission=submission)
        return self.queryset

    def get_form(self, form_class=None):
        self.get_queryset()
        form_class = form_class or self.get_form_class()
        form_kwargs = self.get_form_kwargs()

        return form_class(queryset=self.queryset, **form_kwargs)

    def form_valid(self, formset):
        instances = formset.save(commit=False)

        for instance in instances:
            # custom data actions
        formset.save_m2m()

        formset_response = super().form_valid(formset)

        return formset_response

