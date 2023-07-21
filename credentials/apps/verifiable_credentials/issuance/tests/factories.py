import uuid
from datetime import datetime, timedelta

import factory

from credentials.apps.credentials.tests.factories import UserCredentialFactory

from ..models import IssuanceConfiguration, IssuanceLine


class IssuanceLineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IssuanceLine

    uuid = factory.LazyFunction(uuid.uuid4)
    user_credential = factory.SubFactory(UserCredentialFactory)
    processed = False
    issuer_id = factory.Sequence(lambda o: o)
    storage_id = factory.Sequence(lambda o: o)
    subject_id = factory.Sequence(lambda o: "subject-id-%d" % o)
    data_model_id = factory.Sequence(lambda o: "data-model-id-%d" % o)
    expiration_date = factory.LazyFunction(lambda: datetime.now() + timedelta(days=30))
    status_index = factory.Sequence(lambda n: n)
    status = factory.Sequence(lambda o: o)


class IssuanceConfigurationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IssuanceConfiguration

    enabled = True
    issuer_id = factory.Sequence(lambda n: n)
    issuer_key = {"public_key": "my-public-key", "private_key": "my-private-key"}
    issuer_name = factory.Faker("company")
