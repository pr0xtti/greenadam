# For logging
import logging
from pprint import pformat

# For logging
from core.config import APP_NAME
from core.config import settings
from db.models.rocket import (
    Rocket,
    RocketType,
)
from db.session import Session
from db.repository.entity_base import EntityBase
from db.database import table_empty
from sxapi.rocket import *


class EntityRocket(EntityBase):
    name: str = "rocket"
    table_order: list

    def __init__(self):
        super(EntityRocket, self).__init__()

    def get_data_and_save(self) -> tuple[str | None, int | None]:
        logger = logging.getLogger(f"{APP_NAME}.{__name__}")
        tables_affected: int = 0  # Counter
        logger.debug(f"Iterating through models: {self.model_order} ...")
        # Iterating through models/tables list
        # for model_name in self.model_order:
        model_name = self.model_order[0]
        logger.debug(f"Model: {model_name}")
        # Getting class type for a SQLAlchemy Model by class name
        class_type = globals()[model_name]
        err, check = table_empty(table_model=class_type)
        if not err and check:  # Table is empty
            # Inserting data
            logger.debug(f"Going to fill the table ...")
            # Getting class type for a SxapiTableClass by class name
            sxapi_class_type = globals()["Sxapi" + model_name]

            logger.debug(f"Instantiating: {sxapi_class_type}")
            sxapi_class_instance = sxapi_class_type()
            logger.debug(f"Calling {sxapi_class_type}.get_data()")
            err, sxapi_data = sxapi_class_instance.get_data()
            if not err:
                logger.debug(f"OK, we have data: {len(sxapi_data)} count")
            db_data = []
            logger.debug(f"Making list of instances of Model ...")
            # Making a list of object of sqlalchemy models (type db.model.Class)
            rocket_type_dict = {}
            for item in sxapi_data:
                # rocket_type
                name = item.pop('type')
                if name not in rocket_type_dict.keys():
                    rocket_type_dict[name] = RocketType(name=name)
                    db_data.append(rocket_type_dict[name])
                rocket_type = rocket_type_dict[name]
                item['rocket_type'] = rocket_type

                # logger.debug(f"item: {pformat(item)}")
                rocket = Rocket(**item)
                db_data.append(rocket)

            logger.debug(f"Going to insert: {len(db_data)} records")
            db = Session()
            try:
                db.add_all(db_data)
                db.commit()
                logger.debug(f"OK, inserted")
                err = None
            except Exception as e:
                db.rollback()
                err = f"Failed to insert: {e}"
                logger.critical(err)
            finally:
                db.close()

            if err:
                logger.critical(f"Failed to fill table for model: {model_name}")
            else:
                tables_affected += 1
        else:  # Table isn't empty
            # Already has data. Appending or updating data
            # IT'S NOT IMPLEMENTED
            pass
            logger.critical(f"It's not implemented. Doing nothing")

        logger.debug(f"Affected: {tables_affected}")
        return None, tables_affected

    @staticmethod
    def get_id_by_ext_id(ext_id: str):
        logger = logging.getLogger(f"{APP_NAME}.{__name__}")
        logger.debug(f"Executing db query ...")
        db = Session()
        try:
            mission = db.query(Rocket).filter_by(
                external_object_id=ext_id
            ).first()
            db.close()
            if mission:
                logger.debug(f"OK, got result")
                return mission.id
            else:
                logger.warning(f"Not found")
        except Exception as e:
            logger.critical(f"Failed: {e}")
            db.close()

    def articles_count(self) -> int | None:
        logger = logging.getLogger(f"{APP_NAME}.{__name__}")
        result = 0
        logger.debug(f"Source unknown. Always returning {result}")
        return result

    def wikipedia_count(self) -> int | None:
        logger = logging.getLogger(f"{APP_NAME}.{__name__}")
        logger.debug(f"Querying ...")
        result = None
        with Session() as db:
            result = db.query(Rocket).filter(
                Rocket.wikipedia.isnot(None)
            ).count()
        logger.debug(f"Returning {result}")
        return result
