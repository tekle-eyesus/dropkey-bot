import re
from typing import Dict, Any

class FileTypeDetector:
    """Detect and categorize file types"""
    
    IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'}
    AUDIO_TYPES = {'audio/mpeg', 'audio/ogg', 'audio/wav', 'audio/m4a'}
    VIDEO_TYPES = {'video/mp4', 'video/avi', 'video/mkv', 'video/quicktime'}
    DOCUMENT_TYPES = {
        'application/pdf', 'text/plain', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    
    @staticmethod
    def categorize_file(mime_type: str, file_name: str = "") -> str:
        """Categorize file into broad types"""
        if mime_type in FileTypeDetector.IMAGE_TYPES:
            return 'image'
        elif mime_type in FileTypeDetector.AUDIO_TYPES:
            return 'audio'
        elif mime_type in FileTypeDetector.VIDEO_TYPES:
            return 'video'
        elif mime_type in FileTypeDetector.DOCUMENT_TYPES:
            return 'document'
        elif mime_type.startswith('text/'):
            return 'text'
        else:
            # Try to determine from file extension
            if file_name:
                ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
                if ext in {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}:
                    return 'image'
                elif ext in {'mp3', 'ogg', 'wav', 'm4a'}:
                    return 'audio'
                elif ext in {'mp4', 'avi', 'mkv', 'mov'}:
                    return 'video'
                elif ext in {'pdf', 'txt', 'doc', 'docx', 'xls', 'xlsx'}:
                    return 'document'
            return 'unknown'
    
    @staticmethod
    def get_file_icon(file_type: str) -> str:
        """Get appropriate icon for file type"""
        icons = {
            'image': '🖼️',
            'audio': '🎵',
            'video': '🎬',
            'document': '📄',
            'text': '📝',
            'unknown': '📎'
        }
        return icons.get(file_type, '📎')

class FileValidator:
    """Validate files for security and size limits"""
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB Telegram limit
    
    # Dangerous file extensions
    DANGEROUS_EXTENSIONS = {
        'exe', 'bat', 'cmd', 'sh', 'bin', 'app', 'jar', 'msi',
        'dmg', 'pkg', 'deb', 'rpm', 'scr', 'com'
    }
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if size_bytes is None:
            return "Unknown size"
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        return f"{size:.1f} {size_names[i]}"
    
    @staticmethod
    def is_file_safe(file_name: str, mime_type: str) -> bool:
        """Check if file is safe to accept"""
        if not file_name:
            return True
            
        # Check extension
        ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
        if ext in FileValidator.DANGEROUS_EXTENSIONS:
            return False
            
        # Additional safety checks can be added here
        return True
    
    @staticmethod
    def is_size_within_limit(file_size: int) -> bool:
        """Check if file size is within limits"""
        if file_size is None:
            return True  # Some files might not have size info
        return file_size <= FileValidator.MAX_FILE_SIZE