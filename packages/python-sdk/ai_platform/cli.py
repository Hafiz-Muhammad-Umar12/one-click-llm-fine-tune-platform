import click
import json
import os
from .client import AIPlatformClient

@click.group()
@click.option('--api-key', envvar='AI_PLATFORM_API_KEY', help='Your API Key')
@click.option('--base-url', default='https://api.platform.com/api/v1', help='API Base URL')
@click.pass_context
def main(ctx, api_key, base_url):
    if not api_key:
        click.echo("Error: API Key is required. Set AI_PLATFORM_API_KEY env var or use --api-key.")
        ctx.exit(1)
    ctx.obj = AIPlatformClient(api_key, base_url)

@main.group()
def datasets():
    """Manage datasets."""
    pass

@datasets.command(name='list')
@click.pass_obj
def list_datasets(client):
    """List all datasets."""
    res = client.list_datasets()
    click.echo(json.dumps(res, indent=2))

@datasets.command(name='upload')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--name', required=True, help='Name of the dataset')
@click.pass_obj
def upload_dataset(client, file_path, name):
    """Upload a dataset file."""
    res = client.upload_dataset(file_path, name)
    click.echo(f"Successfully uploaded dataset. ID: {res['id']}")

@main.group()
def training():
    """Manage training jobs."""
    pass

@training.command(name='status')
@click.argument('job_id')
@click.pass_obj
def get_status(client, job_id):
    """Get status of a training job."""
    res = client.get_job_status(job_id)
    click.echo(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
