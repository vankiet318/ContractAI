from app.retrieval.topic_gate import AnchorTopicGate


class FakeEmbedding:
    """Maps known texts to fixed unit vectors."""

    VECTORS = {
        "contract": [1.0, 0.0],
        "off": [0.0, 1.0],
    }

    def embed(self, texts):
        return [self.VECTORS[text] for text in texts]


def build_gate(min_margin: float = 0.0) -> AnchorTopicGate:
    return AnchorTopicGate(
        embedding_model=FakeEmbedding(),
        contract_examples=["contract"],
        off_topic_examples=["off"],
        min_margin=min_margin,
    )


def test_question_close_to_contract_examples_is_on_topic():
    assert build_gate().is_on_topic([0.9, 0.1])


def test_question_close_to_off_topic_examples_is_rejected():
    assert not build_gate().is_on_topic([0.1, 0.9])


def test_margin_is_difference_of_best_similarities():
    assert build_gate().margin([0.6, 0.8]) == 0.6 - 0.8


def test_very_low_min_margin_disables_gate():
    assert build_gate(min_margin=-1.0).is_on_topic([0.0, 1.0])
