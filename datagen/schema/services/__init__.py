from factory import Faker

from .variable_sentences_provider import Provider as SentencesProvider

Faker.add_provider(SentencesProvider)
