from app.alignment import align_paragraphs, align_tables


def _one_hot(index: int, dims: int) -> list[float]:
    vector = [0.0] * dims
    vector[index] = 1.0
    return vector


def test_empty_inputs_produce_no_pairs():
    assert align_paragraphs([], [], [], []) == []


def test_perfect_one_to_one_alignment():
    dims = 3
    embeddings = [_one_hot(i, dims) for i in range(dims)]
    source = ["A", "B", "C"]
    target = ["A'", "B'", "C'"]

    pairs = align_paragraphs(source, embeddings, target, embeddings)

    assert pairs == [
        {"source_text": "A", "target_text": "A'"},
        {"source_text": "B", "target_text": "B'"},
        {"source_text": "C", "target_text": "C'"},
    ]


def test_detects_inserted_paragraph_without_desyncing_the_rest():
    # This is exactly the failure mode positional (index N <-> index N)
    # alignment cannot handle: one extra paragraph on the target side used
    # to shift every pair after it out of sync.
    dims = 4
    e_a, e_b, e_c, e_x = (_one_hot(i, dims) for i in range(dims))
    source = ["A", "B", "C"]
    source_embeddings = [e_a, e_b, e_c]
    target = ["A'", "X", "B'", "C'"]
    target_embeddings = [e_a, e_x, e_b, e_c]

    pairs = align_paragraphs(source, source_embeddings, target, target_embeddings)

    assert {"source_text": "A", "target_text": "A'"} in pairs
    assert {"source_text": "B", "target_text": "B'"} in pairs
    assert {"source_text": "C", "target_text": "C'"} in pairs
    assert {"source_text": "", "target_text": "X"} in pairs
    assert len(pairs) == 4


def test_detects_deleted_paragraph():
    dims = 3
    e_a, e_b, e_c = (_one_hot(i, dims) for i in range(dims))
    source = ["A", "B", "C"]
    source_embeddings = [e_a, e_b, e_c]
    target = ["A'", "C'"]
    target_embeddings = [e_a, e_c]

    pairs = align_paragraphs(source, source_embeddings, target, target_embeddings)

    assert {"source_text": "A", "target_text": "A'"} in pairs
    assert {"source_text": "B", "target_text": ""} in pairs
    assert {"source_text": "C", "target_text": "C'"} in pairs
    assert len(pairs) == 3


def test_merges_two_source_paragraphs_into_one_target():
    dims = 3
    e_a, e_b, e_c = (_one_hot(i, dims) for i in range(dims))
    # "B" was split across two source paragraphs but translated as one.
    source = ["A", "B1", "B2", "C"]
    source_embeddings = [e_a, e_b, e_b, e_c]
    target = ["A'", "B'", "C'"]
    target_embeddings = [e_a, e_b, e_c]

    pairs = align_paragraphs(source, source_embeddings, target, target_embeddings)

    assert {"source_text": "A", "target_text": "A'"} in pairs
    assert {"source_text": "B1 B2", "target_text": "B'"} in pairs
    assert {"source_text": "C", "target_text": "C'"} in pairs
    assert len(pairs) == 3


def test_merges_one_source_paragraph_into_two_target():
    dims = 3
    e_a, e_b, e_c = (_one_hot(i, dims) for i in range(dims))
    source = ["A", "B", "C"]
    source_embeddings = [e_a, e_b, e_c]
    target = ["A'", "B1'", "B2'", "C'"]
    target_embeddings = [e_a, e_b, e_b, e_c]

    pairs = align_paragraphs(source, source_embeddings, target, target_embeddings)

    assert {"source_text": "A", "target_text": "A'"} in pairs
    assert {"source_text": "B", "target_text": "B1' B2'"} in pairs
    assert {"source_text": "C", "target_text": "C'"} in pairs
    assert len(pairs) == 3


def test_identical_length_but_shuffled_similarity_still_finds_best_pairing():
    # Same paragraph counts on both sides (positional alignment would look
    # "fine" here) but the translator reordered nothing - content decides
    # the pairing, and it must still come out correct.
    dims = 3
    e_a, e_b, e_c = (_one_hot(i, dims) for i in range(dims))
    source = ["Alpha", "Beta", "Gamma"]
    source_embeddings = [e_a, e_b, e_c]
    target = ["Alpha'", "Beta'", "Gamma'"]
    target_embeddings = [e_a, e_b, e_c]

    pairs = align_paragraphs(source, source_embeddings, target, target_embeddings)

    assert pairs == [
        {"source_text": "Alpha", "target_text": "Alpha'"},
        {"source_text": "Beta", "target_text": "Beta'"},
        {"source_text": "Gamma", "target_text": "Gamma'"},
    ]


def test_align_tables_matches_cells_by_position_even_when_meaningless_alone():
    # These bare values (element symbols, numbers) are exactly the case
    # embedding similarity can't reliably handle - positional matching must
    # not depend on the *content* being distinguishable at all.
    source = [[["Fe", "Ti", "Mo"], ["178.29", "0.5", "I"]]]
    target = [[["Fe", "Ti", "Mo"], ["178,29", "0,5", "I"]]]

    pairs = align_tables(source, target)

    assert pairs == [
        {"source_text": "Fe", "target_text": "Fe"},
        {"source_text": "Ti", "target_text": "Ti"},
        {"source_text": "Mo", "target_text": "Mo"},
        {"source_text": "178.29", "target_text": "178,29"},
        {"source_text": "0.5", "target_text": "0,5"},
        {"source_text": "I", "target_text": "I"},
    ]


def test_align_tables_flags_missing_row_as_gap():
    source = [[["A", "B"], ["C", "D"]]]
    target = [[["A", "B"]]]  # second row missing entirely

    pairs = align_tables(source, target)

    assert {"source_text": "A", "target_text": "A"} in pairs
    assert {"source_text": "B", "target_text": "B"} in pairs
    assert {"source_text": "C", "target_text": ""} in pairs
    assert {"source_text": "D", "target_text": ""} in pairs


def test_align_tables_flags_missing_column_as_gap():
    source = [[["A", "B", "C"]]]
    target = [[["A", "B"]]]  # third column missing

    pairs = align_tables(source, target)

    assert {"source_text": "A", "target_text": "A"} in pairs
    assert {"source_text": "B", "target_text": "B"} in pairs
    assert {"source_text": "C", "target_text": ""} in pairs


def test_align_tables_flags_missing_whole_table_as_gap():
    source = [[["A"]], [["B"]]]
    target = [[["A"]]]  # second table missing entirely

    pairs = align_tables(source, target)

    assert {"source_text": "A", "target_text": "A"} in pairs
    assert {"source_text": "B", "target_text": ""} in pairs


def test_align_tables_skips_fully_blank_cell_pairs():
    source = [[["A", ""]]]
    target = [[["A", ""]]]

    pairs = align_tables(source, target)

    assert pairs == [{"source_text": "A", "target_text": "A"}]


def test_align_tables_empty_inputs_produce_no_pairs():
    assert align_tables([], []) == []
