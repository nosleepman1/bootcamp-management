"""Factories factory_boy pour les tests de apps.programs."""

import factory

from apps.programs.models import Program, Project


class ProgramFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Program

    title = factory.Sequence(lambda n: f"Programme {n}")
    description = ""
    status = Program.StatusProgramEnum.ACTIVE


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    program = factory.SubFactory(ProgramFactory)
    title = factory.Sequence(lambda n: f"Projet {n}")
    description = "Réalisation d'une application fullstack."
    order = factory.Sequence(lambda n: n + 1)
    duration_days = 14
    status = Project.StatusProjectEnum.PUBLISHED