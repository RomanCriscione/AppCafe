import pytest
from django.contrib.auth import get_user_model
from reviews.models import Cafe, Tag


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username='usuario_test', password='test1234'
    )


@pytest.fixture
def cafe(user):
    return Cafe.objects.create(
        name='Café Test',
        address='Calle Falsa 123',
        location='Springfield',
        description='Café de prueba con wifi',
        phone='123456',
        owner=user,
    )


@pytest.fixture
def tag(db):
    return Tag.objects.create(name='Especialidad')
