"""
Django management command to load the `lms_user_id` column from historical user data.
"""


import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.models import Max


User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Import username/lms_user_id mappings into the `lms_user_id` column of the Credentials IDA's `core_user` table.

    Export data for this by running this query from the LMS:
        SELECT *
        INTO OUTFILE '<csv_file_name>.csv'
        FIELDS TERMINATED BY ','
        OPTIONALLY ENCLOSED BY '"'
        LINES TERMINATED BY '\n'
        FROM (
            SELECT
                username,
                id as user_id
            FROM auth_user
            WHERE id NOT IN (
                SELECT user_id FROM user_api_userretirementstatus
            )
            UNION SELECT
                original_username AS username,
                user_id
            FROM user_api_userretirementstatus
        ) u

    This management command assumes the data will be accessible from an AWS S3 bucket hosting the exported CSV.

    This commands capabilities are split into multiple 'stages' in order to allow time for manual verifications before
    and after syncing the LMS user data:
        - The 'create' stage will create a temporary table and an index on the `username` column.
        - The 'update_temp' stage will load data from a CSV containing an export of username and user-id records from
          the LMS.
        - The 'update_credentials' stage will sync the LMS user ids with the Credentials user records.
        - The 'delete' stage will remove the temporary table created in the 'create' stage.

    Example usage:
        - To create the temp table:
            ./manage.py sync_lms_user_ids --stage create
        - To update the temp table with LMS user data:
            ./manage.py sync_lms_user_ids --stage update_temp --s3-bucket-name <bucket_name> --file-name <csv_file_name>
        - To update the Credentials IDA's user records:
            ./manage.py sync_lms_user_ids --stage update_credentials
        - To delete the temp table and data:
            ./manage.py sync_lms_user_ids --stage delete
    """

    def add_arguments(self, parser):
        parser.add_argument("--max-user-id", type=int, default=None, help="Maximum user id to update")
        parser.add_argument("--starting-user-id", type=int, default=0, help="First user id to update")
        parser.add_argument(
            "--batch-size",
            type=int,
            default=10000,
            help="Number of users to update at a time",
        )
        parser.add_argument("--s3-bucket-name", default=None, help="Name of AWS S3 bucket to pull data from")
        parser.add_argument(
            "--file-name",
            default=None,
            help="Name of CSV file containing the data used to populate the temp table",
        )
        parser.add_argument(
            "--stage",
            type=str.lower,
            default=None,
            required=True,
            choices=["create", "update_temp", "update_creds", "delete"],
            help="The name of the 'stage' that will be executed in this run of the management command.",
        )

    def create_temp_table(self):
        """
        Stage 1.

        Creates a temporary table that will contain the username and user id data exported from the LMS.
        """
        create_table_sql = """
            CREATE TABLE temp_username_userid
            (
                username VARCHAR(150),
                lms_user_id INT(11),
                PRIMARY KEY(lms_user_id)
            )
            ENGINE = InnoDB;
        """

        create_index_sql = """
            CREATE INDEX username_index
            ON temp_username_userid (username);
        """

        with connection.cursor() as cursor:
            logger.info("Creating temp table")
            cursor.execute(create_table_sql)

            logger.info("Creating index on temp table")
            cursor.execute(create_index_sql)

        logger.info("Temp table creation complete")

    def update_temp_table_with_lms_data(self, bucket_name, file_name):
        """
        Stage 2.

        Loads data from a CSV file (housed in an S3 bucket) to a temporary table in the Credentials database.
        """
        load_data_sql = """
            LOAD DATA FROM S3 FILE %s
            INTO TABLE temp_username_userid
            FIELDS TERMINATED BY ','
            OPTIONALLY ENCLOSED BY '"'
            LINES TERMINATED BY '\\n'
                (username, lms_user_id)
        """

        file_location = f"{bucket_name}/{file_name}"

        with connection.cursor() as cursor:
            logger.info("Loading temp table with LMS user data")
            result = cursor.execute(load_data_sql, (file_location,))

        logger.info(f"Updated {result} rows in temp table from {file_location}")

    def update_credentials_user_table(self, batch_size, starting_user_id, max_user_id):
        """
        Stage 3.

        Sync LMS user id info from our temp table to the Credentials IDA's user table.
        """
        logger.info("Updating user records")
        while True:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    update_count = cursor.execute(
                        """
                        UPDATE core_user cu
                        JOIN temp_username_userid temp
                        ON cu.username = temp.username
                        SET cu.lms_user_id = temp.lms_user_id
                        WHERE cu.id >= %s AND cu.id < %s
                        AND cu.lms_user_id IS NULL
                        """,
                        (starting_user_id, min(starting_user_id + batch_size, max_user_id + 1)),
                    )
            logger.info(f"Updated {update_count} rows, starting at {starting_user_id}")

            starting_user_id += batch_size
            if starting_user_id > max_user_id:
                break

        logger.info("User records update complete")

    def drop_temp_table(self):
        """
        Stage 4.

        Drops the temporary table from the Credentials database.
        """
        drop_table_sql = "DROP TABLE temp_username_userid"
        with connection.cursor() as cursor:
            logger.info("Dropping temp table")
            cursor.execute(drop_table_sql)

    def handle(self, *args, **options):
        stage = options.get("stage")
        if stage == "create":
            self.create_temp_table()
        elif stage == "update_temp":
            bucket_name = options.get("s3_bucket_name")
            file_name = options.get("file_name")
            if not bucket_name or not file_name:
                logger.error(
                    "Missing 'bucket_name' or 'file_name' argument when attempting to run the 'update_temp' stage."
                )
            else:
                self.update_temp_table_with_lms_data(bucket_name, file_name)
        elif stage == "update_creds":
            max_user_id = options.get("max_user_id")
            if max_user_id is None:
                max_user_id = User.objects.aggregate(Max("id"))["id__max"]

            batch_size = options.get("batch_size")
            starting_user_id = options.get("starting_user_id")

            self.update_credentials_user_table(batch_size, starting_user_id, max_user_id)
        elif stage == "delete":
            self.drop_temp_table()
