import pytest

from reviews.models import Cafe
from reviews.utils.ranking import calcular_score_cafe


@pytest.mark.django_db
def test_cafe_con_mejor_rating_tiene_mayor_score(django_user_model):
    user = django_user_model.objects.create_user(
        username="testuser",
        password="1234"
    )

    cafe_bueno = Cafe.objects.create(
        name="Cafe Bueno",
        address="Calle 123",
        location="Palermo",
        visibility_level=0,
        has_wifi=True,
        owner=user,
    )

    cafe_malo = Cafe.objects.create(
        name="Cafe Malo",
        address="Calle 456",
        location="Palermo",
        visibility_level=0,
        owner=user,
    )

    # simulamos valores anotados (no vienen de DB)
    cafe_bueno.average_rating = 4.5
    cafe_bueno.total_reviews = 10

    cafe_malo.average_rating = 2.5
    cafe_malo.total_reviews = 2

    score_bueno = calcular_score_cafe(cafe_bueno, user=user)
    score_malo = calcular_score_cafe(cafe_malo, user=user)

    assert score_bueno > score_malo


@pytest.mark.django_db
def test_cafe_visto_penaliza_score(django_user_model):
    user = django_user_model.objects.create_user(
        username="testuser",
        password="1234"
    )

    cafe = Cafe.objects.create(
        name="Cafe Repetido",
        address="Calle 789",
        location="Centro",
        owner=user,
    )

    cafe.average_rating = 4.0
    cafe.total_reviews = 5

    score_no_visto = calcular_score_cafe(
        cafe,
        user=user,
        cafes_vistos_ids=[]
    )

    score_visto = calcular_score_cafe(
        cafe,
        user=user,
        cafes_vistos_ids=[cafe.id]
    )

    assert score_visto < score_no_visto


@pytest.mark.django_db
def test_plan_premium_tiene_mayor_score(django_user_model):
    user = django_user_model.objects.create_user(
        username="testuser",
        password="1234"
    )

    cafe_gratis = Cafe.objects.create(
        name="Cafe Gratis",
        address="Calle 111",
        location="Recoleta",
        visibility_level=0,
        owner=user,
    )

    cafe_premium = Cafe.objects.create(
        name="Cafe Premium",
        address="Calle 222",
        location="Recoleta",
        visibility_level=2,
        owner=user,
    )

    cafe_gratis.average_rating = 4
    cafe_gratis.total_reviews = 5

    cafe_premium.average_rating = 4
    cafe_premium.total_reviews = 5

    score_gratis = calcular_score_cafe(cafe_gratis, user=user)
    score_premium = calcular_score_cafe(cafe_premium, user=user)

    assert score_premium > score_gratis


@pytest.mark.django_db
def test_cercania_aumenta_score(django_user_model):
    user = django_user_model.objects.create_user(
        username="testuser",
        password="1234"
    )

    cafe_cerca = Cafe.objects.create(
        name="Cafe Cerca",
        address="Calle Cerca",
        location="Palermo",
        latitude=-34.58,
        longitude=-58.42,
        owner=user,
    )

    cafe_lejos = Cafe.objects.create(
        name="Cafe Lejos",
        address="Calle Lejos",
        location="Palermo",
        latitude=-34.70,
        longitude=-58.60,
        owner=user,
    )

    for cafe in (cafe_cerca, cafe_lejos):
        cafe.average_rating = 4
        cafe.total_reviews = 5

    score_cerca = calcular_score_cafe(
        cafe_cerca,
        user=user,
        user_lat=-34.58,
        user_lon=-58.42,
    )

    score_lejos = calcular_score_cafe(
        cafe_lejos,
        user=user,
        user_lat=-34.58,
        user_lon=-58.42,
    )

    assert score_cerca > score_lejos
