# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals

import itertools
import string
import datetime
from collections import defaultdict, Counter


from django.utils.safestring import mark_safe
from django.db.models import (
    Count,
    Value,
    Case,
    Q,
    When,
    CharField,
    DurationField,
    F,
    ExpressionWrapper,
    Avg,
)
from peerinst.models import (
    Question,
    Assignment,
    Student,
    Answer,
    LtiEvent,
    ShownRationale,
)


def get_object_or_none(model_class, *args, **kwargs):
    try:
        return model_class.objects.get(*args, **kwargs)
    except model_class.DoesNotExist:
        return None


def int_or_none(s):
    if s == "None":
        return None
    return int(s)


def roundrobin(iterables):
    "roundrobin(['ABC', 'D', 'EF']) --> A D E B F C"
    # Recipe taken from the itertools documentation.
    iterables = list(iterables)
    pending = len(iterables)
    nexts = itertools.cycle(iter(it).next for it in iterables)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = itertools.cycle(itertools.islice(nexts, pending))


def make_percent_function(total):
    if total:

        def percent(enum):
            return mark_safe("{:.1f}&nbsp;%".format(100 * enum / total))

    else:

        def percent(enum):
            return ""

    return percent


class SessionStageData(object):
    """
    Manages data to be kept in the session between different question stages
    """

    SESSION_KEY = "dalite_stage_data"

    def __init__(self, session, custom_key):
        self.custom_key = custom_key
        self.session = session
        self.data_dict = session.setdefault(self.SESSION_KEY, {})
        self.data = self.data_dict.get(custom_key)

    def store(self):
        if self.data is None:
            return
        # There is a race condition here:  Django loads the session before
        # calling the view, and stores it after returning.  Two concurrent
        # request can result in changes being lost.
        # This only happens if the same user sends POST requests for two
        # different questions at exactly the same time, which doesn't seem
        # likely (or useful to support).
        self.data_dict[self.custom_key] = self.data
        # Explicitly mark the session as modified since it can't detect
        # nested modifications.
        self.session.modified = True

    def update(self, **kwargs):
        if self.data is None:
            self.data = kwargs
        else:
            self.data.update(**kwargs)

    def get(self, key, default=None):
        if self.data is None:
            return None
        return self.data.get(key, default)

    def clear(self):
        self.data = None
        self.data_dict.pop(self.custom_key, None)
        self.session.modified = True


def load_log_archive(json_log_archive):
    """
    argument:name of json file, which should be in BASE_DIR/log directory,
    which itself is a list of tuples. Each tuple is of form
           (user_token,[course1,course2,...])

    return: none

    usage:

    In [1]: from peerinst.util import load_log_archive as load_log_archive
    In [2]: load_log_archive('student-group.json')


    Notes:
    The argument to this function is made using the following offline code
    (Ideally this function should work directly from log files, TO DO):

    fname = 'data_mydalite/studentlog1.log'
    logs=[]
    for line in open(fname,'r'):
        logs.append(json.loads(line))

    fname = 'data_mydalite/studentlog2.log'
    for line in open(fname,'r'):
        logs.append(json.loads(line))

    students={}
    for l in logs:
        # if we have seen this student before:
        if l['username'] in students:
            # if this student has not been assigned to this group
            if l['course_id'] not in students[l['username']]:
                students[l['username']].append(l['course_id'])
        else:
            students[l['username']]=[]
            students[l['username']].append(l['course_id'])

    fname = 'student-group.json'
    with open(fname,'w') as f:
        json.dump(students,f)

    """
    import json
    import os

    from django.contrib.auth.models import User
    from peerinst.models import Student, StudentGroup
    from django.conf import settings

    path_to_json = os.path.join(settings.BASE_DIR, "log", json_log_archive)

    with open(path_to_json, "r") as f:
        test = json.load(f)

    new_students = 0
    new_groups = 0

    for pair in test.items():
        user, created_user = User.objects.get_or_create(username=pair[0])
        if created_user:
            user.save()
            new_students += 1
        student, created_student = Student.objects.get_or_create(student=user)
        if created_student:
            student.save()
        for course in pair[1]:
            group, created_group = StudentGroup.objects.get_or_create(
                name=course
            )
            if created_group:
                group.save()
                new_groups += 1
            student.groups.add(group)
            student.save()

    print("{} new students loaded into db".format(new_students))
    print("{} new groups loaded into db".format(new_groups))

    return


def load_timestamps_from_logs(log_filename_list):
    """
    function to parse log files and add timestamps to previous records in
    Answer model with newly added time field
    argument: list of filenames in log directory
    return: none

    usage from shell:
    In [1]: from peerinst.util import load_timestamps_from_logs
    In [2]: load_timestamps_from_logs(['student.log','student2.log'])

    """
    import json
    import os
    from django.utils import dateparse, timezone
    from peerinst.models import Answer
    from django.conf import settings

    # load logs
    logs = []
    for name in log_filename_list:
        fname = os.path.join(settings.BASE_DIR, "log", name)
        for line in open(fname, "r"):
            log_event = json.loads(line)
            if log_event["event_type"] == "save_problem_success":
                logs.append(log_event)
    print("{} save_problem_success log events".format(len(logs)))

    # get records that don't have a timestamp
    answer_qs = Answer.objects.filter(time__isnull=True)

    records_updated = 0
    records_not_in_logs = 0

    # iterate through each record, find its log entry, and save the timestamp
    print("{} records to parse".format(len(answer_qs)))
    print("start time: {}".format(timezone.now()))
    records_parsed = 0
    for a in answer_qs:
        for log in logs:
            if (
                (log["username"] == a.user_token)
                and (log["event"]["assignment_id"] == a.assignment_id)
                and (log["event"]["question_id"] == a.question_id)
            ):
                timestamp = timezone.make_aware(
                    dateparse.parse_datetime(log["time"])
                )
                a.time = timestamp
                a.save()
                records_updated += 1
        if a.time is None:
            records_not_in_logs += 1
        records_parsed += 1
        if records_parsed % 1000 == 0:
            print("{} db records parsed".format(records_parsed))
            print("{} db records updated".format(records_updated))
            print("time: {}".format(timezone.now()))

    print("End time: {}".format(timezone.now()))
    print(
        "{} total answer table records in db updated with time field from logs".format(  # noqa
            records_updated
        )
    )
    print(
        "{} total answer table records in db not found in logs; likely seed rationales from teacher backend".format(  # noqa
            records_updated
        )
    )
    return


def rename_groups():
    """
    go through LtiUserData table and build translation dict between context_id
    and context_title;
    go through StudentGroup table, and rename with context_title (if not none)

    Usage from shell:
    [1]: from peerinst.util import rename_groups
    [2]: rename_groups()

    NOTE: on production server, this should be *immediately* followed by update
    of views.py code, in QuestionFormView, at end of emit_event method, so that
    ongoing groups are not seen as new

    CURRENT:
    group, created_group = StudentGroup.objects.get_or_create(name=course_id)

    CHANGE TO:
    course_title = self.lti_data.edx_lti_parameters.get('context_title')
    if not course_title:
        group, created_group =
            StudentGroup.objects.get_or_create(name=course_id+':'+course_title)
    else:
        group, created_group =
            StudentGroup.objects.get_or_create(name=course_id)

    """
    from django_lti_tool_provider.models import LtiUserData
    from peerinst.models import StudentGroup

    id_title_dict = {}

    for r in LtiUserData.objects.all():
        if r.edx_lti_parameters["context_id"] not in id_title_dict:
            id_title_dict[
                r.edx_lti_parameters["context_id"]
            ] = r.edx_lti_parameters["context_title"]

    for g in StudentGroup.objects.all():
        try:
            if id_title_dict[g.name]:
                print("** adding title **")
                print(g.name)
                g.title = id_title_dict[g.name]
                g.save()
                print(g.title)
        except KeyError as e:
            print(e)
            pass

    return


def student_list_from_student_groups(group_list):
    from peerinst.models import StudentGroup

    student_ids = []
    for group in StudentGroup.objects.filter(pk__in=group_list):
        student_ids.extend(
            [
                s.student.username
                for s in group.student_set.all()
                if s.student.username not in ["student"]
            ]
        )
    return student_ids


def question_search_function(search_string):
    """
    given a search_string, return query_set of question objects that have that
    string in either question text, title, or categories
    """
    query_term = (
        Question.objects.filter(
            Q(id__icontains=search_string)
            | Q(text__icontains=search_string)
            | Q(title__icontains=search_string)
            | Q(parent__title__icontains=search_string)
            | Q(parent__text__icontains=search_string)
            | Q(category__title__icontains=search_string)
            | Q(discipline__title__icontains=search_string)
            | Q(answerchoice__text__icontains=search_string)
            | Q(user__username__icontains=search_string)
        )
        .annotate(answer_count=Count("answer", distinct=True))
        .order_by("-answer_count")
    )

    return query_term


def get_student_objects_from_group_list(student_groups):
    student_obj_qs = (
        Student.objects.filter(groups__pk__in=student_groups)
        .exclude(student__username__in=["student", ""])
        .distinct()
    )
    return student_obj_qs


def subset_answers_by_studentgroup_and_assignment(
    assignment_list, student_groups
):
    """
    given list of student groups
    return student objects, filtering on special cases of students generated by
    lti/teacher interface
    """

    student_obj_qs = get_student_objects_from_group_list(student_groups)

    student_id_list = student_obj_qs.values_list(
        "student__username", flat=True
    )
    answer_qs = Answer.objects.filter(
        assignment_id__in=assignment_list
    ).filter(user_token__in=student_id_list)
    return answer_qs


def report_data_transitions(
    question, correct_answer_choices, assignment_list, student_groups
):
    """
    given question assignment, and list of student groups,
    return answer-queryset annotated by type of transition
    """

    answer_qs = subset_answers_by_studentgroup_and_assignment(
        assignment_list=assignment_list, student_groups=student_groups
    )

    answer_qs_question = answer_qs.filter(question_id=question.id)

    transitions = answer_qs_question.annotate(
        transition=Case(
            When(
                Q(first_answer_choice__in=correct_answer_choices)
                & Q(second_answer_choice__in=correct_answer_choices),
                then=Value("rr"),
            ),
            When(
                Q(first_answer_choice__in=correct_answer_choices)
                & ~Q(second_answer_choice__in=correct_answer_choices),
                then=Value("rw"),
            ),
            When(
                ~Q(first_answer_choice__in=correct_answer_choices)
                & Q(second_answer_choice__in=correct_answer_choices),
                then=Value("wr"),
            ),
            When(
                ~Q(first_answer_choice__in=correct_answer_choices)
                & ~Q(second_answer_choice__in=correct_answer_choices),
                then=Value("ww"),
            ),
            output_field=CharField(),
        )
    )

    return transitions


def get_correct_answer_choices(question):
    answer_choices_correct = question.answerchoice_set.values_list(
        "correct", flat=True
    )  # e.g. [False, False, True, True]

    correct_answer_choices = list(
        itertools.compress(itertools.count(1), answer_choices_correct)
    )  # e.g. [3,4]
    return correct_answer_choices


def report_data_by_assignment(assignment_list, student_groups):
    """
    Returns data for report by assignment

    Parameters
    ----------
    assignment_list : List[Assignment]
        Wanted assignments
    student_groups : List[int]
        Primary keys for wanted student groups

    Returns
    -------
    [
        {
            "assignment" : str
                title of the assignment,
            "transitions" : List[]
            "questions" : [
                {
                    "answer_choices" : List[str]
                        objects representing answer choices
                    "question_image" : ImageFieldFile
                        object representing an image for the question
                    "title" : str
                        title of the question,
                    "text" : str
                        text of the question
                    "student_responses" : List
                    "num_responses" : int
                        number of student responses
                    "transitions" : [
                    {
                        "data": List[]
                        "label" : str
                    }
                    ],
                    "confusion_matrix" : [
                        {
                        "first_answer_choice" : int
                            index of the answer choice (starting at 1)
                        "second_answer_choice" : {
                            "value" : int
                                index of the answer choice (starting at 1)
                            "N" : int
                                number of answers with that choice
                            }
                        }
                    ]
                    "answer_distributions" [
                        {
                            "data" : List[]
                            "label" : str
                                Label of what the data corresponds to (question
                                index)
                        }
                    ]
                }
            ],
        }
    ]
    """
    student_obj_qs = get_student_objects_from_group_list(student_groups)
    answer_qs = subset_answers_by_studentgroup_and_assignment(
        assignment_list, student_groups
    )

    assignment_data = []
    for a_str in assignment_list:
        a = Assignment.objects.get(identifier=a_str)
        d_a = {}
        d_a["assignment"] = a.title
        d_a["questions"] = []

        # metric_list = ["num_responses", "rr", "rw", "wr", "ww"]
        # metric_labels = ["N", "RR", "RW", "WR", "WW"]

        student_gradebook_transitions = {}
        question_list = []
        d3_data = []
        for q in a.questions.all():

            answer_qs_question = answer_qs.filter(question_id=q.id)

            d_q = {}
            d_q["text"] = q.text
            d_q["title"] = q.title
            try:
                d_q["question_image"] = q.image
            except ValueError as e:
                print(e)
                pass
            try:
                d_q["question_video"] = q.video_url
            except ValueError as e:
                print(e)
                pass

            d_q["num_responses"] = answer_qs.filter(question_id=q.id).count()

            if d_q["num_responses"] > 0:
                d_q["show"] = True

            d_q["type"] = q.type
            d_q["sequential_review"] = q.sequential_review

            question_list.append(q)

            # PI questions
            if q.answerchoice_set.all().count() > 0:
                d_q["answer_choices"] = q.answerchoice_set.all()

                # answer_choices_texts = q.answerchoice_set.values_list(
                #    "text", flat=True
                # )

                # answer_style = q.answer_style

                correct_answer_choices = get_correct_answer_choices(q)

                transitions = report_data_transitions(
                    question=q,
                    correct_answer_choices=correct_answer_choices,
                    assignment_list=assignment_list,
                    student_groups=student_groups,
                )

                # aggregates for this question in this assignment
                field_names = [
                    "first_answer_choice",
                    "second_answer_choice",
                ]  # ,'transition']
                field_labels = [
                    "First Answer Choice",
                    "Second Answer Choice",
                ]  # ,'Transition']
                d_q["answer_distributions"] = []
                for field_name, field_label in zip(field_names, field_labels):
                    counts = (
                        answer_qs_question.values_list(field_name)
                        .order_by(field_name)
                        .annotate(count=Count(field_name))
                    )

                    d_q_a_d = {}
                    d_q_a_d["label"] = field_label
                    d_q_a_d["data"] = []
                    for c in counts:
                        d_q_a_c = {}
                        d_q_a_c["answer_choice"] = list(
                            string.ascii_uppercase
                        )[c[0] - 1]
                        d_q_a_c[
                            "answer_choice_correct"
                        ] = q.answerchoice_set.values_list(
                            "correct", flat=True
                        )[
                            c[0] - 1
                        ]
                        d_q_a_c["count"] = c[1]
                        d_q_a_d["data"].append(d_q_a_c)
                    d_q["answer_distributions"].append(d_q_a_d)

                field_names = ["transition"]
                field_labels = ["Transition"]
                d_q["transitions"] = []
                for field_name, field_label in zip(field_names, field_labels):
                    counts = (
                        transitions.values_list(field_name)
                        .order_by(field_name)
                        .annotate(count=Count(field_name))
                    )

                    d_q_a_d = {}
                    d_q_a_d["label"] = field_label
                    d_q_a_d["data"] = []
                    for c in counts:
                        d_q_a_c = {}
                        d_q_a_c["transition_type"] = c[0]
                        d_q_a_c["count"] = c[1]
                        d_q_a_d["data"].append(d_q_a_c)

                        # counter for assignment level aggregate
                        if c[0] in student_gradebook_transitions:
                            student_gradebook_transitions[c[0]] += c[1]
                        else:
                            student_gradebook_transitions[c[0]] = c[1]

                d_q["transitions"].append(d_q_a_d)

                # For plot()
                d_q["matrix"] = {}
                for entry in d_q_a_d["data"]:
                    if entry["transition_type"] == "rr":
                        d_q["matrix"].update(
                            easy=entry["count"] / d_q["num_responses"]
                        )
                    if entry["transition_type"] == "ww":
                        d_q["matrix"].update(
                            hard=entry["count"] / d_q["num_responses"]
                        )
                    if entry["transition_type"] == "rw":
                        d_q["matrix"].update(
                            tricky=entry["count"] / d_q["num_responses"]
                        )
                    if entry["transition_type"] == "wr":
                        d_q["matrix"].update(
                            peer=entry["count"] / d_q["num_responses"]
                        )

                first_choice = {}
                second_choice = {}
                for entry in d_q["answer_distributions"]:
                    if entry["label"] == "First Answer Choice":
                        for choice in entry["data"]:
                            first_choice[choice["answer_choice"]] = (
                                choice["count"] / d_q["num_responses"]
                            )
                    if entry["label"] == "Second Answer Choice":
                        for choice in entry["data"]:
                            second_choice[choice["answer_choice"]] = (
                                choice["count"] / d_q["num_responses"]
                            )
                d_q["choices"] = {}
                d_q["choices"].update(first_choice=first_choice)
                d_q["choices"].update(second_choice=second_choice)
                # End plot()

                d3_data_dict = {}
                d3_data_dict["question"] = q.title
                d3_data_dict["distribution"] = d_q_a_d
                d3_data.append(d3_data_dict)

            # confusion matrix
            d_q["confusion_matrix"] = []
            for first_choice_index in range(1, q.answerchoice_set.count() + 1):
                d_q_cf = {}
                first_answer_qs = (
                    q.answer_set.filter(first_answer_choice=first_choice_index)
                    .exclude(user_token="")
                    .filter(assignment_id=a.identifier)
                )
                d_q_cf["first_answer_choice"] = first_choice_index
                d_q_cf["second_answer_choice"] = []
                for second_choice_index in range(
                    1, q.answerchoice_set.count() + 1
                ):
                    d_q_cf_a2 = {}
                    d_q_cf_a2["value"] = second_choice_index
                    count = first_answer_qs.filter(
                        second_answer_choice=second_choice_index
                    ).count()
                    if count:
                        d_q_cf_a2["N"] = count
                    else:
                        d_q_cf_a2["N"] = 0
                    d_q_cf["second_answer_choice"].append(d_q_cf_a2)
                d_q["confusion_matrix"].append(d_q_cf)

            d_q["student_responses"] = []
            for student_response in answer_qs_question:
                d_q_a = {}
                # d_q_a["student"] = student_response.user_token
                d_q_a["student"] = student_obj_qs.get(
                    student__username=student_response.user_token
                ).student.email.split("@")[0]

                d_q_a["first_answer_choice"] = list(string.ascii_uppercase)[
                    student_response.first_answer_choice - 1
                ]
                d_q_a["rationale"] = student_response.rationale
                ##
                if student_response.second_answer_choice:
                    d_q_a["second_answer_choice"] = list(
                        string.ascii_uppercase
                    )[student_response.second_answer_choice - 1]
                else:
                    d_q_a[
                        "second_answer_choice"
                    ] = student_response.second_answer_choice
                ##
                if student_response.chosen_rationale_id:
                    d_q_a["chosen_rationale"] = Answer.objects.get(
                        pk=student_response.chosen_rationale_id
                    ).rationale
                else:
                    d_q_a["chosen_rationale"] = "Stick to my own rationale"
                d_q_a["submitted"] = student_response.datetime_first

                if q.sequential_review:
                    d_q_a["upvotes"] = student_response.upvotes
                    d_q_a["downvotes"] = student_response.downvotes

                d_q["student_responses"].append(d_q_a)

            d_a["questions"].append(d_q)
            d_a["transitions"] = []
            for name, count in student_gradebook_transitions.items():
                d_t = {}
                d_t["transition_type"] = name
                d_t["count"] = count
                d_a["transitions"].append(d_t)

        assignment_data.append(d_a)

    return assignment_data


def report_data_transitions_dict(assignment_list, student_groups):

    student_transitions_by_q = {}
    for q in Question.objects.filter(
        assignment__identifier__in=assignment_list, type="PI"
    ):

        correct_answer_choices = get_correct_answer_choices(q)

        transitions = report_data_transitions(
            question=q,
            correct_answer_choices=correct_answer_choices,
            assignment_list=assignment_list,
            student_groups=student_groups,
        )
        student_transitions_by_q[q.title] = transitions.values(
            "user_token",
            "transition",
            "rationale",
            "first_answer_choice",
            "second_answer_choice",
        )
    return student_transitions_by_q


def report_data_by_student(assignment_list, student_groups):

    # needs DRY
    metric_list = ["num_responses", "rr", "rw", "wr", "ww"]
    metric_labels = ["N", "RR", "RW", "WR", "WW"]

    question_list = Question.objects.filter(
        assignment__identifier__in=assignment_list
    ).values_list("title", flat=True)

    answer_qs = subset_answers_by_studentgroup_and_assignment(
        assignment_list, student_groups
    )

    # student level gradebook
    num_responses_by_student = (
        answer_qs.values("user_token")
        .order_by("user_token")
        .annotate(num_responses=Count("user_token"))
    )

    # serialize num_responses_by_student
    student_gradebook_dict = defaultdict(Counter)
    student_gradebook_dict_by_q = defaultdict(defaultdict)
    for student_entry in num_responses_by_student:
        student_gradebook_dict[
            Student.objects.get(student__username=student_entry["user_token"])
        ]["num_responses"] += student_entry["num_responses"]

    student_transitions_by_q = report_data_transitions_dict(
        assignment_list=assignment_list, student_groups=student_groups
    )

    # aggregate results for each student
    for question, student_entries in student_transitions_by_q.items():
        for student_entry in student_entries:

            student_obj = Student.objects.get(
                student__username=student_entry["user_token"]
            )

            # build student_gradebook_dict: keys are student_objects, and
            # values are counters keeping track of how often that student made
            # each transition type
            student_gradebook_dict[student_obj][
                student_entry["transition"]
            ] += 1
            student_gradebook_dict_by_q[student_obj][question] = student_entry[
                "transition"
            ]

    # dict from just above that serializes into array for template
    gradebook_student = []
    for student_obj, grades_dict in student_gradebook_dict.items():
        d_g = {}
        d_g["student"] = student_obj.student.email.split("@")[0]

        for metric, metric_label in zip(metric_list, metric_labels):
            if metric in grades_dict:
                d_g[metric_label] = grades_dict[metric]
            else:
                d_g[metric_label] = 0
        for question in question_list:

            try:
                d_g[question] = student_gradebook_dict_by_q[student_obj][
                    question
                ]

            except KeyError as e:
                print(e)
                d_g[question] = "-"

        gradebook_student.append(d_g)
    return gradebook_student


def report_data_by_question(assignment_list, student_groups):
    """
    for aggregate gradebook over all assignments
    question level gradebook
    """
    # needs DRY
    metric_list = ["num_responses", "rr", "rw", "wr", "ww"]
    metric_labels = ["N", "RR", "RW", "WR", "WW"]

    answer_qs = subset_answers_by_studentgroup_and_assignment(
        assignment_list, student_groups
    )

    num_responses_by_question = (
        answer_qs.values("question_id")
        .order_by("question_id")
        .annotate(num_responses=Count("user_token"))
    )

    # serialize num_responses_by_question
    question_gradebook_dict = defaultdict(Counter)
    for question_entry in num_responses_by_question:
        question = Question.objects.get(id=question_entry["question_id"])
        question_gradebook_dict[question]["num_responses"] += question_entry[
            "num_responses"
        ]

    student_transitions_by_q = report_data_transitions_dict(
        assignment_list=assignment_list, student_groups=student_groups
    )

    # aggregate results for each question
    for q, student_entries in student_transitions_by_q.items():
        question = Question.objects.get(title=q)
        for student_entry in student_entries:
            question_gradebook_dict[question][student_entry["transition"]] += 1

    # array for template
    gradebook_question = []
    for question, grades_dict in question_gradebook_dict.items():
        d_g = {}
        d_g["question"] = question
        for metric, metric_label in zip(metric_list, metric_labels):
            if metric in grades_dict:
                d_g[metric_label] = grades_dict[metric]
            else:
                d_g[metric_label] = 0
        gradebook_question.append(d_g)

    return gradebook_question


def filter_ltievents(
    start_date, stop_date=datetime.datetime.now(), username=None
):
    """
    given a start date and stop date (as datetime objects), and optional
    username return all LtiEvents that match the criteria
    """
    from peerinst.models import LtiEvent

    events = LtiEvent.objects.filter(
        timestamp__gte=start_date, timestamp__lte=stop_date
    )

    if username:
        rejected_pks, event_pks = [], []
        for e in events:
            try:
                if e.event_log["username"] == username:
                    event_pks.append(e.pk)
            except TypeError as error:
                print(error)
                rejected_pks.append(e.pk)
        events = events.filter(pk__in=event_pks)
        rejected = events.filter(pk__in=rejected_pks)
    else:
        rejected = []

    return rejected, events


def build_event_dict(e, columns, event_columns):
    """
    given and LtiEvent
    return flattened dict with specified columns
    """
    try:
        event_dict1 = {c: e.event_log["event"].get(c) for c in event_columns}
        event_dict2 = {c: e.event_log.get(c) for c in columns}
        event_dict = event_dict1.copy()
        event_dict.update(event_dict2)
        event_dict["event_type"] = e.event_type
        event_dict["timestamp"] = e.timestamp
    except TypeError:
        event_dict = {}
        event_dict["event_type"] = e.event_type
        event_dict["timestamp"] = e.timestamp

    return event_dict


def serialize_events_to_dataframe(events):
    """
    given a queryset of LtiEvent objects
    return a pandas dataframe with columns username,event_type,assignment_id,
    question_id,timestamp
    """
    import pandas as pd

    columns = ["username", "course_id", "referer", "agent", "accept_language"]

    event_columns = [
        "event_type",
        "assignment_id",
        "question_text",
        "question_id",
        "timestamp",
        "rationales",
        "success",
        "assignment_title",
        "rationale_algorithm",
        "chosen_rationale_id",
        "second_answer_choice",
        "first_answer_choice",
        "rationale",
    ]

    df = pd.DataFrame(columns=columns + event_columns)

    for i, e in enumerate(events):
        df.loc[i] = pd.Series(build_event_dict(e, columns, event_columns))

    return df


def get_lti_data_as_csv(weeks_ago_start, weeks_ago_stop=0, username=None):
    import datetime
    import os
    from django.conf import settings

    print("start")
    print(datetime.datetime.now())

    start = datetime.datetime.now() - datetime.timedelta(weeks=weeks_ago_start)
    end = datetime.datetime.now() - datetime.timedelta(weeks=weeks_ago_stop)

    rejected, events = filter_ltievents(
        start_date=start, stop_date=end, username=username
    )
    print("events filtered")
    print(datetime.datetime.now())

    df = serialize_events_to_dataframe(events)

    print("serialied df")
    print(datetime.datetime.now())

    fname = os.path.join(settings.BASE_DIR, "data.csv")
    with open(fname, "w") as f:
        df.to_csv(path_or_buf=f, encoding="utf-8")

    return df


# https://stackoverflow.com/questions/1060279/iterating-through-a-range-of-dates-in-python
def make_daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


def load_shown_rationales_from_ltievent_logs(day_of_logs):

    event_logs = LtiEvent.objects.filter(
        timestamp__gte=day_of_logs,
        timestamp__lte=day_of_logs + datetime.timedelta(hours=24),
    )

    for e in event_logs.iterator():
        e_json = e.event_log
        if e_json["event_type"] == "save_problem_success":

            try:
                try:
                    shown_for_answer = Answer.objects.get(
                        user_token=e_json["username"],
                        question_id=e_json["event"]["question_id"],
                        assignment_id=e_json["event"]["assignment_id"],
                    )
                except Answer.MultipleObjectsReturned:
                    print(
                        "Multiple : ",
                        e_json["username"],
                        e_json["event"]["question_id"],
                        e_json["event"]["assignment_id"],
                    )
                try:
                    for r in e_json["event"]["rationales"]:
                        obj, created = ShownRationale.objects.get_or_create(  # noqa
                            shown_answer=Answer.objects.get(pk=r["id"]),
                            shown_for_answer=shown_for_answer,
                        )
                except KeyError:
                    print("No Rationales")
                    print(e_json)

            except Answer.DoesNotExist:
                print(
                    "Not found : ",
                    e_json["username"],
                    e_json["event"]["question_id"],
                    e_json["event"]["assignment_id"],
                )
    return


def get_average_time_spent_on_all_question_start(question_id):
    """
    Given a question id, return average time taken by all students to
    submit answer. If not enough data, return None
    """

    expression = F("datetime_second") - F("datetime_start")
    wrapped_expression = ExpressionWrapper(expression, DurationField())
    try:
        result = (
            Answer.objects.filter(question_id=question_id)
            .annotate(time_spent=wrapped_expression)
            .values("time_spent")
            .aggregate(Avg("time_spent"))["time_spent__avg"]
            .seconds
        )
    except AttributeError:
        result = None

    return result


def populate_answer_start_time_from_ltievent_logs(day_of_logs):
    """
    Given a date, filter event logs to populate Answer.datetime_start field for
    answer instances already in database
    """

    event_logs = LtiEvent.objects.filter(
        timestamp__gte=day_of_logs,
        timestamp__lte=day_of_logs + datetime.timedelta(hours=24),
    )
    i = 0
    for e in event_logs.iterator():
        e_json = e.event_log
        if e_json["event_type"] == "problem_show":

            try:

                answer_obj = Answer.objects.get(
                    user_token=e_json["username"],
                    question_id=e_json["event"]["question_id"],
                    assignment_id=e_json["event"]["assignment_id"],
                )

                # keep the latest time at which student accessed
                # problem start page
                if answer_obj.datetime_start:
                    if answer_obj.datetime_start < e.timestamp:
                        answer_obj.datetime_start = e.timestamp
                        answer_obj.save()
                        i += 1
                    else:
                        pass
                else:
                    answer_obj.datetime_start = e.timestamp
                    answer_obj.save()
                    i += 1

            except Answer.DoesNotExist:
                pass
                # print(
                #     "Not found : ",
                #     e_json["username"],
                #     e_json["event"]["question_id"],
                #     e_json["event"]["assignment_id"],
                # )

    print("{} answer start times updated".format(i))
    return
