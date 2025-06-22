TOKEN = '7646360181:AAFGYyYrJ51G3YLbBbGFhA2418puiDspXQI'

   import os

db_config = {
  "host":     os.getenv("MYSQL_HOST"),
  "user":     os.getenv("MYSQL_USER"),
  "password": os.getenv("MYSQL_PASSWORD"),
  "database": os.getenv("MYSQL_DB"),
  "port":     int(os.getenv("MYSQL_PORT", 3306)),
}

}

TELEGRAM_GROUP_ID = -1002385537018
