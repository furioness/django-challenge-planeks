from random import randint
from typing import Optional, Sequence
from faker.providers.lorem.en_US import Provider as LoremProvider_en_US


class Provider(LoremProvider_en_US):
    def sentences_variable_str(
        self,
        nb_min: int = 3,
        nb_max: int = 6,
        ext_word_list: Optional[Sequence[str]] = None,
    ) -> str:
        return " ".join(self.sentences(randint(nb_min, nb_max), ext_word_list))
