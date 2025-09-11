#!/usr/bin/env python3
"""
Image import utility for Lifjell Opp 2025.

This script copies JPEG images from a source directory to a destination directory,
renaming them with sequential LOP25-nnnn.jpeg format, optionally adding photographer
information to EXIF data, and updating a TOML index file.
"""

import argparse
import os
import re
import shutil
from pathlib import Path
from typing import List, Optional

import toml
from PIL import Image
import piexif


def find_highest_serial_number(dest_dir: Path) -> int:
    """
    Find the highest serial number used in the destination directory.
    
    Args:
        dest_dir: Path to the destination directory
        
    Returns:
        The highest serial number found, or 0 if none found
    """
    pattern = re.compile(r'LOP25-(\d{4})\.jpeg')
    max_num = 0
    
    if not dest_dir.exists():
        return 0
        
    for file_path in dest_dir.iterdir():
        if file_path.is_file():
            match = pattern.match(file_path.name)
            if match:
                num = int(match.group(1))
                max_num = max(max_num, num)
    
    return max_num


def get_image_files(source_dir: Path) -> List[Path]:
    """
    Get all JPEG files from the source directory.
    
    Args:
        source_dir: Path to the source directory
        
    Returns:
        List of Path objects for JPEG files
    """
    image_files = []
    
    # Look for both .jpeg and .jpg files
    for pattern in ['*.jpeg', '*.jpg', '*.JPEG', '*.JPG']:
        image_files.extend(source_dir.glob(pattern))
    
    return sorted(image_files)


def update_exif_artist(image_file: Path, photographer: str) -> None:
    """
    Update the EXIF Artist tag for an image file.
    
    Args:
        image_file: Path to the image file
        photographer: Photographer name to add to EXIF
    """
    try:
        # Load the image
        image = Image.open(image_file)
        
        # Get existing EXIF data
        exif_dict = piexif.load(image.info.get('exif', b''))
        
        # Update the Artist tag (tag 315)
        exif_dict['0th'][piexif.ImageIFD.Artist] = photographer.encode('utf-8')
        
        # Save the image with updated EXIF
        exif_bytes = piexif.dump(exif_dict)
        image.save(image_file, exif=exif_bytes)
        
    except Exception as e:
        print(f"Warning: Could not update EXIF data for {image_file.name}: {e}")


def create_thumbnail(source_file: Path, thumb_dir: Path, thumb_name: str, 
                    max_width: int = 400, max_height: int = 300) -> None:
    """
    Create a thumbnail image suitable for a three-wide grid layout.
    
    Args:
        source_file: Path to the source image file
        thumb_dir: Directory to save the thumbnail
        thumb_name: Name for the thumbnail file
        max_width: Maximum width for the thumbnail
        max_height: Maximum height for the thumbnail
    """
    try:
        image = Image.open(source_file)
        
        # Convert to RGB if necessary (handles RGBA, P mode images)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        thumb_file = thumb_dir / thumb_name
        image.save(thumb_file, 'JPEG', quality=85, optimize=True)
        
    except Exception as e:
        print(f"Warning: Could not create thumbnail for {source_file.name}: {e}")


def update_toml_index(index_file: Path, image_files: List[str]) -> None:
    """
    Update the TOML index file with new image entries.
    
    Args:
        index_file: Path to the TOML index file
        image_files: List of image filenames to add
    """
    # Load existing TOML data or create new structure
    if index_file.exists():
        try:
            data = toml.load(index_file)
        except Exception as e:
            print(f"Warning: Could not load existing TOML file: {e}")
            data = {}
    else:
        data = {}
    
    # Ensure images array exists
    if 'images' not in data:
        data['images'] = []
    
    # Add new image entries
    for image_file in image_files:
        data['images'].append({'file': image_file})
    
    # Write back to file
    try:
        with open(index_file, 'w') as f:
            toml.dump(data, f)
        print(f"Updated TOML index file: {index_file}")
    except Exception as e:
        print(f"Error: Could not write TOML file: {e}")


def main():
    """Main function to handle command line arguments and execute the import process."""
    parser = argparse.ArgumentParser(
        description='Import JPEG images with sequential naming and optional EXIF updates'
    )
    parser.add_argument('source', help='Source directory containing images')
    parser.add_argument('destination', help='Destination directory for imported images')
    parser.add_argument('--photographer', help='Photographer name to add to EXIF Artist tag')
    parser.add_argument('--index-file', help='TOML file to update with image entries')
    
    args = parser.parse_args()
    
    # Convert to Path objects
    source_dir = Path(args.source)
    dest_dir = Path(args.destination)
    
    # Validate source directory
    if not source_dir.exists():
        print(f"Error: Source directory '{source_dir}' does not exist")
        return 1
    
    if not source_dir.is_dir():
        print(f"Error: Source path '{source_dir}' is not a directory")
        return 1
    
    # Create destination directory structure
    dest_dir.mkdir(parents=True, exist_ok=True)
    images_dir = dest_dir / 'images'
    thumbs_dir = dest_dir / 'thumbs'
    images_dir.mkdir(exist_ok=True)
    thumbs_dir.mkdir(exist_ok=True)
    
    # Find the highest serial number in images directory
    highest_num = find_highest_serial_number(images_dir)
    print(f"Found highest serial number: {highest_num:04d}")
    
    # Get image files from source
    image_files = get_image_files(source_dir)
    if not image_files:
        print(f"No JPEG files found in '{source_dir}'")
        return 0
    
    print(f"Found {len(image_files)} image files to import")
    
    # Process each image file
    imported_files = []
    current_num = highest_num + 1
    
    for source_file in image_files:
        new_name = f"LOP25-{current_num:04d}.jpeg"
        dest_file = images_dir / new_name
        shutil.copy2(source_file, dest_file)
        
        if args.photographer:
            update_exif_artist(dest_file, args.photographer)
        
        # Create thumbnail
        create_thumbnail(source_file, thumbs_dir, new_name)
        
        imported_files.append(new_name)
        print(f"Imported: {source_file.name} -> {new_name} (with thumbnail)")
        current_num += 1
    
    # Update TOML index file if specified
    if args.index_file:
        index_file = Path(args.index_file)
        update_toml_index(index_file, imported_files)
    
    print(f"Successfully imported {len(imported_files)} images")
    return 0


if __name__ == '__main__':
    exit(main())
