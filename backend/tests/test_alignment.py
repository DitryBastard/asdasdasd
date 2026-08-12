from app.alignment import align_tables


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
