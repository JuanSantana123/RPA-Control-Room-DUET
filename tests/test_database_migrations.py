import os
import unittest


RUN_DATABASE_TESTS = os.getenv("DUET_RUN_DATABASE_TESTS") == "true"

if RUN_DATABASE_TESTS:
    import models  # noqa: F401
    from database import Base, criar_banco, engine
    from sqlalchemy import inspect, text


@unittest.skipUnless(
    RUN_DATABASE_TESTS,
    "Defina DUET_RUN_DATABASE_TESTS=true somente em um PostgreSQL descartável.",
)
class DatabaseMigrationTests(unittest.TestCase):
    def setUp(self):
        database_url = os.environ["DATABASE_URL"]
        if "duet_test" not in database_url:
            self.fail("Os testes de migração exigem um banco descartável chamado duet_test.")
        self._reset_database()

    def tearDown(self):
        self._reset_database()

    def _reset_database(self):
        with engine.begin() as connection:
            connection.execute(text("DROP SCHEMA public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))

    def test_fresh_database_is_upgraded_to_head(self):
        criar_banco()

        with engine.connect() as connection:
            tables = set(inspect(connection).get_table_names())
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()

        self.assertIn("executions", tables)
        self.assertIn("automation_projects", tables)
        self.assertEqual(revision, "5e3799a70fb6")

    def test_equivalent_legacy_schema_is_stamped(self):
        Base.metadata.create_all(bind=engine)

        criar_banco()

        with engine.connect() as connection:
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()

        self.assertEqual(revision, "5e3799a70fb6")

    def test_drifted_legacy_schema_is_rejected_without_stamp(self):
        Base.metadata.create_all(bind=engine)
        with engine.begin() as connection:
            connection.execute(text("DROP INDEX ix_users_username"))

        with self.assertRaisesRegex(RuntimeError, "diverge do baseline"):
            criar_banco()

        with engine.connect() as connection:
            self.assertNotIn(
                "alembic_version",
                inspect(connection).get_table_names(),
            )


if __name__ == "__main__":
    unittest.main()
