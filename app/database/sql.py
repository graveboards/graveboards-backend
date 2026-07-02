# Realign every owned SERIAL/IDENTITY sequence with the current max of its column.
# Inserting rows with explicit primary keys (e.g. during a data migration) does not
# advance the backing sequence, so a subsequent server-generated insert would reuse an
# existing id and raise a UniqueViolationError. Empty tables are reset so the next id is
# 1; populated tables continue from max(id) + 1.
RESET_SEQUENCES_SQL = """
DO $$
DECLARE
    r RECORD;
    max_id BIGINT;
BEGIN
    FOR r IN
        SELECT s.relname AS seq_name, t.relname AS table_name, a.attname AS col_name
        FROM pg_class s
        JOIN pg_depend d ON d.objid = s.oid AND d.deptype = 'a'
        JOIN pg_class t ON t.oid = d.refobjid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = d.refobjsubid
        WHERE s.relkind = 'S'
    LOOP
        EXECUTE format('SELECT COALESCE(MAX(%I), 0) FROM %I', r.col_name, r.table_name)
            INTO max_id;
        IF max_id > 0 THEN
            EXECUTE format('SELECT setval(%L, %s, true)', r.seq_name, max_id);
        ELSE
            EXECUTE format('SELECT setval(%L, 1, false)', r.seq_name);
        END IF;
    END LOOP;
END $$;
"""
