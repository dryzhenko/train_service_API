# Train Service API

API service for journey management written using Django REST Framework (DRF).

## Installing using GitHub

1. Install **PostgreSQL** and create a database.
2. Clone the repository: 

    ```bash
    git clone https://github.com/dryzhenko/train_service_API.git
    cd train_API
    ```
   
3. Create and activate a virtual environment:

    ```bash
    python -m venv venv 
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    ```

4. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

5. Set up environment variables:

    ```bash
    set DB_HOST=<your db hostname>
    set DB_NAME=<your db name>
    set DB_USER=<your db username>
    set DB_PASSWORD=<your db user password>
    set SECRET_KEY=<your secret key>
    ```

6. Apply the database migrations:

    ```bash
    python manage.py migrate
    ```

7. Run the development server:

    ```bash
    python manage.py runserver
    ```

## Running with Docker

Docker should be installed on your system.

1. Build the Docker containers:

    ```bash
    docker-compose build
    ```

2. Start the Docker containers:

    ```bash
    docker-compose up
    ```

## Getting Access

1. **Create a user** via the registration endpoint: `/api/user/register/`
2. **Get an access token** via: `/api/user/token/`

## Features

- JWT Authentication
- Admin panel available at `/admin/`
- API documentation located at `/api/doc/swagger/`
- Managing orders and tickets
- Creating trains with crews
- Adding and managing routes and journeys
- Filtering trains
