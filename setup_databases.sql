-- Database setup for Honeybadger Insights test applications

-- Create Django database
CREATE DATABASE IF NOT EXISTS honeybadger_django_test;

-- Create Flask database  
CREATE DATABASE IF NOT EXISTS honeybadger_flask_test;

-- Grant privileges (adjust username/password as needed)
GRANT ALL PRIVILEGES ON honeybadger_django_test.* TO 'root'@'localhost';
GRANT ALL PRIVILEGES ON honeybadger_flask_test.* TO 'root'@'localhost';

FLUSH PRIVILEGES;