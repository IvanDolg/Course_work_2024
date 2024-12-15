# Структура полей для поиска
FIELDS = {
    'f899b': [
        {
            'name': 'f899b_1', # 899 b
            'fields': [
                'holdings_data__sublocation' # 899 b
            ]
        }
    ],
    'f999a': [
        {
            'name': 'f999a_1', # 999 a
            'fields': [
                'record_compiler__bibliographer' # 999 a
            ]
        }
    ],
    'psn': [
        {
            'name': 'psn_1', # 700 a b c d f
            'fields': [
                'personal_name_primary__entry_element', # 700 a
                'personal_name_primary__part_of_name_other_than_entry_element', # 700 b 
                'personal_name_primary__additions_to_names_other_than_dates', # 700 c 
                'personal_name_primary__roman_numerals', # 700 d
                'personal_name_primary__dates' # 700 f
            ]
        },
        {
            'name': 'psn_2', # 701 a b c d f
            'fields': [
                'personal_name_alternative__entry_element', # 701 a
                'personal_name_alternative__part_of_name_other_than_entry_element', # 701 b 
                'personal_name_alternative__additions_to_names_other_than_dates', # 701 c 
                'personal_name_alternative__roman_numerals', # 701 d
                'personal_name_alternative__dates' # 701 f
            ]
        },
        {
            'name': 'psn_3', # 702 a b c d f
            'fields': [
                'personal_name_secondary__entry_element', # 702 a
                'personal_name_secondary__part_of_name_other_than_entry_element', # 702 b 
                'personal_name_secondary__additions_to_names_other_than_dates', # 702 c 
                'personal_name_secondary__roman_numerals', # 702 d
                'personal_name_secondary__dates' # 702 f
            ]
        },
        {
            'name': 'psn_4', # 710 a b c d f
            'fields': [
                'corporate_body_primary__entry_element', # 710 a
                'corporate_body_primary__subdivision', # 710 b 
                'corporate_body_primary__addition_to_name_or_qualifier', # 710 c 
                'corporate_body_primary__number_of_meeting', # 710 d
                'corporate_body_primary__date_of_meeting' # 710 f
            ]
        },
        {
            'name': 'psn_5', # 711 a b c d f
            'fields': [
                'corporate_body_alternative__entry_element', # 711 a
                'corporate_body_alternative__subdivision', # 711 b 
                'corporate_body_alternative__addition_to_name_or_qualifier', # 711 c 
                'corporate_body_alternative__number_of_meeting', # 711 d
                'corporate_body_alternative__date_of_meeting' # 711 f
            ]
        },
        {
            'name': 'psn_6', # 712 a b c d f
            'fields': [
                'corporate_body_secondary__entry_element', # 712 a
                'corporate_body_secondary__subdivision', # 712 b 
                'corporate_body_secondary__addition_to_name_or_qualifier', # 712 c 
                'corporate_body_secondary__number_of_meeting', # 712 d
                'corporate_body_secondary__date_of_meeting' # 712 f
            ]
        },
        {
            'name': 'psn_7', # 700 a g c d f
            'fields': [
                'personal_name_primary__entry_element', # 700 a
                'personal_name_primary__expansion_of_initials', # 700 g
                'personal_name_primary__additions_to_names_other_than_dates', # 700 c 
                'personal_name_primary__roman_numerals', # 700 d
                'personal_name_primary__dates' # 700 f
            ]
        },
        {
            'name': 'psn_8', # 701 a g c d f
            'fields': [
                'personal_name_alternative__entry_element', # 701 a
                'personal_name_alternative__expansion_of_initials', # 701 g
                'personal_name_alternative__additions_to_names_other_than_dates', # 701 c 
                'personal_name_alternative__roman_numerals', # 701 d
                'personal_name_alternative__dates' # 701 f
            ]
        },
        {
            'name': 'psn_9', # 702 a g c d f
            'fields': [
                'personal_name_secondary__entry_element', # 702 a
                'personal_name_secondary__expansion_of_initials', # 702 g
                'personal_name_secondary__additions_to_names_other_than_dates', # 702 c 
                'personal_name_secondary__roman_numerals', # 702 d
                'personal_name_secondary__dates' # 702 f
            ]
        },
        {
            'name': 'psn_10', # 710 a g c d f
            'fields': [
                'corporate_body_primary__entry_element', # 710 a
                'corporate_body_primary__inverted_element', # 710 g
                'corporate_body_primary__addition_to_name_or_qualifier', # 710 c 
                'corporate_body_primary__number_of_meeting', # 710 d
                'corporate_body_primary__date_of_meeting' # 710 f
            ]
        },
        {
            'name': 'psn_11', # 711 a g c d f
            'fields': [
                'corporate_body_alternative__entry_element', # 711 a
                'corporate_body_alternative__inverted_element', # 711 g
                'corporate_body_alternative__addition_to_name_or_qualifier', # 711 c 
                'corporate_body_alternative__number_of_meeting', # 711 d
                'corporate_body_alternative__date_of_meeting' # 711 f
            ]
        },
        {
            'name': 'psn_12', # 712 a g c d f
            'fields': [
                'corporate_body_secondary__entry_element', # 712 a
                'corporate_body_secondary__inverted_element', # 712 g
                'corporate_body_secondary__addition_to_name_or_qualifier', # 712 c 
                'corporate_body_secondary__number_of_meeting', # 712 d
                'corporate_body_secondary__date_of_meeting' # 712 f
            ]
        },
        {
            'name': 'psn_13', # 600 a b c d f j x y z
            'fields': [
                'personal_name_subject__entry_element', # 600 a
                'personal_name_subject__part_of_name_other_than_entry_element', # 600 b
                'personal_name_subject__additions_to_names_other_than_dates', # 600 c 
                'personal_name_subject__roman_numerals', # 600 d
                'personal_name_subject__dates', # 600 f
                'personal_name_subject__form_subdivision', # 600 j
                'personal_name_subject__subject_subdivision', # 600 x
                'personal_name_subject__geographical_subdivision', # 600 y
                'personal_name_subject__chronological_subdivision' # 600 z
            ]
        },
        {
            'name': 'psn_14', # 600 a g c d f j x y z
            'fields': [
                'personal_name_subject__entry_element', # 600 a
                'personal_name_subject__expansion_of_initials', # 600 g
                'personal_name_subject__additions_to_names_other_than_dates', # 600 c 
                'personal_name_subject__roman_numerals', # 600 d
                'personal_name_subject__dates', # 600 f
                'personal_name_subject__form_subdivision', # 600 j
                'personal_name_subject__subject_subdivision', # 600 x
                'personal_name_subject__geographical_subdivision', # 600 y
                'personal_name_subject__chronological_subdivision' # 600 z
            ]
        }
    ],
    'crn': [
        {
            'name': 'crn_1', # 710 a b c d e f g h
            'fields': [
                'corporate_body_primary__entry_element', # 710 a
                'corporate_body_primary__subdivision', # 710 b 
                'corporate_body_primary__addition_to_name_or_qualifier', # 710 c 
                'corporate_body_primary__number_of_meeting', # 710 d
                'corporate_body_primary__location_of_meeting', # 710 e
                'corporate_body_primary__date_of_meeting', # 710 f
                'corporate_body_primary__inverted_element', # 710 g
                'corporate_body_primary__general_term', # 710 h
            ]
        },
        {
            'name': 'crn_2', # 711 a b c d e f g h
            'fields': [
                'corporate_body_alternative__entry_element', # 711 a
                'corporate_body_alternative__subdivision', # 711 b 
                'corporate_body_alternative__addition_to_name_or_qualifier', # 711 c 
                'corporate_body_alternative__number_of_meeting', # 711 d
                'corporate_body_alternative__location_of_meeting', # 711 e
                'corporate_body_alternative__date_of_meeting', # 711 f
                'corporate_body_alternative__inverted_element', # 711 g
                'corporate_body_alternative__general_term', # 711 h
            ]
        },
        {
            'name': 'crn_3', # 712 a b c d e f g h
            'fields': [
                'corporate_body_secondary__entry_element', # 712 a
                'corporate_body_secondary__subdivision', # 712 b 
                'corporate_body_secondary__addition_to_name_or_qualifier', # 712 c 
                'corporate_body_secondary__number_of_meeting', # 712 d
                'corporate_body_secondary__location_of_meeting', # 712 e
                'corporate_body_secondary__date_of_meeting', # 712 f
                'corporate_body_secondary__inverted_element', # 712 g
                'corporate_body_secondary__general_term', # 712 h
            ]
        },
        {
            'name': 'crn_4', # 601 a b c d e f g h j x y z
            'fields': [
                'corporate_body_subject__entry_element', # 601 a
                'corporate_body_subject__subdivision', # 601 b
                'corporate_body_subject__addition_to_name_or_qualifier', # 601 c
                'corporate_body_subject__number_of_meeting', # 601 d
                'corporate_body_subject__location_of_meeting', # 601 e
                'corporate_body_subject__date_of_meeting', # 601 f
                'corporate_body_subject__inverted_element', # 601 g
                'corporate_body_subject__general_term', # 601 h
                'corporate_body_subject__form_subdivision', # 601 j
                'corporate_body_subject__subject_subdivision', # 601 x
                'corporate_body_subject__geographical_subdivision', # 601 y
                'corporate_body_subject__chronological_subdivision', # 601 z
            ]
        }
    ],
    'name': [
        {
            'name': 'name_1', # 700 a b c d f
            'fields': [
                'personal_name_primary__entry_element', # 700 a
                'personal_name_primary__part_of_name_other_than_entry_element', # 700 b 
                'personal_name_primary__additions_to_names_other_than_dates', # 700 c 
                'personal_name_primary__roman_numerals', # 700 d
                'personal_name_primary__dates' # 700 f
            ]
        },
        {
            'name': 'name_2', # 701 a b c d f
            'fields': [
                'personal_name_alternative__entry_element', # 701 a
                'personal_name_alternative__part_of_name_other_than_entry_element', # 701 b 
                'personal_name_alternative__additions_to_names_other_than_dates', # 701 c 
                'personal_name_alternative__roman_numerals', # 701 d
                'personal_name_alternative__dates' # 701 f
            ]
        },
        {
            'name': 'name_3', # 702 a b c d f
            'fields': [
                'personal_name_secondary__entry_element', # 702 a
                'personal_name_secondary__part_of_name_other_than_entry_element', # 702 b 
                'personal_name_secondary__additions_to_names_other_than_dates', # 702 c 
                'personal_name_secondary__roman_numerals', # 702 d
                'personal_name_secondary__dates' # 702 f
            ]
        },
        {
            'name': 'name_4', # 700 a g c d
            'fields': [
                'personal_name_primary__entry_element', # 700 a
                'personal_name_primary__expansion_of_initials', # 700 g
                'personal_name_primary__additions_to_names_other_than_dates', # 700 c 
                'personal_name_primary__roman_numerals' # 700 d
            ]
        },
        {
            'name': 'name_5', # 701 a g c d
            'fields': [
                'personal_name_alternative__entry_element', # 701 a
                'personal_name_alternative__expansion_of_initials', # 701 g
                'personal_name_alternative__additions_to_names_other_than_dates', # 701 c 
                'personal_name_alternative__roman_numerals' # 701 d
            ]
        },
        {
            'name': 'name_6', # 702 a g c d
            'fields': [
                'personal_name_secondary__entry_element', # 702 a
                'personal_name_secondary__expansion_of_initials', # 702 g
                'personal_name_secondary__additions_to_names_other_than_dates', # 702 c 
                'personal_name_secondary__roman_numerals' # 702 d
            ]
        },
        {
            'name': 'name_7', # 710 a b c d e f g h
            'fields': [
                'corporate_body_primary__entry_element', # 710 a
                'corporate_body_primary__subdivision', # 710 b 
                'corporate_body_primary__addition_to_name_or_qualifier', # 710 c 
                'corporate_body_primary__number_of_meeting', # 710 d
                'corporate_body_primary__location_of_meeting', # 710 e
                'corporate_body_primary__date_of_meeting', # 710 f
                'corporate_body_primary__inverted_element', # 710 g
                'corporate_body_primary__general_term', # 710 h
            ]
        },
        {
            'name': 'name_8', # 711 a b c d e f g h
            'fields': [
                'corporate_body_alternative__entry_element', # 711 a
                'corporate_body_alternative__subdivision', # 711 b 
                'corporate_body_alternative__addition_to_name_or_qualifier', # 711 c 
                'corporate_body_alternative__number_of_meeting', # 711 d
                'corporate_body_alternative__location_of_meeting', # 711 e
                'corporate_body_alternative__date_of_meeting', # 711 f
                'corporate_body_alternative__inverted_element', # 711 g
                'corporate_body_alternative__general_term', # 711 h
            ]
        },
        {
            'name': 'name_9', # 712 a b c d e f g h
            'fields': [
                'corporate_body_secondary__entry_element', # 712 a
                'corporate_body_secondary__subdivision', # 712 b 
                'corporate_body_secondary__addition_to_name_or_qualifier', # 712 c 
                'corporate_body_secondary__number_of_meeting', # 712 d
                'corporate_body_secondary__location_of_meeting', # 712 e
                'corporate_body_secondary__date_of_meeting', # 712 f
                'corporate_body_secondary__inverted_element', # 712 g
                'corporate_body_secondary__general_term', # 712 h
            ]
        }
    ],
    'author': [
        {
            'name': 'author_1', # 700 a b c d f
            'fields': [
                'personal_name_primary__entry_element', # 700 a
                'personal_name_primary__part_of_name_other_than_entry_element', # 700 b 
                'personal_name_primary__additions_to_names_other_than_dates', # 700 c 
                'personal_name_primary__roman_numerals', # 700 d
                'personal_name_primary__dates' # 700 f
            ]
        },
        {
            'name': 'author_2', # 701 a b c d f
            'fields': [
                'personal_name_alternative__entry_element', # 701 a
                'personal_name_alternative__part_of_name_other_than_entry_element', # 701 b 
                'personal_name_alternative__additions_to_names_other_than_dates', # 701 c 
                'personal_name_alternative__roman_numerals', # 701 d
                'personal_name_alternative__dates' # 701 f
            ]
        },
        {
            'name': 'author_3', # 702 a b c d f
            'fields': [
                'personal_name_secondary__entry_element', # 702 a
                'personal_name_secondary__part_of_name_other_than_entry_element', # 702 b 
                'personal_name_secondary__additions_to_names_other_than_dates', # 702 c 
                'personal_name_secondary__roman_numerals', # 702 d
                'personal_name_secondary__dates' # 702 f
            ]
        },
        {
            'name': 'author_4', # 700 a g c d
            'fields': [
                'personal_name_primary__entry_element', # 700 a
                'personal_name_primary__expansion_of_initials', # 700 g
                'personal_name_primary__additions_to_names_other_than_dates', # 700 c 
                'personal_name_primary__roman_numerals' # 700 d
            ]
        },
        {
            'name': 'author_5', # 701 a g c d
            'fields': [
                'personal_name_alternative__entry_element', # 701 a
                'personal_name_alternative__expansion_of_initials', # 701 g
                'personal_name_alternative__additions_to_names_other_than_dates', # 701 c 
                'personal_name_alternative__roman_numerals' # 701 d
            ]
        },
        {
            'name': 'author_6', # 702 a g c d
            'fields': [
                'personal_name_secondary__entry_element', # 702 a
                'personal_name_secondary__expansion_of_initials', # 702 g
                'personal_name_secondary__additions_to_names_other_than_dates', # 702 c 
                'personal_name_secondary__roman_numerals' # 702 d
            ]
        },
        {
            'name': 'author_7', # 710 a b c d e f g h
            'fields': [
                'corporate_body_primary__entry_element', # 710 a
                'corporate_body_primary__subdivision', # 710 b 
                'corporate_body_primary__addition_to_name_or_qualifier', # 710 c 
                'corporate_body_primary__number_of_meeting', # 710 d
                'corporate_body_primary__location_of_meeting', # 710 e
                'corporate_body_primary__date_of_meeting', # 710 f
                'corporate_body_primary__inverted_element', # 710 g
                'corporate_body_primary__general_term', # 710 h
            ]
        },
        {
            'name': 'author_8', # 711 a b c d e f g h
            'fields': [
                'corporate_body_alternative__entry_element', # 711 a
                'corporate_body_alternative__subdivision', # 711 b 
                'corporate_body_alternative__addition_to_name_or_qualifier', # 711 c 
                'corporate_body_alternative__number_of_meeting', # 711 d
                'corporate_body_alternative__location_of_meeting', # 711 e
                'corporate_body_alternative__date_of_meeting', # 711 f
                'corporate_body_alternative__inverted_element', # 711 g
                'corporate_body_alternative__general_term', # 711 h
            ]
        },
        {
            'name': 'author_9', # 712 a b c d e f g h
            'fields': [
                'corporate_body_secondary__entry_element', # 712 a
                'corporate_body_secondary__subdivision', # 712 b 
                'corporate_body_secondary__addition_to_name_or_qualifier', # 712 c 
                'corporate_body_secondary__number_of_meeting', # 712 d
                'corporate_body_secondary__location_of_meeting', # 712 e
                'corporate_body_secondary__date_of_meeting', # 712 f
                'corporate_body_secondary__inverted_element', # 712 g
                'corporate_body_secondary__general_term', # 712 h
            ]
        }
    ],
    'subj': [
        {
            'name': 'subj_1', # 600 a b c d f g p j x y z
            'fields': [
                'personal_name_subject__entry_element', # 600 a
                'personal_name_subject__part_of_name_other_than_entry_element', # 600 b
                'personal_name_subject__additions_to_names_other_than_dates', # 600 c 
                'personal_name_subject__roman_numerals', # 600 d
                'personal_name_subject__dates', # 600 f
                'personal_name_subject__expansion_of_initials', # 600 g
                'personal_name_subject__affiliation_or_address', # 600 p
                'personal_name_subject__form_subdivision', # 600 j
                'personal_name_subject__subject_subdivision', # 600 x
                'personal_name_subject__geographical_subdivision', # 600 y
                'personal_name_subject__chronological_subdivision' # 600 z
            ]
        },
        {
            'name': 'subj_2', # 600 j
            'fields': [
                'personal_name_subject__form_subdivision'
            ]
        },
        {
            'name': 'subj_3', # 600 x
            'fields': [
                'personal_name_subject__subject_subdivision'
            ]
        },
        {
            'name': 'subj_4', # 600 y
            'fields': [
                'personal_name_subject__geographical_subdivision'
            ]
        },
        {
            'name': 'subj_5', # 600 z
            'fields': [
                'personal_name_subject__chronological_subdivision'
            ]
        },
        {
            'name': 'subj_6', # 601 a b c d f g p j x y z
            'fields': [
                'corporate_body_subject__entry_element', # 601 a
                'corporate_body_subject__subdivision', # 601 b
                'corporate_body_subject__addition_to_name_or_qualifier', # 601 c 
                'corporate_body_subject__number_of_meeting', # 601 d
                'corporate_body_subject__location_of_meeting', # 601 e
                'corporate_body_subject__date_of_meeting', # 601 f
                'corporate_body_subject__inverted_element', # 601 g
                'corporate_body_subject__general_term', # 601 h
                'corporate_body_subject__form_subdivision', # 601 j
                'corporate_body_subject__subject_subdivision', # 601 x
                'corporate_body_subject__geographical_subdivision', # 601 y
                'corporate_body_subject__chronological_subdivision' # 601 z
            ]
        },
        {
            'name': 'subj_7', # 601 j
            'fields': [
                'corporate_body_subject__form_subdivision'
            ]
        },
        {
            'name': 'subj_8', # 601 x
            'fields': [
                'corporate_body_subject__subject_subdivision'
            ]
        },
        {
            'name': 'subj_9', # 601 y
            'fields': [
                'corporate_body_subject__geographical_subdivision'
            ]
        },
        {
            'name': 'subj_10', # 601 z
            'fields': [
                'corporate_body_subject__chronological_subdivision'
            ]
        },
        {
            'name': 'subj_11', # 606 a j x y z
            'fields': [
                'topical_subject__topic', # 606 a
                'topical_subject__form_subdivision', # 606 j
                'topical_subject__subject_subdivision', # 606 x
                'topical_subject__geographical_subdivision', # 606 y
                'topical_subject__chronological_subdivision' # 606 z
            ]
        },
        {
            'name': 'subj_12', # 606 j
            'fields': [
                'topical_subject__form_subdivision'
            ]
        },
        {
            'name': 'subj_13', # 606 x  
            'fields': [
                'topical_subject__subject_subdivision'
            ]
        },
        {
            'name': 'subj_14', # 606 y
            'fields': [
                'topical_subject__geographical_subdivision'
            ]
        },
        {
            'name': 'subj_15', # 606 z
            'fields': [
                'topical_subject__chronological_subdivision'
            ]
        },
        {
            'name': 'subj_16', # 607 a j x y z
            'fields': [
                'geographical_subject__geographical_name', # 607 a
                'geographical_subject__form_subdivision', # 607 j
                'geographical_subject__subject_subdivision', # 607 x
                'geographical_subject__geographical_subdivision', # 607 y
                'geographical_subject__chronological_subdivision' # 607 z
            ]
        },
        {
            'name': 'subj_17', # 607 j
            'fields': [
                'geographical_subject__form_subdivision'
            ]
        },
        {
            'name': 'subj_18', # 607 x  
            'fields': [
                'geographical_subject__subject_subdivision'
            ]
        },
        {
            'name': 'subj_19', # 607 y
            'fields': [
                'geographical_subject__geographical_subdivision'
            ]
        },
        {
            'name': 'subj_20', # 607 z
            'fields': [
                'geographical_subject__chronological_subdivision'
            ]
        },
        {
            'name': 'subj_21', # 608 a j x y z
            'fields': [
                'form_genre_physical_characteristics__form_genre', # 608 a
                'form_genre_physical_characteristics__form_subdivision', # 608 j
                'form_genre_physical_characteristics__subject_subdivision', # 608 x
                'form_genre_physical_characteristics__geographical_subdivision', # 608 y
                'form_genre_physical_characteristics__chronological_subdivision' # 608 z
            ]
        },
        {
            'name': 'subj_22', # 608 j
            'fields': [
                'form_genre_physical_characteristics__form_subdivision'
            ]
        },
        {
            'name': 'subj_23', # 608 x  
            'fields': [
                'form_genre_physical_characteristics__subject_subdivision'
            ]
        },
        {
            'name': 'subj_24', # 608 y
            'fields': [
                'form_genre_physical_characteristics__geographical_subdivision'
            ]
        },
        {
            'name': 'subj_25', # 608 z
            'fields': [
                'form_genre_physical_characteristics__chronological_subdivision'
            ]
        },
        {
            'name': 'subj_26', # 610 a
            'fields': [
                'uncontrolled_subject_terms__subject_term' # 610 a
            ]
        },
        {
            'name': 'subj_27', # 620 d a b c
            'fields': [
                'place_and_date_of_publication__city', # 620 d
                'place_and_date_of_publication__country', # 620 a
                'place_and_date_of_publication__state_or_province', # 620 b
                'place_and_date_of_publication__county' # 620 c
            ]
        }
    ],
    'ghr': [
        {
            'name': 'ghr_1', # 607 a j x y z
            'fields': [
                'geographical_subject__geographical_name', # 607 a
                'geographical_subject__form_subdivision', # 607 j
                'geographical_subject__subject_subdivision', # 607 x
                'geographical_subject__geographical_subdivision', # 607 y
                'geographical_subject__chronological_subdivision' # 607 z
            ]
        }
    ],
    'title': [
        {
            'name': 'title_1', # 200 a h i
            'fields': [
                'title_and_statement_of_responsibility__title', # 200 a
                'title_and_statement_of_responsibility__part_number', # 200 h
                'title_and_statement_of_responsibility__part_name' # 200 i
            ]
        },
        {
            'name': 'title_2', # 225 a
            'fields': [
                'series__series_title' # 225 a
            ]
        },
        {
            'name': 'title_3', # 500 a h i
            'fields': [
                'uniform_title__uniform_title', # 500 a 
                'uniform_title__section_or_part_number', # 500 h
                'uniform_title__section_or_part_name' # 500 i
            ]
        },
        {
            'name': 'title_4', # 510 a h i
            'fields': [
                'parallel_title__parallel_title', # 510 a
                'parallel_title__part_number', # 510 h
                'parallel_title__part_name' # 510 i
            ]
        },
        {
            'name': 'title_5', # 512 a h i
            'fields': [
                'cover_title__cover_title', # 512 a
                'cover_title__part_number', # 512 h
                'cover_title__part_name' # 512 i
            ]
        }
    ],
    'title6': [
        {
            'name': 'title6_1', # 200 a h i
            'fields': [
                'title_and_statement_of_responsibility__title', # 200 a
                'title_and_statement_of_responsibility__part_number', # 200 h
                'title_and_statement_of_responsibility__part_name' # 200 i
            ]
        },
        {
            'name': 'title6_2', # 225 a
            'fields': [
                'series__series_title' # 225 a
            ]
        },
        {
            'name': 'title6_3', # 500 a h i
            'fields': [
                'uniform_title__uniform_title', # 500 a 
                'uniform_title__section_or_part_number', # 500 h
                'uniform_title__section_or_part_name' # 500 i
            ]
        },
        {
            'name': 'title6_4', # 510 a h i
            'fields': [
                'parallel_title__parallel_title', # 510 a
                'parallel_title__part_number', # 510 h
                'parallel_title__part_name' # 510 i
            ]
        },
        {
            'name': 'title6_5', # 512 a h i
            'fields': [
                'cover_title__cover_title', # 512 a
                'cover_title__part_number', # 512 h
                'cover_title__part_name' # 512 i
            ]
        }
    ],
    'ser': [
        {
            'name': 'ser_1', # 200 a h i
            'fields': [
                'title_and_statement_of_responsibility__title', # 200 a
                'title_and_statement_of_responsibility__part_number', # 200 h
                'title_and_statement_of_responsibility__part_name' # 200 i
            ]
        },
        {
            'name': 'ser_2', # 225 a
            'fields': [
                'series__series_title' # 225 a
            ]
        },
        {
            'name': 'ser_3', # 500 a h i
            'fields': [
                'uniform_title__uniform_title', # 500 a 
                'uniform_title__section_or_part_number', # 500 h
                'uniform_title__section_or_part_name' # 500 i
            ]
        },
        {
            'name': 'ser_4', # 510 a h i
            'fields': [
                'parallel_title__parallel_title', # 510 a
                'parallel_title__part_number', # 510 h
                'parallel_title__part_name' # 510 i
            ]
        },
        {
            'name': 'ser_5', # 512 a h i
            'fields': [
                'cover_title__cover_title', # 512 a
                'cover_title__part_number', # 512 h
                'cover_title__part_name' # 512 i
            ]
        }
    ],
    'f500': [
        {
            'name': 'f500_1', # 500 a h i
            'fields': [
                'uniform_title__uniform_title', # 500 a 
                'uniform_title__section_or_part_number', # 500 h
                'uniform_title__section_or_part_name' # 500 i
            ]
        },
    ],
    'f510': [
        {
            'name': 'f510_1', # 510 a h i
            'fields': [
                'parallel_title__parallel_title', # 510 a
                'parallel_title__part_number', # 510 h
                'parallel_title__part_name' # 510 i
            ]
        },
        {
            'name': 'f510_2', # 200 d
            'fields': [
                'title_and_statement_of_responsibility__parallel_title' # 200 d
            ]
        }
    ],
    'f512': [
        {
            'name': 'f512_1', # 512 a h i
            'fields': [
                'cover_title__cover_title', # 512 a
                'cover_title__part_number', # 512 h
                'cover_title__part_name' # 512 i
            ]
        }
    ],
    'stdi': [
        {
            'name': 'stdi_1', # 010 a
            'fields': [
                'isbn__isbn', # 010 a
            ]
        },
        {
            'name': 'stdi_2', # 010 z
            'fields': [
                'isbn__qualification', # 010 z
            ]
        },
        {
            'name': 'stdi_3', # 011 a
            'fields': [
                'issn__issn', # 011 a
            ]
        },
        {
            'name': 'stdi_4', # 011 z
            'fields': [
                'issn__erroneous_issn', # 011 z
            ]
        },
        {
            'name': 'stdi_5', # 011 y
            'fields': [
                'issn__cancelled_issn', # 011 y
            ]
        },
        {
            'name': 'stdi_6', # 029 b
            'fields': [
                'document_number__document_number', # 029 b
            ]
        },
        {
            'name': 'stdi_7', # 225 x
            'fields': [
                'series__issn', # 225 x
            ]
        }
    ],
    'isbn': [
        {
            'name': 'isbn_1', # 010 a
            'fields': [
                'isbn__isbn', # 010 a
            ]
        },
        {
            'name': 'isbn_2', # 010 z
            'fields': [
                'isbn__qualification', # 010 z
            ]
        },
    ],
    'issn': [
        {
            'name': 'issn_1', # 011 a
            'fields': [
                'issn__issn', # 011 a
            ]
        },
        {
            'name': 'issn_2', # 011 z
            'fields': [
                'issn__erroneous_issn', # 011 z
            ]
        },
        {
            'name': 'issn_3', # 011 y
            'fields': [
                'issn__cancelled_issn', # 011 y
            ]
        },
        {
            'name': 'issn_4', # 225 x
            'fields': [
                'series__issn', # 225 x
            ]
        }
    ],
    'ntdn': [
        {
            'name': 'ntdn_1', # 029 b
            'fields': [
                'document_number__document_number', # 029 b
            ]
        },
    ],
    'id': [
        {
            'name': 'id_1', # 001
            'fields': [
                'record_identifier__name' # 001
            ]
        }
    ],
    'date': [
        {
            'name': 'date_1', # 100 a поз.0-7
            'fields': [
                'general_processing_data__date_entered' # 100 a поз.0-7
            ]
        }
    ],
    'udc': [
        {
            'name': 'udc_1', # 675 a
            'fields': [
                'udc__udc_number' # 675 a
            ]
        }
    ],
    'year': [
        {
            'name': 'year_1', # 210 d
            'fields': [
                'publication_distribution__date_of_publication' # 210 d
            ]
        },
        {
            'name': 'year_2', # 100 a поз.9-12
            'fields': [
                'general_processing_data__publication_date_1' # 100 a поз.9-12
            ]
        },
        {
            'name': 'year_3', # 100 a поз.13-16
            'fields': [
                'general_processing_data__publication_date_2' # 100 a поз.13-16
            ]
        }
    ],
    'plc': [
        {
            'name': 'plc_1', # 102 a
            'fields': [
                'country_of_publication__country_of_publication' # 102 a
            ]
        },
        {
            'name': 'plc_2', # 102 b
            'fields': [
                'country_of_publication__place_of_publication' # 102 b
            ]
        },
        {
            'name': 'plc_3', # 210 a
            'fields': [
                'publication_distribution__place_of_publication' # 210 a
            ]
        },
        {
            'name': 'plc_4', # 620 d a b c
            'fields': [
                'place_and_date_of_publication__city', # 620 d
                'place_and_date_of_publication__country', # 620 a
                'place_and_date_of_publication__state_or_province', # 620 b
                'place_and_date_of_publication__county', # 620 c
            ]
        },
        {
            'name': 'plc_5', # 620 a
            'fields': [
                'place_and_date_of_publication__country', # 620 a
            ]
        },
        {
            'name': 'plc_6', # 620 b
            'fields': [
                'place_and_date_of_publication__state_or_province', # 620 b
            ]
        }
    ],
    'publ': [
        {
            'name': 'publ_1', # 210 c
            'fields': [
                'publication_distribution__name_of_publisher' # 210 c
            ]
        }
    ],
    'wcmnt': [
        {
            'name': 'wcmnt_1', # 300 a
            'fields': [
                'general_note__general_note' # 300 a
            ]
        },
        {
            'name': 'wcmnt_2', # 305 a
            'fields': [
                'note_on_edition__note_text' # 305 a
            ]
        },
        {
            'name': 'wcmnt_3', # 320 a
            'fields': [
                'bibliography_note__bibliography_note' # 320 a
            ]
        },
        {
            'name': 'wcmnt_4', # 330 a
            'fields': [
                'summary_or_abstract__summary_text' # 330 a
            ]
        },
        {
            'name': 'wcmnt_5', # 337 a
            'fields': [
                'system_requirements__system_requirements' # 337 a
            ]
        }
    ],
    'invn': [
        {
            'name': 'invn_1', # 899 p
            'fields': [
                'holdings_data__copy_identifier' # 899 p
            ]
        }
    ],
    'lng': [
        {
            'name': 'lng_1', # 101 a
            'fields': [
                'language_of_document__language_of_text' # 101 a
            ]
        }
    ],
    'cont': [
        {
            'name': 'cont_1', # 105 a поз. 4-7
            'fields': [
                'coded_data_field__form_of_contents_codes' # 105 a поз. 4-7
            ]
        },
        {
            'name': 'cont_2', # 110 a поз. 3-6
            'fields': [
                'coded_data_field_serials__type_of_material_code', # 110 a поз. 3
                'coded_data_field_serials__nature_of_contents_code', # 110 a поз. 4-6
            ]
        }
    ],
    'level': [
        {
            'name': 'level_1',
            'fields': []
        }
    ],
    'instc': [
        {
            'name': 'instc_1', # 801 b
            'fields': [
                'source_of_record__agency' # 801 b
            ]
        }
    ],
    'all': [
        {
            'name': 'all_1',
            'fields': []
        }
    ],
    'ball': [
        {
            'name': 'ball_1', # 700 a b c d f
            'fields': [
                'personal_name_primary__entry_element', # 700 a
                'personal_name_primary__part_of_name_other_than_entry_element', # 700 b 
                'personal_name_primary__additions_to_names_other_than_dates', # 700 c 
                'personal_name_primary__roman_numerals', # 700 d
                'personal_name_primary__dates' # 700 f
            ]
        },
        {
            'name': 'ball_2', # 701 a b c d f
            'fields': [
                'personal_name_alternative__entry_element', # 701 a
                'personal_name_alternative__part_of_name_other_than_entry_element', # 701 b 
                'personal_name_alternative__additions_to_names_other_than_dates', # 701 c 
                'personal_name_alternative__roman_numerals', # 701 d
                'personal_name_alternative__dates' # 701 f
            ]
        },
        {
            'name': 'ball_3', # 702 a b c d f
            'fields': [
                'personal_name_secondary__entry_element', # 702 a
                'personal_name_secondary__part_of_name_other_than_entry_element', # 702 b 
                'personal_name_secondary__additions_to_names_other_than_dates', # 702 c 
                'personal_name_secondary__roman_numerals', # 702 d
                'personal_name_secondary__dates' # 702 f
            ]
        },
        {
            'name': 'ball_4', # 700 a g c d
            'fields': [
                'personal_name_primary__entry_element', # 700 a
                'personal_name_primary__expansion_of_initials', # 700 g
                'personal_name_primary__additions_to_names_other_than_dates', # 700 c 
                'personal_name_primary__roman_numerals' # 700 d
            ]
        },
        {
            'name': 'ball_5', # 701 a g c d
            'fields': [
                'personal_name_alternative__entry_element', # 701 a
                'personal_name_alternative__expansion_of_initials', # 701 g
                'personal_name_alternative__additions_to_names_other_than_dates', # 701 c 
                'personal_name_alternative__roman_numerals' # 701 d
            ]
        },
        {
            'name': 'ball_6', # 702 a g c d
            'fields': [
                'personal_name_secondary__entry_element', # 702 a
                'personal_name_secondary__expansion_of_initials', # 702 g
                'personal_name_secondary__additions_to_names_other_than_dates', # 702 c 
                'personal_name_secondary__roman_numerals' # 702 d
            ]
        },
        {
            'name': 'ball_7', # 710 a b c d e f g h
            'fields': [
                'corporate_body_primary__entry_element', # 710 a
                'corporate_body_primary__subdivision', # 710 b 
                'corporate_body_primary__addition_to_name_or_qualifier', # 710 c 
                'corporate_body_primary__number_of_meeting', # 710 d
                'corporate_body_primary__location_of_meeting', # 710 e
                'corporate_body_primary__date_of_meeting', # 710 f
                'corporate_body_primary__inverted_element', # 710 g
                'corporate_body_primary__general_term', # 710 h
            ]
        },
        {
            'name': 'ball_8', # 711 a b c d e f g h
            'fields': [
                'corporate_body_alternative__entry_element', # 711 a
                'corporate_body_alternative__subdivision', # 711 b 
                'corporate_body_alternative__addition_to_name_or_qualifier', # 711 c 
                'corporate_body_alternative__number_of_meeting', # 711 d
                'corporate_body_alternative__location_of_meeting', # 711 e
                'corporate_body_alternative__date_of_meeting', # 711 f
                'corporate_body_alternative__inverted_element', # 711 g
                'corporate_body_alternative__general_term', # 711 h
            ]
        },
        {
            'name': 'ball_9', # 712 a b c d e f g h
            'fields': [
                'corporate_body_secondary__entry_element', # 712 a
                'corporate_body_secondary__subdivision', # 712 b 
                'corporate_body_secondary__addition_to_name_or_qualifier', # 712 c 
                'corporate_body_secondary__number_of_meeting', # 712 d
                'corporate_body_secondary__location_of_meeting', # 712 e
                'corporate_body_secondary__date_of_meeting', # 712 f
                'corporate_body_secondary__inverted_element', # 712 g
                'corporate_body_secondary__general_term', # 712 h
            ]
        },
                {
            'name': 'ball_10', # 200 a h i
            'fields': [
                'title_and_statement_of_responsibility__title', # 200 a
                'title_and_statement_of_responsibility__part_number', # 200 h
                'title_and_statement_of_responsibility__part_name' # 200 i
            ]
        },
        {
            'name': 'ball_11', # 225 a
            'fields': [
                'series__series_title' # 225 a
            ]
        },
        {
            'name': 'ball_12', # 500 a h i
            'fields': [
                'uniform_title__uniform_title', # 500 a 
                'uniform_title__section_or_part_number', # 500 h
                'uniform_title__section_or_part_name' # 500 i
            ]
        },
        {
            'name': 'ball_13', # 510 a h i
            'fields': [
                'parallel_title__parallel_title', # 510 a
                'parallel_title__part_number', # 510 h
                'parallel_title__part_name' # 510 i
            ]
        },
        {
            'name': 'ball_14', # 512 a h i
            'fields': [
                'cover_title__cover_title', # 512 a
                'cover_title__part_number', # 512 h
                'cover_title__part_name' # 512 i
            ]
        },
                {
            'name': 'ball_15', # 600 a b c d f g p j x y z
            'fields': [
                'personal_name_subject__entry_element', # 600 a
                'personal_name_subject__part_of_name_other_than_entry_element', # 600 b
                'personal_name_subject__additions_to_names_other_than_dates', # 600 c 
                'personal_name_subject__roman_numerals', # 600 d
                'personal_name_subject__dates', # 600 f
                'personal_name_subject__expansion_of_initials', # 600 g
                'personal_name_subject__affiliation_or_address', # 600 p
                'personal_name_subject__form_subdivision', # 600 j
                'personal_name_subject__subject_subdivision', # 600 x
                'personal_name_subject__geographical_subdivision', # 600 y
                'personal_name_subject__chronological_subdivision' # 600 z
            ]
        },
        {
            'name': 'ball_16', # 600 j
            'fields': [
                'personal_name_subject__form_subdivision'
            ]
        },
        {
            'name': 'ball_17', # 600 x
            'fields': [
                'personal_name_subject__subject_subdivision'
            ]
        },
        {
            'name': 'ball_18', # 600 y
            'fields': [
                'personal_name_subject__geographical_subdivision'
            ]
        },
        {
            'name': 'ball_19', # 600 z
            'fields': [
                'personal_name_subject__chronological_subdivision'
            ]
        },
        {
            'name': 'ball_20', # 601 a b c d f g p j x y z
            'fields': [
                'corporate_body_subject__entry_element', # 601 a
                'corporate_body_subject__subdivision', # 601 b
                'corporate_body_subject__addition_to_name_or_qualifier', # 601 c 
                'corporate_body_subject__number_of_meeting', # 601 d
                'corporate_body_subject__location_of_meeting', # 601 e
                'corporate_body_subject__date_of_meeting', # 601 f
                'corporate_body_subject__inverted_element', # 601 g
                'corporate_body_subject__general_term', # 601 h
                'corporate_body_subject__form_subdivision', # 601 j
                'corporate_body_subject__subject_subdivision', # 601 x
                'corporate_body_subject__geographical_subdivision', # 601 y
                'corporate_body_subject__chronological_subdivision' # 601 z
            ]
        },
        {
            'name': 'ball_21', # 601 j
            'fields': [
                'corporate_body_subject__form_subdivision'
            ]
        },
        {
            'name': 'ball_22', # 601 x
            'fields': [
                'corporate_body_subject__subject_subdivision'
            ]
        },
        {
            'name': 'ball_23', # 601 y
            'fields': [
                'corporate_body_subject__geographical_subdivision'
            ]
        },
        {
            'name': 'ball_24', # 601 z
            'fields': [
                'corporate_body_subject__chronological_subdivision'
            ]
        },
        {
            'name': 'ball_25', # 606 a j x y z
            'fields': [
                'topical_subject__topic', # 606 a
                'topical_subject__form_subdivision', # 606 j
                'topical_subject__subject_subdivision', # 606 x
                'topical_subject__geographical_subdivision', # 606 y
                'topical_subject__chronological_subdivision' # 606 z
            ]
        },
        {
            'name': 'ball_26', # 606 j
            'fields': [
                'topical_subject__form_subdivision'
            ]
        },
        {
            'name': 'ball_27', # 606 x  
            'fields': [
                'topical_subject__subject_subdivision'
            ]
        },
        {
            'name': 'ball_28', # 606 y
            'fields': [
                'topical_subject__geographical_subdivision'
            ]
        },
        {
            'name': 'ball_29', # 606 z
            'fields': [
                'topical_subject__chronological_subdivision'
            ]
        },
        {
            'name': 'ball_30', # 607 a j x y z
            'fields': [
                'geographical_subject__geographical_name', # 607 a
                'geographical_subject__form_subdivision', # 607 j
                'geographical_subject__subject_subdivision', # 607 x
                'geographical_subject__geographical_subdivision', # 607 y
                'geographical_subject__chronological_subdivision' # 607 z
            ]
        },
        {
            'name': 'ball_31', # 607 j
            'fields': [
                'geographical_subject__form_subdivision'
            ]
        },
        {
            'name': 'ball_32', # 607 x  
            'fields': [
                'geographical_subject__subject_subdivision'
            ]
        },
        {
            'name': 'ball_33', # 607 y
            'fields': [
                'geographical_subject__geographical_subdivision'
            ]
        },
        {
            'name': 'ball_34', # 607 z
            'fields': [
                'geographical_subject__chronological_subdivision'
            ]
        },
        {
            'name': 'ball_35', # 608 a j x y z
            'fields': [
                'form_genre_physical_characteristics__form_genre', # 608 a
                'form_genre_physical_characteristics__form_subdivision', # 608 j
                'form_genre_physical_characteristics__subject_subdivision', # 608 x
                'form_genre_physical_characteristics__geographical_subdivision', # 608 y
                'form_genre_physical_characteristics__chronological_subdivision' # 608 z
            ]
        },
        {
            'name': 'ball_36', # 608 j
            'fields': [
                'form_genre_physical_characteristics__form_subdivision'
            ]
        },
        {
            'name': 'ball_37', # 608 x  
            'fields': [
                'form_genre_physical_characteristics__subject_subdivision'
            ]
        },
        {
            'name': 'ball_38', # 608 y
            'fields': [
                'form_genre_physical_characteristics__geographical_subdivision'
            ]
        },
        {
            'name': 'ball_39', # 608 z
            'fields': [
                'form_genre_physical_characteristics__chronological_subdivision'
            ]
        },
        {
            'name': 'ball_40', # 610 a
            'fields': [
                'uncontrolled_subject_terms__subject_term' # 610 a
            ]
        },
        {
            'name': 'ball_41', # 620 d a b c
            'fields': [
                'place_and_date_of_publication__city', # 620 d
                'place_and_date_of_publication__country', # 620 a
                'place_and_date_of_publication__state_or_province', # 620 b
                'place_and_date_of_publication__county' # 620 c
            ]
        }
    ]
}
