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
            inspector = inspect(connection)
            tables = set(inspector.get_table_names())
            agent_columns = {column["name"] for column in inspector.get_columns("agents")}
            agent_constraints = {
                constraint["name"]
                for constraint in inspector.get_check_constraints("agents")
            }
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()

        self.assertIn("executions", tables)
        self.assertIn("automation_projects", tables)
        self.assertTrue({
            "accepting_work",
            "maintenance_reason",
            "availability_updated_at",
        }.issubset(agent_columns))
        self.assertIn("ck_agents_operational_availability", agent_constraints)
        self.assertEqual(revision, "f7a1d4b3c902")

    def test_equivalent_legacy_schema_is_stamped(self):
        Base.metadata.create_all(bind=engine)

        criar_banco()

        with engine.connect() as connection:
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()

        self.assertEqual(revision, "f7a1d4b3c902")

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
