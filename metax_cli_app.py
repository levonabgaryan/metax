import typer

from metax_migrations_cli.postgres import migrations

cli_app = typer.Typer()
cli_app.add_typer(migrations)

if __name__ == "__main__":
    cli_app()
