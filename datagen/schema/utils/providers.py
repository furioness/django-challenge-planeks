from random import randint
from typing import List, Optional, Sequence
from faker.providers.lorem.en_US import Provider as LoremProvider_en_US


# TODO: redo to standart Faker localized format


class VariableSentencesLoremProvider_en_US(LoremProvider_en_US):
    def sentences_variable_str(
        self, nb_min: int = 3, nb_max: int = 6, ext_word_list: Optional[Sequence[str]] = None
    ) -> str:
        return " ".join(self.sentences(randint(nb_min, nb_max), ext_word_list))
