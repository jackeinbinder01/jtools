import logging
from types import TracebackType
from typing import Self

import pandas as pd
import snowflake.connector


logger = logging.getLogger(__name__)


class SnowflakeClient:
    def __init__(
            self,
            user: str,
            account: str,
            role: str,
            warehouse: str,
            database: str | None = None,
    ):
        self.user = user
        self.account = account
        self.role = role
        self.warehouse = warehouse
        self.database = database

        self.ctx = self._connect()
        logger.info("Snowflake client initialized.")

    def _connect(self) -> snowflake.connector.SnowflakeConnection:
        logger.info("Initiating SSO Login...")
        
        ctx = snowflake.connector.connect(
            user=self.user,
            account=self.account,
            authenticator='externalbrowser'
        )

        with ctx.cursor() as cursor:
            cursor.execute(f"USE ROLE {self.role}")
            cursor.execute(f"USE WAREHOUSE {self.warehouse}")

            if self.database is not None:
                cursor.execute(f"USE DATABASE {self.database}")

        return ctx

    def __enter__(self) -> Self:
        return self

    def __exit__(
            self, 
            exc_type: type[BaseException] | None, 
            exc: BaseException | None, 
            tb: TracebackType | None,
    ) -> None:
        self.close()

    def to_df(self, query: str) -> pd.DataFrame:
        try:
            with self.ctx.cursor() as cursor:
                cursor.execute(query)
                df = cursor.fetch_pandas_all()

            logger.info("Query executed successfully.")
            return df
        except Exception:
            logger.exception("Error executing Snowflake query.")
            raise

    def close(self) -> None:
        if self.ctx:
            self.ctx.close()
            logger.info("Snowflake connection closed.")
