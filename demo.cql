CREATE KEYSPACE IF NOT EXISTS demo WITH replication = {'class':'SimpleStrategy', 'replication_factor':1};
USE demo;
CREATE TABLE IF NOT EXISTS users (id uuid PRIMARY KEY, name text, age int);
INSERT INTO users (id, name, age) VALUES (uuid(), 'Alice', 30);
INSERT INTO users (id, name, age) VALUES (uuid(), 'Bob', 25);
