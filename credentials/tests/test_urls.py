import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_api_docs(client):
    """
    Verify that the API docs render.
    """
    path = reverse('api_docs')
    response = client.get(path)

    assert response.status_code == 200
