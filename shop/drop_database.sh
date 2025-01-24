export PGPASSWORD=qwerty12
psql --host 127.0.0.1 -p 5432 -U postgres -d postgres -c "drop database diplom_db"
psql --host 127.0.0.1 -p 5432 -U postgres -d postgres -c "create database diplom_db"