#!/usr/bin/env python3
"""
Open WebUI Knowledge Uploader - Command Line Interface

CLI tool for uploading files to Open WebUI knowledge collections.
"""

import argparse
import os
import sys
import logging
from pathlib import Path
from typing import List

from openwebui_uploader import OpenWebUIClient


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def collect_files(directory: str, recursive: bool = True) -> List[str]:
    """
    Collect all files from a directory.
    
    Args:
        directory: Path to the directory
        recursive: If True, scan subdirectories recursively
        
    Returns:
        List of file paths
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        raise ValueError(f"Directory does not exist: {directory}")
    
    if not directory_path.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")
    
    files = []
    if recursive:
        for file_path in directory_path.rglob('*'):
            if file_path.is_file():
                files.append(str(file_path))
    else:
        for file_path in directory_path.iterdir():
            if file_path.is_file():
                files.append(str(file_path))
    
    return sorted(files)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Upload files to Open WebUI knowledge collections',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload files to existing knowledge collection
  python cli.py --endpoint http://localhost:3000 --api-key YOUR_KEY \\
                --knowledge "My Docs" --path ./documents

  # Create knowledge collection if it doesn't exist
  python cli.py --endpoint http://localhost:3000 --api-key YOUR_KEY \\
                --knowledge "New Collection" --path ./documents --create

  # Non-recursive upload (current directory only)
  python cli.py --endpoint http://localhost:3000 --api-key YOUR_KEY \\
                --knowledge "My Docs" --path ./documents --no-recursive

  # Use API key from environment variable
  export OPEN_WEBUI_API_KEY=your_key
  python cli.py --endpoint http://localhost:3000 \\
                --knowledge "My Docs" --path ./documents
        """
    )
    
    parser.add_argument(
        '--endpoint',
        required=True,
        help='Open WebUI API endpoint (e.g., http://localhost:3000)'
    )
    
    parser.add_argument(
        '--api-key',
        default=os.environ.get('OPEN_WEBUI_API_KEY'),
        help='API key for authentication (or set OPEN_WEBUI_API_KEY env var)'
    )
    
    parser.add_argument(
        '--knowledge',
        required=True,
        help='Name of the knowledge collection'
    )
    
    parser.add_argument(
        '--create',
        action='store_true',
        help='Create knowledge collection if it does not exist'
    )
    
    parser.add_argument(
        '--description',
        default='',
        help='Description for the knowledge collection (used when creating)'
    )
    
    parser.add_argument(
        '--path',
        required=True,
        help='Path to directory containing files to upload'
    )
    
    parser.add_argument(
        '--recursive',
        action='store_true',
        default=True,
        help='Recursively scan subdirectories (default: True)'
    )
    
    parser.add_argument(
        '--no-recursive',
        dest='recursive',
        action='store_false',
        help='Do not scan subdirectories'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Validate API key
    if not args.api_key:
        logger.error("API key is required. Provide --api-key or set OPEN_WEBUI_API_KEY environment variable.")
        sys.exit(1)
    
    # Validate endpoint format
    if not args.endpoint.startswith(('http://', 'https://')):
        logger.error("Endpoint must start with http:// or https://")
        sys.exit(1)
    
    try:
        # Collect files
        logger.info(f"Collecting files from: {args.path}")
        files = collect_files(args.path, recursive=args.recursive)
        
        if not files:
            logger.warning(f"No files found in {args.path}")
            sys.exit(0)
        
        logger.info(f"Found {len(files)} file(s) to upload")
        
        # Initialize client
        client = OpenWebUIClient(api_endpoint=args.endpoint, api_key=args.api_key)
        
        # Upload files
        logger.info(f"Uploading files to knowledge collection: {args.knowledge}")
        results = client.upload_files_to_knowledge(
            knowledge_name=args.knowledge,
            file_paths=files,
            create_if_missing=args.create,
            description=args.description
        )
        
        # Print summary
        print("\n" + "="*60)
        print("Upload Summary")
        print("="*60)
        print(f"Total files: {results['total']}")
        print(f"Successful: {results['success']}")
        print(f"Failed: {results['failed']}")
        
        if results['errors']:
            print("\nErrors:")
            for error in results['errors']:
                print(f"  - {error}")
        
        print("="*60)
        
        # Exit with appropriate code
        if results['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nUpload interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == '__main__':
    main()

