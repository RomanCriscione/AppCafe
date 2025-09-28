import pytest
from reviews.forms import ReviewForm, CafeForm
from reviews.models import Tag


@pytest.mark.django_db
def test_valid_review_form():
    form_data = {
        'rating': 5,
        'comment': 'Excelente atención y café de primera.'
    }
    form = ReviewForm(data=form_data)
    assert form.is_valid(), f"Errores inesperados: {form.errors}"


@pytest.mark.django_db
def test_invalid_review_form_without_rating():
    form_data = {'comment': 'Faltó puntaje.'}
    form = ReviewForm(data=form_data)
    assert not form.is_valid()
    assert 'rating' in form.errors


@pytest.mark.django_db
def test_review_form_comment_optional():
    form_data = {'rating': 3, 'comment': ''}
    form = ReviewForm(data=form_data)
    assert form.is_valid(), f"Errores inesperados: {form.errors}"


@pytest.mark.django_db
def test_valid_cafe_form_with_tags(db, django_user_model):
    user = django_user_model.objects.create_user(username='dueno', password='pass')
    tag = Tag.objects.create(name='Especialidad')

    form_data = {
        'name': 'Café de prueba',
        'address': 'Av. Siempreviva 123',
        'location': 'Springfield',
        'description': 'Un café cómodo y moderno.',
        'phone': '123456',
        'google_maps_url': 'https://maps.google.com/?q=Springfield',
        'tags': [tag.id],
    }
    form = CafeForm(data=form_data)
    assert form.is_valid(), f"Errores inesperados: {form.errors}"


@pytest.mark.django_db
def test_invalid_cafe_form_missing_name():
    form_data = {
        'address': 'Sin nombre',
        'location': 'Springfield',
        'description': 'Falta nombre',
        'phone': '000000'
    }
    form = CafeForm(data=form_data)
    assert not form.is_valid()
    assert 'name' in form.errors
