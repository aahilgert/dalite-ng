from faker import Faker

from peerinst.models import Discipline, Question, RationaleOnlyQuestion

fake = Faker()


def new_questions(n, teacher):
    def generator():
        i = 0
        while True:
            i += 1
            yield {
                "title": fake.sentence(),
                "text": fake.paragraph(),
                "user": teacher.user,
            }

    gen = generator()
    return [next(gen) for _ in range(n)]


def new_disciplines(n):
    def generator():
        i = 0
        while True:
            i += 1
            yield {"title": fake.word()}

    gen = generator()
    return [next(gen) for _ in range(n)]


def add_questions(questions):
    return [Question.objects.get_or_create(**q)[0] for q in questions]


def add_disciplines(disciplines):
    return [Discipline.objects.get_or_create(**d)[0] for d in disciplines]


def add_rationale_only_questions(questions):
    return [
        RationaleOnlyQuestion.objects.get_or_create(**q)[0] for q in questions
    ]
