# nexus-engine

This repository contains the backend code for Nexus.

## Setting up the development environment

There are two options for this; docker or a virtual environment:

### Docker

If you wish to use docker, you should install and set up docker desktop for your operating system.

Run the services :

`docker compose up`

This will start the API app and database services for development.

### Virtual environments

If you wish to use a virtual environment, you should do the following:

**Setup environment variables:**

Create a `.env` file inside the `api/` directory and configure the required environment variables following the format in `api/.env.sample`.

`DATABASE_URL` is the connection string for your development database server. It should be in the format _postgresql://username:password@host:port/database_

`SECRET_KEY` should be a random string.

`DEBUG` should be set to `True` since you're setting up a development environment.

**Install the PostgreSQL development library on your system:**

On Ubuntu and Debian, you can use the following command to install the library:

```bash
sudo apt-get install libpq-dev
```

On Fedora, Red Hat and CentOS, use:

```bash
sudo yum install postgresql-devel
```

On macOS, you can install it via brew

```bash
brew install postgresql
```

**Set up a virtual environment:**
Open your terminal and navigate to the root of the project repository.

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

You will know that you are in the virtual environment when your terminal prompt starts with (env).

Install the dependencies from requirements.txt and requirements.dev.txt:

```bash
pip install -r requirements.txt
pip install -r requirements.dev.txt
```

When you are done working on the project, you can exit the virtual environment by running the `exit` command

To deactivate the virtual environment without exiting the terminal, simply type `deactivate` on the command prompt.

Please let me know if you have any questions or issues setting up your environment.

## Setting up Pre-Commit Hooks

Pre-commit hooks are a great way to ensure that code meets certain standards before it is committed to the repository.

To set up pre-commit hooks on your machine, you will need to have the `pre-commit` package installed. You can install it by running the following command in your virtual environment:

```bash
pip install pre-commit
```

Once the package is installed, navigate to the root of your repository and run the following command:

```bash
pre-commit install
```

This command will install the pre-commit hook in the .git/hooks folder and will run the pre-commit checks every time you run the `git commit` command.

Verify that the hooks are working correctly: You can run the pre-commit run command to check that the hooks are working correctly:

```bash
pre-commit run --all-files
```
