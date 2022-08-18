add_entity_query = "INSERT INTO inverted_index VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"
create_table_query = "CREATE VIRTUAL TABLE IF NOT EXISTS inverted_index USING fts5(title, entity_id, num_rels " + \
                     "UNINDEXED, tag, page, descr, entity_title, name_or_alias, p31, p131, p641, " + \
                     "triplets UNINDEXED, tokenize = 'porter ascii');"
insert_entity_query = "INSERT INTO inverted_index " + \
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
inv_index_query = "SELECT * FROM inverted_index WHERE inverted_index MATCH ?;"
add_info_query = "SELECT * FROM entity_additional_info WHERE entity_id=?;"
